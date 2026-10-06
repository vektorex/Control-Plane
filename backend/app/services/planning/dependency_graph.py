"""
Dependency Graph, Topological Sorting, Critical Path, and Cycle Detection for Planning Items.
"""
from typing import Dict, List, Set, Tuple, Optional, Any
from backend.app.services.planning.errors import DependencyCycleError


class PlanningDependencyGraph:
    """
    Constructs a directed acyclic graph of planning items and dependencies.
    Performs cycle detection, topological sorting, and critical path analysis.
    """

    def __init__(self):
        self.nodes: Set[str] = set()
        self.durations: Dict[str, float] = {}  # item_id -> duration in minutes
        self.adj: Dict[str, List[Tuple[str, str, int]]] = {}  # u -> list of (v, dep_type, lag)
        self.in_degree: Dict[str, int] = {}
        self.predecessors: Dict[str, List[Tuple[str, str, int]]] = {}  # v -> list of (u, dep_type, lag)

    def add_node(self, item_id: str, estimated_duration: Optional[float] = None) -> None:
        self.nodes.add(item_id)
        self.durations[item_id] = float(estimated_duration or 0.0)
        if item_id not in self.adj:
            self.adj[item_id] = []
        if item_id not in self.predecessors:
            self.predecessors[item_id] = []
        if item_id not in self.in_degree:
            self.in_degree[item_id] = 0

    def add_edge(self, u: str, v: str, dependency_type: str = "finish_to_start", lag: int = 0) -> None:
        """Adds dependency u -> v (u precedes v)."""
        if u not in self.nodes:
            self.add_node(u)
        if v not in self.nodes:
            self.add_node(v)
        self.adj[u].append((v, dependency_type, lag))
        self.predecessors[v].append((u, dependency_type, lag))
        self.in_degree[v] += 1

    def detect_cycles(self) -> Optional[List[str]]:
        """
        Detects if a cycle exists using DFS graph coloring (0=unvisited, 1=visiting, 2=visited).
        Returns the cycle path as a list of item IDs if detected, otherwise None.
        """
        visited: Dict[str, int] = {node: 0 for node in self.nodes}
        parent: Dict[str, Optional[str]] = {node: None for node in self.nodes}
        cycle_path: List[str] = []

        def dfs(u: str) -> bool:
            visited[u] = 1
            for v, _, _ in self.adj.get(u, []):
                if visited[v] == 1:
                    # Cycle detected: trace path back
                    curr = u
                    cycle_path.append(v)
                    while curr and curr != v:
                        cycle_path.append(curr)
                        curr = parent.get(curr)
                    cycle_path.append(v)
                    cycle_path.reverse()
                    return True
                elif visited[v] == 0:
                    parent[v] = u
                    if dfs(v):
                        return True
            visited[u] = 2
            return False

        for node in list(self.nodes):
            if visited[node] == 0:
                if dfs(node):
                    return cycle_path

        return None

    def validate_no_cycles(self) -> None:
        cycle = self.detect_cycles()
        if cycle:
            raise DependencyCycleError(cycle)

    def topological_sort(self) -> List[str]:
        """
        Returns items in topologically sorted order using Kahn's algorithm.
        Raises DependencyCycleError if a cycle is present.
        """
        self.validate_no_cycles()

        in_deg = {n: 0 for n in self.nodes}
        for u in self.adj:
            for v, _, _ in self.adj[u]:
                in_deg[v] = in_deg.get(v, 0) + 1

        queue = [n for n in self.nodes if in_deg[n] == 0]
        order: List[str] = []

        while queue:
            queue.sort()  # deterministic ordering
            u = queue.pop(0)
            order.append(u)
            for v, _, _ in self.adj.get(u, []):
                in_deg[v] -= 1
                if in_deg[v] == 0:
                    queue.append(v)

        if len(order) != len(self.nodes):
            self.validate_no_cycles()  # Will raise DependencyCycleError

        return order

    def compute_critical_path(self) -> Dict[str, Any]:
        """
        Computes forward and backward passes:
        Earliest Start (ES), Earliest Finish (EF), Latest Start (LS), Latest Finish (LF), Slack.
        Identifies critical path items (slack == 0).
        """
        self.validate_no_cycles()
        order = self.topological_sort()

        # Forward pass
        es: Dict[str, float] = {n: 0.0 for n in self.nodes}
        ef: Dict[str, float] = {}

        for u in order:
            dur = self.durations.get(u, 0.0)
            ef[u] = es[u] + dur
            for v, dep_type, lag in self.adj.get(u, []):
                # Standard finish_to_start: v cannot start until u finishes + lag
                min_v_start = ef[u] + float(lag)
                if min_v_start > es[v]:
                    es[v] = min_v_start

        total_project_duration = max(ef.values()) if ef else 0.0

        # Backward pass
        lf: Dict[str, float] = {n: total_project_duration for n in self.nodes}
        ls: Dict[str, float] = {}

        for u in reversed(order):
            for v, dep_type, lag in self.adj.get(u, []):
                max_u_finish = ls[v] - float(lag)
                if max_u_finish < lf[u]:
                    lf[u] = max_u_finish
            dur = self.durations.get(u, 0.0)
            ls[u] = lf[u] - dur

        slack: Dict[str, float] = {n: round(ls[n] - es[n], 2) for n in self.nodes}
        critical_items = [n for n in order if abs(slack[n]) < 1e-4]

        return {
            "total_duration": total_project_duration,
            "earliest_start": es,
            "earliest_finish": ef,
            "latest_start": ls,
            "latest_finish": lf,
            "slack": slack,
            "critical_path": critical_items,
        }
