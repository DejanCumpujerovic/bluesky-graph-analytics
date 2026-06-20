"""Project-wide constants (DEO 6.4 — not run-tunable)."""

VERSION = "0.1.0"
APP_NAME = "bluesky_graph_analytics"

DEFAULT_CONFIG_PATH = "config/config.yaml"
DEV_CONFIG_PATH = "config/config.dev.yaml"
SEED_PROFILES_PATH = "config/seed_profiles.yaml"

DATA_DIR = "data"
CACHE_DB_PATH = "data/cache.db"

# Phase 1 crawl depth (DEO 5.1); not exposed in config.yaml.
CRAWL_DEPTH = 1

# Statistički donji prag za similarity overlap (DEO 6.4).
MIN_OVERLAP_ABSOLUTE = 3

# Maksimalni broj čvorova za "živu" ForceAtlas2 vizualizaciju.
VIZ_MAX_NODES_LIVE = 500

# BLAKE2b digest size za pseudonime (8 bajtova = 16 hex karaktera).
PSEUDONYM_DIGEST_SIZE = 8

# Fallback git commit hash kada nije dostupan (Docker bez .git).
GIT_COMMIT_UNKNOWN = "unknown"

# Default Streamlit port (DEO 6.1 dashboard).
DEFAULT_STREAMLIT_PORT = 8501

# langdetect prag pouzdanosti (Lui & Baldwin 2012).
LANGDETECT_DEFAULT_THRESHOLD = 0.90

# Seed file bounds (DEO 6.2).
SEED_FILE_MIN_COUNT = 50
SEED_FILE_MAX_COUNT = 200

# Default followers page size for atproto getFollowers.
FOLLOWERS_PAGE_SIZE = 100
