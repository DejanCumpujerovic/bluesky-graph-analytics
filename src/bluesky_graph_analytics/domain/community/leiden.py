"""Leiden community detection on weighted follower projection (§5.3, DEO 6.1)."""

from collections.abc import Mapping

import igraph as ig
import leidenalg


class LeidenCommunityDetector:
    def __init__(
        self,
        *,
        resolution: float = 1.0,
        modularity_min: float = 0.3,
        algorithm: str = "leiden",
        random_seed: int = 42,
    ) -> None:
        self._resolution = resolution
        self._modularity_min = modularity_min
        self._algorithm = algorithm
        self._random_seed = random_seed

    def detect_on_igraph(self, graph: ig.Graph) -> tuple[Mapping[str, int], float]:
        if graph.vcount() == 0:
            return {}, 0.0
        if self._algorithm != "leiden":
            msg = f"Unsupported community algorithm: {self._algorithm}"
            raise ValueError(msg)

        weights = graph.es["weight"] if "weight" in graph.edge_attributes() else None
        partition = leidenalg.find_partition(
            graph,
            leidenalg.RBConfigurationVertexPartition,
            weights=weights,
            resolution_parameter=self._resolution,
            seed=self._random_seed,
        )
        modularity = float(partition.modularity)
        if modularity < self._modularity_min and graph.ecount() > 0:
            return {}, modularity

        names = graph.vs["name"]
        result: dict[str, int] = {}
        for part_id, cluster in enumerate(partition):
            for idx in cluster:
                result[str(names[idx])] = part_id
        return result, modularity
