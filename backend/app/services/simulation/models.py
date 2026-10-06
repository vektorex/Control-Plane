"""
SQLAlchemy models for Step 41: AI Agent Simulation, Sandbox & Scenario Testing Layer.
"""
from datetime import datetime, timezone
import uuid
from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    JSON,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

from backend.app.db.base import Base


def _gen_uuid() -> str:
    return str(uuid.uuid4())


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Simulation(Base):
    """Core governed simulation model."""

    __tablename__ = "simulations"

    id = Column(String(36), primary_key=True, default=_gen_uuid)
    workspace_id = Column(String(36), nullable=False, index=True)
    project_id = Column(String(36), nullable=True, index=True)
    name = Column(String(128), nullable=False)
    slug = Column(String(128), nullable=False, index=True)
    description = Column(Text, nullable=True)
    status = Column(String(32), nullable=False, default="draft", index=True)  # draft, ready, running, completed, failed, cancelled, archived
    simulation_type = Column(String(32), nullable=False, default="single_agent")  # single_agent, agent_team, workflow, task, replay, scenario_suite
    target_type = Column(String(32), nullable=False)  # agent, agent_team, workflow, task, replay
    target_id = Column(String(36), nullable=False, index=True)
    target_version_id = Column(String(36), nullable=True)
    current_version_id = Column(String(36), nullable=True)
    created_by = Column(String(36), nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow, onupdate=_utcnow)

    __table_args__ = (
        UniqueConstraint("workspace_id", "slug", name="uq_simulations_ws_slug"),
        Index("ix_simulations_ws_status", "workspace_id", "status"),
        Index("ix_simulations_target", "target_type", "target_id"),
    )

    versions = relationship(
        "SimulationVersion",
        back_populates="simulation",
        cascade="all, delete-orphan",
        order_by="SimulationVersion.version.desc()",
    )
    runs = relationship(
        "SimulationRun",
        back_populates="simulation",
        cascade="all, delete-orphan",
    )


class SimulationVersion(Base):
    """Immutable published or draft version of a Simulation."""

    __tablename__ = "simulation_versions"

    id = Column(String(36), primary_key=True, default=_gen_uuid)
    simulation_id = Column(String(36), ForeignKey("simulations.id", ondelete="CASCADE"), nullable=False, index=True)
    version = Column(Integer, nullable=False)
    configuration = Column(JSON, nullable=False, default=dict)
    environment_config = Column(JSON, nullable=False, default=dict)
    scenario_config = Column(JSON, nullable=False, default=dict)
    fault_config = Column(JSON, nullable=False, default=dict)
    policy_overrides = Column(JSON, nullable=False, default=dict)
    assertions = Column(JSON, nullable=False, default=list)
    created_by = Column(String(36), nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)
    published_at = Column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        UniqueConstraint("simulation_id", "version", name="uq_simulation_versions_sim_ver"),
    )

    simulation = relationship("Simulation", back_populates="versions")


class SimulationEnvironment(Base):
    """Isolated environment state definition for simulations."""

    __tablename__ = "simulation_environments"

    id = Column(String(36), primary_key=True, default=_gen_uuid)
    workspace_id = Column(String(36), nullable=False, index=True)
    name = Column(String(128), nullable=False)
    description = Column(Text, nullable=True)
    mode = Column(String(32), nullable=False, default="isolated")  # isolated, snapshot, synthetic
    config = Column(JSON, nullable=False, default=dict)  # synthetic docs, artifacts, tool mocks, etc.
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow, onupdate=_utcnow)

    __table_args__ = (
        Index("ix_sim_env_ws_mode", "workspace_id", "mode"),
    )


