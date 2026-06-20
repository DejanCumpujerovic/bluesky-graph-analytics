"""Pseudonymization for sharing-ready exports (DEO 5.7, 6.1 ethics)."""

import hashlib

from bluesky_graph_analytics.constants import PSEUDONYM_DIGEST_SIZE
from bluesky_graph_analytics.domain.models import Profile
from bluesky_graph_analytics.domain.value_objects import DID, Handle, PseudonymHash


class Pseudonymizer:
    def __init__(self, salt: bytes, *, digest_size: int = PSEUDONYM_DIGEST_SIZE) -> None:
        if len(salt) < 32:
            msg = "PSEUDONYM_SALT must be at least 32 bytes"
            raise ValueError(msg)
        self._salt = salt
        self._digest_size = digest_size

    def hash_did(self, did: DID) -> PseudonymHash:
        digest = hashlib.blake2b(
            did.encode(), key=self._salt, digest_size=self._digest_size
        ).hexdigest()
        return PseudonymHash(digest)

    def hash_handle(self, handle: Handle) -> PseudonymHash:
        digest = hashlib.blake2b(
            str(handle).encode(), key=self._salt, digest_size=self._digest_size
        ).hexdigest()
        return PseudonymHash(digest)

    def anonymize_profile(
        self, profile: Profile, *, exclude_fields: tuple[str, ...] = ("display_name", "description")
    ) -> dict[str, object]:
        data: dict[str, object] = {
            "did": self.hash_did(profile.did),
            "handle": self.hash_handle(profile.handle) if profile.handle else None,
            "display_name": profile.display_name,
            "description": profile.description,
            "followers_count": profile.followers_count,
            "follows_count": profile.follows_count,
            "posts_count": profile.posts_count,
            "detected_language": profile.detected_language,
            "language_confidence": profile.language_confidence,
            "is_seed": profile.is_seed,
        }
        for field in exclude_fields:
            if field in data:
                data[field] = None
        return data


def pseudonymizer_from_salt_hex(
    salt_hex: str,
    *,
    digest_size: int = PSEUDONYM_DIGEST_SIZE,
) -> Pseudonymizer:
    raw = bytes.fromhex(salt_hex) if len(salt_hex) == 64 else salt_hex.encode()
    return Pseudonymizer(raw, digest_size=digest_size)
