/**
 * Event Filters and Matcher Utilities for Step 26.
 */

/**
 * Checks whether an event type satisfies a filter pattern (e.g. 'job.*' or 'workflow.completed').
 */
export function matchesFilter(eventType, pattern) {
  if (!pattern || pattern === '*') {
    return true;
  }
  if (!eventType) {
    return false;
  }

  if (pattern.endsWith('.*')) {
    const prefix = pattern.slice(0, -1); // 'job.'
    return eventType.startsWith(prefix);
  }

  return eventType === pattern;
}

/**
 * Builds the URL query string for SSE streaming.
 */
export function buildStreamQuery({
  workspaceId,
  projectId,
  eventType,
  aggregateType,
  aggregateId,
  after,
}) {
  const params = new URLSearchParams();

  if (workspaceId) params.set('workspace_id', workspaceId);
  if (projectId) params.set('project_id', projectId);
  if (eventType) params.set('event_type', eventType);
  if (aggregateType) params.set('aggregate_type', aggregateType);
  if (aggregateId) params.set('aggregate_id', aggregateId);
  if (after) params.set('after', after);

  const qs = params.toString();
  return qs ? `?${qs}` : '';
}