class SimulationScenario(Base):
    """Definition of test input, context, faults, and assertions for a simulation."""

    __tablename__ = "simulation_scenarios"

    id = Column(String(36), primary_key=True, default=_gen_uuid)
    simulation_version_id = Column(String(36), nullable=True, index=True)
    suite_id = Column(String(36), nullable=True, index=True)
    workspace_id = Column(String(36), nullable=False, index=True)
    name = Column(String(128), nullable=False)
    description = Column(Text, nullable=True)
    scenario_type = Column(String(32), nullable=False, default="normal")  # normal, edge_case, failure, security, adversarial, regression, performance, policy
    input = Column(JSON, nullable=False, default=dict)
    context = Column(JSON, nullable=False, default=dict)
    environment_state = Column(JSON, nullable=False, default=dict)
    expected_behavior = Column(JSON, nullable=False, default=dict)
    fault_configuration = Column(JSON, nullable=False, default=dict)
    assertions = Column(JSON, nullable=False, default=list)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)

    __table_args__ = (
        Index("ix_sim_scen_ws_type", "workspace_id", "scenario_type"),
    )


class FaultProfile(Base):
    """Reusable bounded failure injection profile."""

    __tablename__ = "fault_profiles"

    id = Column(String(36), primary_key=True, default=_gen_uuid)
    workspace_id = Column(String(36), nullable=False, index=True)
    name = Column(String(128), nullable=False)
    description = Column(Text, nullable=True)
    faults = Column(JSON, nullable=False, default=dict)
    distribution_mode = Column(String(32), nullable=False, default="fixed")  # fixed, percentage, count, sequence
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)


class SimulationRun(Base):
    """Record of a simulation execution run."""

    __tablename__ = "simulation_runs"

    id = Column(String(36), primary_key=True, default=_gen_uuid)
    simulation_id = Column(String(36), ForeignKey("simulations.id", ondelete="CASCADE"), nullable=False, index=True)
    simulation_version_id = Column(String(36), nullable=True, index=True)
    scenario_id = Column(String(36), nullable=True, index=True)
    suite_id = Column(String(36), nullable=True, index=True)
    seed = Column(Integer, nullable=False, default=42)
    status = Column(String(32), nullable=False, default="queued", index=True)  # queued, running, completed, failed, cancelled
    target_type = Column(String(32), nullable=False)
    target_id = Column(String(36), nullable=False, index=True)
    target_version_id = Column(String(36), nullable=True)
    environment_snapshot_id = Column(String(36), nullable=True)
    execution_snapshot_id = Column(String(36), nullable=True)
    policy_snapshot = Column(JSON, nullable=False, default=dict)
    fault_snapshot = Column(JSON, nullable=False, default=dict)
    output = Column(JSON, nullable=False, default=dict)
    assertion_results = Column(JSON, nullable=False, default=list)
    side_effects = Column(JSON, nullable=False, default=list)
    events_count = Column(Integer, nullable=False, default=0)
    tool_calls = Column(JSON, nullable=False, default=list)
    connector_calls = Column(JSON, nullable=False, default=list)
    delegations = Column(JSON, nullable=False, default=list)
    tokens = Column(JSON, nullable=False, default=dict)
    cost = Column(Float, nullable=False, default=0.0)
    latency = Column(Float, nullable=False, default=0.0)
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    error = Column(Text, nullable=True)
    reproducibility_metadata = Column(JSON, nullable=False, default=dict)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)

    __table_args__ = (
        Index("ix_sim_runs_sim_status", "simulation_id", "status"),
        Index("ix_sim_runs_target", "target_type", "target_id"),
    )

    simulation = relationship("Simulation", back_populates="runs")
    assertions_rel = relationship("SimulationAssertion", back_populates="run", cascade="all, delete-orphan")
    side_effects_rel = relationship("SimulationSideEffect", back_populates="run", cascade="all, delete-orphan")
    fault_injections_rel = relationship("FaultInjection", back_populates="run", cascade="all, delete-orphan")


class FaultInjection(Base):
    """Record of an individual fault injected during a simulation run."""

    __tablename__ = "fault_injections"

    id = Column(String(36), primary_key=True, default=_gen_uuid)
    run_id = Column(String(36), ForeignKey("simulation_runs.id", ondelete="CASCADE"), nullable=False, index=True)
    fault_type = Column(String(64), nullable=False)
    target = Column(String(128), nullable=False)
    parameters = Column(JSON, nullable=False, default=dict)
    trigger_condition = Column(JSON, nullable=False, default=dict)
    injected_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)
    result = Column(String(64), nullable=False, default="injected")  # injected, bypassed, failed

    run = relationship("SimulationRun", back_populates="fault_injections_rel")


