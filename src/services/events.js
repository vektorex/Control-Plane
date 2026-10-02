/**
 * Event Bus and Execution Stream API service client for Step 26.
 */
import { apiClient } from '@/lib/api';
import { buildStreamQuery } from '@/lib/events/eventFilters';

export const eventService = {
  /**
   * List historical events with multi-tenant filtering.
   */
  async listEvents(params = {}) {
    const query = new URLSearchParams();
    if (params.workspace_id) query.set('workspace_id', params.workspace_id);
    if (params.project_id) query.set('project_id', params.project_id);
    if (params.event_type) query.set('event_type', params.event_type);
    if (params.aggregate_type) query.set('aggregate_type', params.aggregate_type);
    if (params.aggregate_id) query.set('aggregate_id', params.aggregate_id);
    if (params.correlation_id) query.set('correlation_id', params.correlation_id);
    if (params.after) query.set('after', params.after);
    if (params.limit) query.set('limit', String(params.limit));

    const qs = query.toString();
    const url = `/api/events${qs ? `?${qs}` : ''}`;
    const headers = {};
    if (params.workspace_id) {
      headers['X-Workspace-Id'] = params.workspace_id;
    }
    return apiClient.get(url, { headers });
  },

  /**
   * Get single event details by ID.
   */
  async getEvent(eventId, workspaceId = null) {
    const headers = {};
    if (workspaceId) {
      headers['X-Workspace-Id'] = workspaceId;
    }
    return apiClient.get(`/api/events/${eventId}`, { headers });
  },

  /**
   * Replay historical events after a cursor event ID.
   */
  async replayEvents(params = {}) {
    const query = new URLSearchParams();
    if (params.after) query.set('after', params.after);
    if (params.event_type) query.set('event_type', params.event_type);
    if (params.limit) query.set('limit', String(params.limit));
    if (params.workspace_id) query.set('workspace_id', params.workspace_id);

    const qs = query.toString();
    const url = `/api/events/replay${qs ? `?${qs}` : ''}`;
    const headers = {};
    if (params.workspace_id) {
      headers['X-Workspace-Id'] = params.workspace_id;
    }
    return apiClient.get(url, { headers });
  },

  /**
   * Returns stream URL for EventSource.
   */
  getStreamUrl(params = {}) {
    return `/api/events/stream${buildStreamQuery(params)}`;
  },
};
