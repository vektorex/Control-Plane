/**
 * Event Types and Connection Enums for Step 26: Unified Event Bus & Real-Time Updates.
 */

export const JOB_EVENTS = {
  CREATED: 'job.created',
  QUEUED: 'job.queued',
  STARTED: 'job.started',
  PROGRESS: 'job.progress',
  RETRYING: 'job.retrying',
  CANCEL_REQUESTED: 'job.cancel_requested',
  CANCELLED: 'job.cancelled',
  COMPLETED: 'job.completed',
  FAILED: 'job.failed',
  RECOVERED: 'job.recovered',
};

export const WORKFLOW_EVENTS = {
  STARTED: 'workflow.started',
  STEP_STARTED: 'workflow.step_started',
  STEP_COMPLETED: 'workflow.step_completed',
  WAITING_FOR_APPROVAL: 'workflow.waiting_for_approval',
  RESUMED: 'workflow.resumed',
  COMPLETED: 'workflow.completed',
  FAILED: 'workflow.failed',
};

export const TRIGGER_EVENTS = {
  CREATED: 'trigger.created',
  UPDATED: 'trigger.updated',
  PAUSED: 'trigger.paused',
  RESUMED: 'trigger.resumed',
  FIRED: 'trigger.fired',
  COMPLETED: 'trigger.completed',
  FAILED: 'trigger.failed',
};

export const DOCUMENT_EVENTS = {
  STARTED: 'document.processing_started',
  PROGRESS: 'document.processing_progress',
  COMPLETED: 'document.processing_completed',
  FAILED: 'document.processing_failed',
};

export const EVALUATION_EVENTS = {
  STARTED: 'evaluation.started',
  COMPLETED: 'evaluation.completed',
  REGRESSION_DETECTED: 'evaluation.regression_detected',
  FAILED: 'evaluation.failed',
};

export const REPLAY_EVENTS = {
  STARTED: 'replay.started',
  PROGRESS: 'replay.progress',
  COMPLETED: 'replay.completed',
  FAILED: 'replay.failed',
};

export const CONNECTOR_EVENTS = {
  STARTED: 'connector.started',
  COMPLETED: 'connector.completed',
  FAILED: 'connector.failed',
};

export const APPROVAL_EVENTS = {
  REQUESTED: 'approval.requested',
  APPROVED: 'approval.approved',
  REJECTED: 'approval.rejected',
  EXPIRED: 'approval.expired',
};

export const NOTIFICATION_EVENTS = {
  CREATED: 'notification.created',
  DELIVERY_STARTED: 'notification.delivery_started',
  DELIVERY_COMPLETED: 'notification.delivery_completed',
  DELIVERY_FAILED: 'notification.delivery_failed',
};

export const SYSTEM_EVENTS = {
  WARNING: 'system.warning',
  ERROR: 'system.error',
};

export const CONNECTION_STATUS = {
  DISCONNECTED: 'disconnected',
  CONNECTING: 'connecting',
  CONNECTED: 'connected',
  ERROR: 'error',
  FALLBACK: 'fallback',
};
