"""Atproto Bluesky client adapter with cursor pagination (§5.12)."""

from __future__ import annotations

import asyncio
import logging
from collections.abc import Callable
from dataclasses import dataclass
from enum import StrEnum
from typing import Any, TypeVar

import httpx
import structlog
from aiolimiter import AsyncLimiter
from atproto import Client
from returns.result import Failure, Result, Success
from tenacity import (
    before_sleep_log,
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from bluesky_graph_analytics.application.ports.bluesky_client import BlueskyClient
from bluesky_graph_analytics.domain.errors import DomainError, ErrorCode
from bluesky_graph_analytics.domain.models import FollowRelation, Profile
from bluesky_graph_analytics.domain.value_objects import DID, Handle, SnapshotId
from bluesky_graph_analytics.infrastructure.bluesky.acl_mapper import profile_from_atproto

T = TypeVar("T")

logger = structlog.get_logger(__name__)
_py_logger = logging.getLogger(__name__)


class RateLimitError(Exception):
    """HTTP 429."""


class ServerError(Exception):
    """HTTP 5xx."""


class TerminationReason(StrEnum):
    CURSOR_EXHAUSTED = "cursor_exhausted"
    MAX_FOLLOWERS_REACHED = "max_followers_reached"
    MAX_PAGES_REACHED = "max_pages_reached"


@dataclass(frozen=True, slots=True)
class FollowerPageResult:
    relations: list[FollowRelation]
    profiles: list[Profile]
    reason: TerminationReason
    pages_fetched: int


class AtprotoBlueskyClient(BlueskyClient):
    def __init__(
        self,
        service_url: str,
        *,
        handle: str | None = None,
        app_password: str | None = None,
        auth_token: str | None = None,
        requests_per_second: float = 8.0,
        rate_limit_per_minute: int | None = None,
        timeout_seconds: float = 30.0,
    ) -> None:
        self._service_url = service_url
        self._handle = handle
        self._app_password = app_password
        self._auth_token = auth_token
        self._timeout_seconds = timeout_seconds
        self._client: Client | None = None
        rps = requests_per_second
        if rate_limit_per_minute is not None:
            rps = rate_limit_per_minute / 60.0
        self._limiter = AsyncLimiter(max(1, int(rps)), 1)

    def _get_client(self) -> Client:
        if self._client is None:
            self._client = Client(base_url=self._service_url)
            if self._handle and self._app_password:
                self._client.login(self._handle, self._app_password)
        return self._client

    @retry(
        stop=stop_after_attempt(5),
        wait=wait_exponential(multiplier=2, min=1, max=60),
        retry=retry_if_exception_type(
            (httpx.NetworkError, httpx.TimeoutException, RateLimitError, ServerError)
        ),
        before_sleep=before_sleep_log(_py_logger, logging.WARNING),
        reraise=True,
    )
    async def _call(self, fn: Callable[..., T], *args: Any, **kwargs: Any) -> T:
        async with self._limiter:
            try:
                return await asyncio.wait_for(
                    asyncio.to_thread(fn, *args, **kwargs),
                    timeout=self._timeout_seconds,
                )
            except Exception as exc:  # noqa: BLE001
                status = _extract_status_code(exc)
                if status == 429:
                    raise RateLimitError(str(exc)) from exc
                if status in {500, 502, 503, 504}:
                    raise ServerError(str(exc)) from exc
                raise

    async def resolve_handle(self, handle: Handle) -> Result[DID, DomainError]:
        try:
            client = self._get_client()
            resolved = await self._call(client.resolve_handle, str(handle))
            return Success(DID(resolved.did))
        except Exception as exc:  # noqa: BLE001
            return Failure(
                DomainError(
                    code=ErrorCode.EXTERNAL_API,
                    message="resolve_handle failed",
                    details={"handle": str(handle), "error": str(exc)},
                )
            )

    async def fetch_profile(self, did: DID) -> Result[Profile, DomainError]:
        try:
            client = self._get_client()
            resp = await self._call(client.app.bsky.actor.get_profile, {"actor": did})
            return Success(
                profile_from_atproto(
                    did=resp.did,
                    handle=resp.handle,
                    display_name=resp.display_name,
                    description=resp.description,
                    followers_count=resp.followers_count or 0,
                    follows_count=resp.follows_count or 0,
                    posts_count=resp.posts_count or 0,
                )
            )
        except Exception as exc:  # noqa: BLE001
            return Failure(
                DomainError(
                    code=ErrorCode.EXTERNAL_API,
                    message="fetch_profile failed",
                    details={"did": did, "error": str(exc)},
                )
            )

    async def fetch_followers_page(
        self,
        did: DID,
        *,
        snapshot_id: SnapshotId,
        limit: int,
        cursor: str | None,
    ) -> Result[tuple[list[FollowRelation], list[Profile], str | None], DomainError]:
        try:
            client = self._get_client()
            params: dict[str, object] = {"actor": did, "limit": limit}
            if cursor:
                params["cursor"] = cursor
            resp = await self._call(client.app.bsky.graph.get_followers, params)
            relations: list[FollowRelation] = []
            profiles: list[Profile] = []
            for follower in resp.followers:
                fdid = DID(follower.did)
                relations.append(
                    FollowRelation(
                        follower_did=fdid,
                        followee_did=did,
                        snapshot_id=snapshot_id,
                    )
                )
                profiles.append(
                    profile_from_atproto(
                        did=follower.did,
                        handle=_optional_str(follower, "handle"),
                        display_name=_optional_str(follower, "display_name"),
                        description=_optional_str(follower, "description"),
                        followers_count=_optional_int(follower, "followers_count"),
                        follows_count=_optional_int(follower, "follows_count"),
                        posts_count=_optional_int(follower, "posts_count"),
                    )
                )
            return Success((relations, profiles, resp.cursor))
        except Exception as exc:  # noqa: BLE001
            return Failure(
                DomainError(
                    code=ErrorCode.EXTERNAL_API,
                    message="get_followers failed",
                    details={"did": did, "error": str(exc)},
                )
            )

    async def fetch_followers_paginated(
        self,
        did: DID,
        *,
        snapshot_id: SnapshotId,
        max_followers: int,
        max_pages: int,
        page_size: int,
    ) -> Result[FollowerPageResult, DomainError]:
        all_relations: list[FollowRelation] = []
        all_profiles: list[Profile] = []
        cursor: str | None = None
        pages = 0
        reason = TerminationReason.CURSOR_EXHAUSTED

        while pages < max_pages and len(all_relations) < max_followers:
            page = await self.fetch_followers_page(
                did,
                snapshot_id=snapshot_id,
                limit=min(page_size, max_followers - len(all_relations)),
                cursor=cursor,
            )
            if isinstance(page, Failure):
                return page
            rels, profs, cursor = page.unwrap()
            all_relations.extend(rels)
            all_profiles.extend(profs)
            pages += 1
            if cursor is None:
                reason = TerminationReason.CURSOR_EXHAUSTED
                break
            if len(all_relations) >= max_followers:
                reason = TerminationReason.MAX_FOLLOWERS_REACHED
                break
        else:
            if pages >= max_pages:
                reason = TerminationReason.MAX_PAGES_REACHED

        return Success(
            FollowerPageResult(
                relations=all_relations[:max_followers],
                profiles=all_profiles[:max_followers],
                reason=reason,
                pages_fetched=pages,
            )
        )

    async def fetch_followers(
        self, did: DID, *, snapshot_id: SnapshotId, limit: int
    ) -> Result[list[FollowRelation], DomainError]:
        result = await self.fetch_followers_paginated(
            did,
            snapshot_id=snapshot_id,
            max_followers=limit,
            max_pages=1,
            page_size=min(100, limit),
        )
        if isinstance(result, Failure):
            return result
        return Success(result.unwrap().relations)

    async def fetch_following(
        self, did: DID, *, snapshot_id: SnapshotId, limit: int
    ) -> Result[list[FollowRelation], DomainError]:
        _ = (did, snapshot_id, limit)
        return Success([])


def _optional_int(obj: object, attr: str, default: int = 0) -> int:
    value = getattr(obj, attr, None)
    if value is None:
        return default
    return int(value)


def _optional_str(obj: object, attr: str) -> str | None:
    value = getattr(obj, attr, None)
    return value if isinstance(value, str) else None


def _extract_status_code(exc: Exception) -> int | None:
    for attr in ("status_code", "status"):
        value = getattr(exc, attr, None)
        if isinstance(value, int):
            return value
    response = getattr(exc, "response", None)
    status_code = getattr(response, "status_code", None)
    if isinstance(status_code, int):
        return status_code
    message = str(exc)
    for code in ("429", "500", "502", "503", "504"):
        if f" {code}" in message or f"[{code}]" in message:
            return int(code)
    return None
