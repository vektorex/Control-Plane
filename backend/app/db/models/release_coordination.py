from sqlalchemy import Column, String, DateTime, Text, JSON, Boolean, ForeignKey, Integer
from sqlalchemy.sql import func
from backend.app.db.base import Base

class ReleasePortfolio(Base):
    __tablename__ = "release_portfolios"

    id = Column(String(36), primary_key=True, index=True)
    organization_id = Column(String(36), ForeignKey("organizations.id"), nullable=False, index=True)
    workspace_id = Column(String(36), ForeignKey("workspaces.id"), nullable=False, index=True)
    project_id = Column(String(36), ForeignKey("projects.id"), nullable=True, index=True)

    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)

    status = Column(String(50), nullable=False)
    owner_id = Column(String(36), nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

class ReleaseTrain(Base):
    __tablename__ = "release_trains"

    id = Column(String(36), primary_key=True, index=True)
    portfolio_id = Column(String(36), ForeignKey("release_portfolios.id"), nullable=False, index=True)

    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)

    status = Column(String(50), nullable=False)
    version = Column(Integer, nullable=False, default=1)
    owner_id = Column(String(36), nullable=False)

    start_window = Column(DateTime(timezone=True), nullable=True)
    target_completion = Column(DateTime(timezone=True), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

class ReleaseGroup(Base):
    __tablename__ = "release_groups"

    id = Column(String(36), primary_key=True, index=True)
    release_train_id = Column(String(36), ForeignKey("release_trains.id"), nullable=False, index=True)

    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    purpose = Column(String(50), nullable=False)
    
    sequence_order = Column(Integer, nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

class ReleaseWave(Base):
    __tablename__ = "release_waves"

    id = Column(String(36), primary_key=True, index=True)
    release_train_id = Column(String(36), ForeignKey("release_trains.id"), nullable=False, index=True)

    name = Column(String(255), nullable=False)
    sequence_number = Column(Integer, nullable=False)

    status = Column(String(50), nullable=False)

    planned_start = Column(DateTime(timezone=True), nullable=True)
    planned_end = Column(DateTime(timezone=True), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

class ReleaseSequence(Base):
    __tablename__ = "release_sequences"

    id = Column(String(36), primary_key=True, index=True)
    release_train_id = Column(String(36), ForeignKey("release_trains.id"), nullable=False, index=True)
    
    release_id = Column(String(36), ForeignKey("releases.id"), nullable=False, index=True)
    wave_id = Column(String(36), ForeignKey("release_waves.id"), nullable=True, index=True)

    sequence_number = Column(Integer, nullable=False)
    reason = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

class ReleaseWaveItem(Base):
    __tablename__ = "release_wave_items"

    id = Column(String(36), primary_key=True, index=True)
    wave_id = Column(String(36), ForeignKey("release_waves.id"), nullable=False, index=True)
    release_id = Column(String(36), ForeignKey("releases.id"), nullable=False, index=True)

    sequence_order = Column(Integer, nullable=False)
    required = Column(Boolean, nullable=False, default=True)
    status = Column(String(50), nullable=False)

class ReleaseDependency(Base):
    __tablename__ = "release_dependencies"

    id = Column(String(36), primary_key=True, index=True)
    release_train_id = Column(String(36), ForeignKey("release_trains.id"), nullable=False, index=True)

    source_release_id = Column(String(36), ForeignKey("releases.id"), nullable=False)
    target_release_id = Column(String(36), ForeignKey("releases.id"), nullable=False)

    dependency_type = Column(String(50), nullable=False)
    reason = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

class ReleaseConflict(Base):
    __tablename__ = "release_conflicts"

    id = Column(String(36), primary_key=True, index=True)
    release_train_id = Column(String(36), ForeignKey("release_trains.id"), nullable=False, index=True)

    release_a_id = Column(String(36), ForeignKey("releases.id"), nullable=True)
    release_b_id = Column(String(36), ForeignKey("releases.id"), nullable=True)

    conflict_type = Column(String(50), nullable=False)
    severity = Column(String(50), nullable=False)
    
    description = Column(Text, nullable=False)
    evidence = Column(JSON, nullable=False)
    
    status = Column(String(50), nullable=False)
    resolution = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    resolved_at = Column(DateTime(timezone=True), nullable=True)

class ChangeWindow(Base):
    __tablename__ = "change_windows"

    id = Column(String(36), primary_key=True, index=True)
    organization_id = Column(String(36), ForeignKey("organizations.id"), nullable=False, index=True)
    workspace_id = Column(String(36), ForeignKey("workspaces.id"), nullable=False, index=True)
    project_id = Column(String(36), ForeignKey("projects.id"), nullable=True, index=True)

    name = Column(String(255), nullable=False)
    window_type = Column(String(50), nullable=False)
    
    starts_at = Column(DateTime(timezone=True), nullable=False)
    ends_at = Column(DateTime(timezone=True), nullable=False)
    timezone = Column(String(50), nullable=False)

    description = Column(Text, nullable=True)
    active = Column(Boolean, nullable=False, default=True)

    created_by = Column(String(36), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

class ReleaseCalendarEntry(Base):
    __tablename__ = "release_calendar_entries"

    id = Column(String(36), primary_key=True, index=True)
    release_train_id = Column(String(36), ForeignKey("release_trains.id"), nullable=True, index=True)

    release_id = Column(String(36), ForeignKey("releases.id"), nullable=True, index=True)
    rollout_id = Column(String(36), ForeignKey("progressive_rollouts.id"), nullable=True, index=True)

    entry_type = Column(String(50), nullable=False)
    
    starts_at = Column(DateTime(timezone=True), nullable=False)
    ends_at = Column(DateTime(timezone=True), nullable=True)
    
    environment = Column(String(50), nullable=False)
    status = Column(String(50), nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

class CoordinationDecision(Base):
    __tablename__ = "coordination_decisions"

    id = Column(String(36), primary_key=True, index=True)
    release_train_id = Column(String(36), ForeignKey("release_trains.id"), nullable=False, index=True)

    decision_type = Column(String(50), nullable=False)
    decision = Column(JSON, nullable=False)
    
    reason = Column(Text, nullable=False)
    evidence = Column(JSON, nullable=False)

    created_by = Column(String(36), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
