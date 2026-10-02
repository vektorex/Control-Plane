/**
 * Lightweight client-side bounded event store for Step 26.
 * Tracks connection status, last event ID, and a bounded recent-events buffer.
 */

export class EventStore {
  constructor(maxSize = 100) {
    this.maxSize = maxSize;
    this.recentEvents = [];
    this.lastEventId = null;
    this.status = 'disconnected';
    this.listeners = new Set();
  }

  addEvent(event) {
    if (!event || !event.id) return;

    this.lastEventId = event.id;

    // Avoid duplicate insertions
    if (this.recentEvents.some((e) => e.id === event.id)) {
      return;
    }

    this.recentEvents.unshift(event);
    if (this.recentEvents.length > this.maxSize) {
      this.recentEvents.pop();
    }

    this.notify();
  }

  setStatus(status) {
    if (this.status !== status) {
      this.status = status;
      this.notify();
    }
  }

  getRecentEvents() {
    return [...this.recentEvents];
  }

  getLastEventId() {
    return this.lastEventId;
  }

  subscribe(listener) {
    this.listeners.add(listener);
    return () => {
      this.listeners.delete(listener);
    };
  }

  notify() {
    for (const listener of this.listeners) {
      try {
        listener(this);
      } catch (err) {
        console.error('[EventStore] Listener error:', err);
      }
    }
  }

  clear() {
    this.recentEvents = [];
    this.lastEventId = null;
    this.notify();
  }
}

// Global default store instance
export const globalEventStore = new EventStore(100);
