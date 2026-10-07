# Release Dependencies

Release Coordination enforces deterministic sequencing using a topological DAG. Dependency types include `requires`, `blocks`, `must_precede`, `must_follow`, `same_window`, and `different_window`.

Cycles evaluate to `BLOCKED`.