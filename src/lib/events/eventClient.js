/**
 * Production-grade Server-Sent Events (SSE) Client for Step 26.
 * Features:
 * - Automatic reconnect with jittered exponential backoff
 * - Last-Event-ID resumption
 * - Bounded failure retries before transitioning to polling fallback
 * - Memory leak prevention and clean teardown
 */

import { CONNECTION_STATUS } from './eventTypes';
import { buildStreamQuery, matchesFilter } from './eventFilters';
import { globalEventStore } from './eventStore';

export class EventClient {
  constructor(options = {}) {
    this.options = {
      baseUrl: '/api/events/stream',
      workspaceId: null,
      projectId: null,
      eventType: null,
      aggregateType: null,
      aggregateId: null,
      maxConsecutiveErrors: 5,
      baseReconnectDelayMs: 1000,
      maxReconnectDelayMs: 30000,
      store: globalEventStore,
      ...options,
    };

    this.eventSource = null;
    this.status = CONNECTION_STATUS.DISCONNECTED;
    this.consecutiveErrors = 0;
    this.reconnectTimer = null;
    this.listeners = new Map(); // eventType -> Set<callback>
    this.isManualDisconnect = false;
  }

  setStatus(newStatus) {
    this.status = newStatus;
    if (this.options.store) {
      this.options.store.setStatus(newStatus);
    }
    this.emit('_status', { status: newStatus });
  }

  connect() {
    if (typeof window === 'undefined') return; // SSR safe
    if (this.eventSource) {
      this.disconnect();
    }

    this.isManualDisconnect = false;
    this.setStatus(CONNECTION_STATUS.CONNECTING);

    const lastId = this.options.store ? this.options.store.getLastEventId() : null;
    const query = buildStreamQuery({
      workspaceId: this.options.workspaceId,
      projectId: this.options.projectId,
      eventType: this.options.eventType,
      aggregateType: this.options.aggregateType,
      aggregateId: this.options.aggregateId,
      after: lastId,
    });

    const url = `${this.options.baseUrl}${query}`;

    try {
      this.eventSource = new EventSource(url, { withCredentials: true });

      this.eventSource.onopen = () => {
        this.consecutiveErrors = 0;
        this.setStatus(CONNECTION_STATUS.CONNECTED);
      };

      this.eventSource.onmessage = (e) => {
        this.handleRawMessage(e);
      };

      this.eventSource.onerror = (err) => {
        this.handleError(err);
      };
    } catch (err) {
      this.handleError(err);
    }
  }

  handleRawMessage(e) {
    if (!e.data) return;
    try {
      const parsed = JSON.parse(e.data);
      if (parsed && parsed.id) {
        if (this.options.store) {
          this.options.store.addEvent(parsed);
        }
        this.emit(parsed.type || 'message', parsed);
        this.emit('*', parsed);
      }
    } catch (err) {
      console.warn('[EventClient] Failed parsing event data:', err);
    }
  }

  handleError(err) {
    if (this.isManualDisconnect) return;

    if (this.eventSource) {
      this.eventSource.close();
      this.eventSource = null;
    }

    this.consecutiveErrors++;

    if (this.consecutiveErrors >= this.options.maxConsecutiveErrors) {
      // Transition to polling fallback to prevent infinite tight reconnect loops
      this.setStatus(CONNECTION_STATUS.FALLBACK);
      console.warn('[EventClient] Max SSE reconnect attempts reached. Falling back to polling.');
      return;
    }

    this.setStatus(CONNECTION_STATUS.ERROR);
    this.scheduleReconnect();
  }

  scheduleReconnect() {
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
    }

    // Exponential backoff with jitter
    const delay = Math.min(
      this.options.maxReconnectDelayMs,
      this.options.baseReconnectDelayMs * Math.pow(2, this.consecutiveErrors)
    ) * (0.8 + Math.random() * 0.4);

    this.reconnectTimer = setTimeout(() => {
      this.connect();
    }, delay);
  }

  disconnect() {
    this.isManualDisconnect = true;
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }
    if (this.eventSource) {
      this.eventSource.close();
      this.eventSource = null;
    }
    this.setStatus(CONNECTION_STATUS.DISCONNECTED);
  }

  on(eventType, callback) {
    if (!this.listeners.has(eventType)) {
      this.listeners.set(eventType, new Set());
    }
    this.listeners.get(eventType).add(callback);

    // Also register with native eventSource for custom event names
    if (this.eventSource && eventType !== '*' && eventType !== '_status') {
      this.eventSource.addEventListener(eventType, (e) => this.handleRawMessage(e));
    }

    return () => this.off(eventType, callback);
  }

  off(eventType, callback) {
    const set = this.listeners.get(eventType);
    if (set) {
      set.delete(callback);
      if (set.size === 0) {
        this.listeners.delete(eventType);
      }
    }
  }

  emit(eventType, data) {
    // Notify exact matches
    const set = this.listeners.get(eventType);
    if (set) {
      for (const cb of set) {
        try {
          cb(data);
        } catch (err) {
          console.error(`[EventClient] Error in listener for ${eventType}:`, err);
        }
      }
    }

    // Notify pattern listeners (e.g. 'job.*')
    for (const [pattern, listeners] of this.listeners.entries()) {
      if (pattern !== eventType && pattern !== '*' && matchesFilter(eventType, pattern)) {
        for (const cb of listeners) {
          try {
            cb(data);
          } catch (err) {
            console.error(`[EventClient] Error in pattern listener for ${pattern}:`, err);
          }
        }
      }
    }
  }
}