class SimulationAssertion(Base):
    """Detailed record of an assertion result evaluated during a simulation run."""

    __tablename__ = "simulation_assertions"

    id = Column(String(36), primary_key=True, default=_gen_uuid)
    run_id = Column(String(36), ForeignKey("simulation_runs.id", ondelete="CASCADE"), nullable=False, index=True)
    assertion_type = Column(String(64), nullable=False)
    parameters = Column(JSON, nullable=False, default=dict)
    expected = Column(JSON, nullable=True)
    actual = Column(JSON, nullable=True)
    passed = Column(Boolean, nullable=False)
    severity = Column(String(32), nullable=False, default="error")  # error, warning, info
    details = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)

    run = relationship("SimulationRun", back_populates="assertions_rel")


class SimulationSideEffect(Base):
    """Recorded intercepted side effect that would have occurred in production."""

    __tablename__ = "simulation_side_effects"

    id = Column(String(36), primary_key=True, default=_gen_uuid)
    run_id = Column(String(36), ForeignKey("simulation_runs.id", ondelete="CASCADE"), nullable=False, index=True)
    intended_action = Column(String(128), nullable=False)
    actor = Column(String(128), nullable=False, default="agent")
    target = Column(String(256), nullable=False)
    parameters = Column(JSON, nullable=False, default=dict)
    policy_decision = Column(String(64), nullable=False, default="blocked")
    would_require_approval = Column(Boolean, nullable=False, default=False)
    simulated_result = Column(JSON, nullable=False, default=dict)
    intercepted_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)

    run = relationship("SimulationRun", back_populates="side_effects_rel")


class SimulationSuite(Base):
    """A regression test suite composed of simulation scenarios."""

    __tablename__ = "simulation_suites"

    id = Column(String(36), primary_key=True, default=_gen_uuid)
    workspace_id = Column(String(36), nullable=False, index=True)
    project_id = Column(String(36), nullable=True, index=True)
    name = Column(String(128), nullable=False)
    description = Column(Text, nullable=True)
    target_type = Column(String(32), nullable=False)
    target_id = Column(String(36), nullable=False, index=True)
    status = Column(String(32), nullable=False, default="active", index=True)
    created_by = Column(String(36), nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow, onupdate=_utcnow)

    __table_args__ = (
        Index("ix_sim_suites_ws_target", "workspace_id", "target_type", "target_id"),
    )

    scenarios = relationship("SimulationSuiteScenario", back_populates="suite", cascade="all, delete-orphan", order_by="SimulationSuiteScenario.order_index")


class SimulationSuiteScenario(Base):
    """Association linking scenarios to a simulation suite."""

    __tablename__ = "simulation_suite_scenarios"

    id = Column(String(36), primary_key=True, default=_gen_uuid)
    suite_id = Column(String(36), ForeignKey("simulation_suites.id", ondelete="CASCADE"), nullable=False, index=True)
    scenario_id = Column(String(36), nullable=False, index=True)
    order_index = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)

    suite = relationship("SimulationSuite", back_populates="scenarios")


class SimulationComparison(Base):
    """Factual comparative analysis between two simulation runs."""

    __tablename__ = "simulation_comparisons"

    id = Column(String(36), primary_key=True, default=_gen_uuid)
    workspace_id = Column(String(36), nullable=False, index=True)
    baseline_run_id = Column(String(36), nullable=False, index=True)
    comparison_run_id = Column(String(36), nullable=False, index=True)
    factual_differences = Column(JSON, nullable=False, default=dict)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)

    __table_args__ = (
        Index("ix_sim_comp_pair", "baseline_run_id", "comparison_run_id"),
    )
