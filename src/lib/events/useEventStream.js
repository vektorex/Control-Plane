'use client';

import { useEffect, useRef, useState } from 'react';
import { EventClient } from './eventClient';
import { CONNECTION_STATUS } from './eventTypes';
import { globalEventStore } from './eventStore';

/**
 * React hook for consuming real-time execution events via SSE with fallback polling.
 */
export function useEventStream(options = {}) {
  const {
    workspaceId,
    projectId,
    eventType,
    aggregateType,
    aggregateId,
    onEvent,
    fallbackPollingInterval = 10000,
    fallbackPollingFn,
    store = globalEventStore,
  } = options;

  const [status, setStatus] = useState(CONNECTION_STATUS.DISCONNECTED);
  const [lastEvent, setLastEvent] = useState(null);
  const [recentEvents, setRecentEvents] = useState(() => store.getRecentEvents());
  const clientRef = useRef(null);
  const onEventRef = useRef(onEvent);
  onEventRef.current = onEvent;

  const fallbackPollingFnRef = useRef(fallbackPollingFn);
  fallbackPollingFnRef.current = fallbackPollingFn;

  useEffect(() => {
    if (!workspaceId) return;

    const client = new EventClient({
      workspaceId,
      projectId,
      eventType,
      aggregateType,
      aggregateId,
      store,
    });
    clientRef.current = client;

    // Listen to status transitions
    const unsubStatus = client.on('_status', ({ status: newStatus }) => {
      setStatus(newStatus);
    });

    // Listen to all events
    const unsubAll = client.on('*', (event) => {
      setLastEvent(event);
      setRecentEvents(store.getRecentEvents());
      if (onEventRef.current) {
        try {
          onEventRef.current(event);
        } catch (err) {
          console.error('[useEventStream] Error in onEvent callback:', err);
        }
      }
    });

    // Connect
    client.connect();

    return () => {
      unsubStatus();
      unsubAll();
      client.disconnect();
      clientRef.current = null;
    };
  }, [workspaceId, projectId, eventType, aggregateType, aggregateId, store]);

  // Fallback Polling Effect: Active only when SSE connection has fallen back
  useEffect(() => {
    if (status !== CONNECTION_STATUS.FALLBACK || !fallbackPollingFnRef.current) {
      return;
    }

    // Execute immediately once upon entering fallback
    fallbackPollingFnRef.current();

    const interval = setInterval(() => {
      if (fallbackPollingFnRef.current) {
        fallbackPollingFnRef.current();
      }
    }, fallbackPollingInterval);

    return () => clearInterval(interval);
  }, [status, fallbackPollingInterval]);

  return {
    status,
    lastEvent,
    recentEvents,
    isConnected: status === CONNECTION_STATUS.CONNECTED,
    isConnecting: status === CONNECTION_STATUS.CONNECTING,
    isPollingFallback: status === CONNECTION_STATUS.FALLBACK,
    client: clientRef.current,
  };
}
