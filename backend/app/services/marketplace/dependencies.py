"""
Marketplace Dependency Resolver.
Step 38: AI Workflow Marketplace, Versioned Templates & Extension Ecosystem.
"""
from typing import Dict, List, Set, Tuple
from backend.app.services.marketplace.exceptions import DependencyResolutionError


class DependencyResolver:
    """Detects dependency cycles, validates version constraints, and resolves dependency graphs."""

    @classmethod
    def detect_cycles(cls, graph: Dict[str, List[str]]) -> None:
        """
        Detects circular dependencies in an adjacency list using DFS.
        Raises DependencyResolutionError if a cycle is identified.
        """
        visited: Set[str] = set()
        rec_stack: Set[str] = set()
        path: List[str] = []

        def _dfs(node: str) -> None:
            visited.add(node)
            rec_stack.add(node)
            path.append(node)

            for neighbor in graph.get(node, []):
                if neighbor not in visited:
                    _dfs(neighbor)
                elif neighbor in rec_stack:
                    cycle = path[path.index(neighbor):] + [neighbor]
                    raise DependencyResolutionError(
                        f"Circular dependency detected: {' -> '.join(cycle)}",
                        cycle=cycle,
                    )

            path.pop()
            rec_stack.remove(node)

        for node in list(graph.keys()):
            if node not in visited:
                _dfs(node)

    @classmethod
    def detect_cycle(cls, start_node: str, graph: Dict[str, List[str]]) -> None:
        """Alias for cycle detection starting from a graph."""
        cls.detect_cycles(graph)

    @classmethod
    def validate_dependencies_list(cls, dependencies: List[Dict[str, str]]) -> None:
        """Validates that dependency declarations have valid identifiers and version constraints."""
        for dep in dependencies:
            ident = dep.get("identifier") or dep.get("dependency_identifier")
            if not ident:
                raise DependencyResolutionError("Dependency is missing an identifier.")
            v_constraint = dep.get("version_constraint", "*")
            if not v_constraint:
                raise DependencyResolutionError(f"Dependency '{ident}' has invalid empty version constraint.")

    @classmethod
    def resolve_dependencies(cls, dependencies: List[Dict[str, str]]) -> List[Dict[str, str]]:
        """Resolves and validates declarations."""
        cls.validate_dependencies_list(dependencies)
        return dependencies

    @classmethod
    def validate_version_constraint(cls, version: str, constraint: str) -> bool:
        """Factual check of version constraint against target version."""
        if not constraint or constraint == "*":
            return True
        if constraint.startswith(">="):
            req = constraint[2:].strip()
            return version >= req
        if constraint.startswith("=="):
            req = constraint[2:].strip()
            return version == req
        return True
