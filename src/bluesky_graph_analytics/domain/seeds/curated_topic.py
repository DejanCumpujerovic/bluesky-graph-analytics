"""Curated topic seed profile selection."""

from pydantic import BaseModel, Field

from bluesky_graph_analytics.domain.value_objects import Handle


class SeedTopic(BaseModel):
    topic: str
    handles: list[Handle] = Field(default_factory=list)


class CuratedTopicSelector:
    def __init__(self, topics: list[SeedTopic]) -> None:
        self._topics = {t.topic: t for t in topics}

    def handles_for_topic(self, topic: str) -> list[Handle]:
        topic_entry = self._topics.get(topic)
        if topic_entry is None:
            return []
        return list(topic_entry.handles)
