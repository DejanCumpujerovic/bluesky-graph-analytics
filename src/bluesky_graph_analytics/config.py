"""Configuration loader — precedence: defaults → yaml → dev yaml → .env → CLI (DEO 6)."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Literal

import yaml
from pydantic import BaseModel, Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from bluesky_graph_analytics.constants import (
    DEFAULT_CONFIG_PATH,
    DEFAULT_STREAMLIT_PORT,
    DEV_CONFIG_PATH,
    FOLLOWERS_PAGE_SIZE,
    LANGDETECT_DEFAULT_THRESHOLD,
    PSEUDONYM_DIGEST_SIZE,
)


class BlueskySettings(BaseModel):
    api_base: str = "https://bsky.social"
    requests_per_second: float = Field(default=8.0, gt=0.0)
    timeout_seconds: float = Field(default=30.0, gt=0.0)


class CollectionSettings(BaseModel):
    seed_source_file: str = "config/seed_profiles.yaml"
    min_followers: int = Field(default=50, ge=0)
    max_followers: int = Field(default=5000, ge=1)
    max_followers_per_seed: int = Field(default=5000, ge=1)
    max_pages_per_seed: int = Field(default=100, ge=1)
    snapshot_id: str = "snap_2025_q1"
    skip_invalid_seeds: bool = True
    enforce_mvp_seed_count: bool = False
    followers_page_size: int = Field(default=FOLLOWERS_PAGE_SIZE, ge=1, le=100)


class StorageSettings(BaseModel):
    database_url: str = Field(
        default_factory=lambda: f"sqlite+aiosqlite:///{Path('data/cache.db').as_posix()}"
    )


class ReproducibilitySettings(BaseModel):
    random_seed: int = 42


class SimilaritySettings(BaseModel):
    metrics: list[str] = Field(default_factory=lambda: ["jaccard", "adamic_adar", "overlap"])
    min_overlap_relative: float = Field(default=0.01, ge=0.0, le=1.0)
    max_pairs: int = Field(default=5000, ge=1)


class CommunitySettings(BaseModel):
    algorithm: Literal["leiden"] = "leiden"
    resolution: float = Field(default=1.0, gt=0.0)
    edge_threshold: float = Field(default=0.1, ge=0.0, le=1.0)
    modularity_min: float = Field(default=0.3, ge=0.0, le=1.0)
    min_overlap_seeds: int = Field(default=1, ge=1)


class Node2VecSettings(BaseModel):
    dimensions: int = Field(default=64, ge=1)
    walk_length: int = Field(default=80, ge=1)
    num_walks: int = Field(default=10, ge=1)
    p: float = Field(default=1.0, gt=0.0)
    q: float = Field(default=1.0, gt=0.0)
    workers: int = Field(default=1, ge=1)


class PredictionSettings(BaseModel):
    test_fraction: float = Field(default=0.1, gt=0.0, lt=1.0)
    negative_ratio: float = Field(default=1.0, gt=0.0)
    negative_strategy: Literal["common_neighbor_filtered"] = "common_neighbor_filtered"
    node2vec: Node2VecSettings = Field(default_factory=Node2VecSettings)
    k_values: list[int] = Field(default_factory=lambda: [10, 50, 100])


class NlpSettings(BaseModel):
    text_source: Literal["description"] = "description"
    langdetect_threshold: float = Field(default=LANGDETECT_DEFAULT_THRESHOLD, ge=0.0, le=1.0)
    target_language: str = "en"
    top_terms_per_community: int = Field(default=10, ge=1)
    stopwords: str = "nltk_english"


class AnalysisSettings(BaseModel):
    similarity: SimilaritySettings = Field(default_factory=SimilaritySettings)
    community: CommunitySettings = Field(default_factory=CommunitySettings)
    prediction: PredictionSettings = Field(default_factory=PredictionSettings)
    nlp: NlpSettings = Field(default_factory=NlpSettings)


class EthicsSettings(BaseModel):
    pseudonym_digest_size: int = Field(default=PSEUDONYM_DIGEST_SIZE, ge=1, le=64)
    exclude_fields_on_export: list[str] = Field(
        default_factory=lambda: ["display_name", "description"]
    )


class LoggingSettings(BaseModel):
    level: str = "INFO"
    format: Literal["json", "console"] = "json"


class DashboardSettings(BaseModel):
    host: str = "0.0.0.0"
    port: int = DEFAULT_STREAMLIT_PORT


class AppSettings(BaseSettings):
    """Root settings; secrets and overrides from environment."""

    model_config = SettingsConfigDict(
        env_prefix="BGA_",
        env_file=".env",
        extra="ignore",
        env_nested_delimiter="__",
    )

    bluesky: BlueskySettings = Field(default_factory=BlueskySettings)
    collection: CollectionSettings = Field(default_factory=CollectionSettings)
    storage: StorageSettings = Field(default_factory=StorageSettings)
    reproducibility: ReproducibilitySettings = Field(default_factory=ReproducibilitySettings)
    analysis: AnalysisSettings = Field(default_factory=AnalysisSettings)
    ethics: EthicsSettings = Field(default_factory=EthicsSettings)
    logging: LoggingSettings = Field(default_factory=LoggingSettings)
    dashboard: DashboardSettings = Field(default_factory=DashboardSettings)

    pseudonym_salt: str | None = Field(default=None, validation_alias="PSEUDONYM_SALT")
    sentry_dsn: str | None = Field(default=None, validation_alias="SENTRY_DSN")
    log_level: str | None = Field(default=None, validation_alias="LOG_LEVEL")
    bluesky_auth_token: str | None = Field(default=None, validation_alias="BLUESKY_AUTH_TOKEN")
    bluesky_handle: str | None = Field(default=None, validation_alias="BLUESKY_HANDLE")
    bluesky_app_password: str | None = Field(default=None, validation_alias="BLUESKY_APP_PASSWORD")

    @model_validator(mode="after")
    def _apply_env_overrides(self) -> AppSettings:
        if self.log_level:
            self.logging.level = self.log_level
        return self

    @property
    def effective_log_level(self) -> str:
        return self.log_level or self.logging.level

    @property
    def effective_sentry_dsn(self) -> str | None:
        return self.sentry_dsn

    @property
    def requests_per_minute(self) -> int:
        return max(1, int(self.bluesky.requests_per_second * 60))

    @property
    def requests_per_second(self) -> float:
        return self.bluesky.requests_per_second


def _deep_merge(base: dict[str, Any], overlay: dict[str, Any]) -> dict[str, Any]:
    merged = dict(base)
    for key, value in overlay.items():
        if key in merged and isinstance(merged[key], dict) and isinstance(value, dict):
            merged[key] = _deep_merge(merged[key], value)
        else:
            merged[key] = value
    return merged


def _load_yaml(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {}
    with path.open(encoding="utf-8") as fh:
        data = yaml.safe_load(fh)
    return data if isinstance(data, dict) else {}


def load_settings(
    *,
    config_path: Path | None = None,
    dev_config_path: Path | None = None,
    cli_overrides: dict[str, Any] | None = None,
) -> AppSettings:
    """Merge configuration sources (later wins)."""
    yaml_merged: dict[str, Any] = {}
    yaml_merged = _deep_merge(yaml_merged, _load_yaml(Path(config_path or DEFAULT_CONFIG_PATH)))
    yaml_merged = _deep_merge(yaml_merged, _load_yaml(Path(dev_config_path or DEV_CONFIG_PATH)))

    if cli_overrides:
        yaml_merged = _deep_merge(yaml_merged, cli_overrides)

    return AppSettings.model_validate(yaml_merged)


def settings_to_yaml(settings: AppSettings) -> str:
    payload = settings.model_dump(
        mode="json",
        exclude={"pseudonym_salt", "bluesky_app_password", "bluesky_auth_token"},
    )
    return yaml.safe_dump(payload, sort_keys=True)
