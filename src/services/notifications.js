import { apiClient } from "@/lib/api";

/**
 * Service client for Step 25: Notifications & External Delivery Layer.
 */
export const notificationService = {
  // ---------------------------------------------------------------------------
  // 1. In-App Notifications
  // ---------------------------------------------------------------------------

  /**
   * List notifications for current user with optional filtering.
   */
  async listNotifications(params = {}) {
    const query = new URLSearchParams();
    if (params.unread_only) query.set("unread_only", "true");
    if (params.severity) query.set("severity", params.severity);
    if (params.event_type) query.set("event_type", params.event_type);
    if (params.source_type) query.set("source_type", params.source_type);
    if (params.limit) query.set("limit", String(params.limit));
    if (params.offset) query.set("offset", String(params.offset));
    const queryString = query.toString() ? `?${query.toString()}` : "";
    return apiClient(`/notifications${queryString}`);
  },

  /**
   * Fetch a single notification by ID.
   */
  async getNotification(notificationId) {
    return apiClient(`/notifications/${notificationId}`);
  },

  /**
   * Get total unread notifications count for current user in active workspace.
   */
  async getUnreadCount() {
    return apiClient("/notifications/unread-count");
  },

  /**
   * Mark a single notification as read.
   */
  async markAsRead(notificationId) {
    return apiClient(`/notifications/${notificationId}/read`, {
      method: "POST",
    });
  },

  /**
   * Mark all unread notifications as read.
   */
  async markAllAsRead() {
    return apiClient("/notifications/read-all", {
      method: "POST",
    });
  },

  /**
   * Archive a notification.
   */
  async archiveNotification(notificationId) {
    return apiClient(`/notifications/${notificationId}/archive`, {
      method: "POST",
    });
  },

  // ---------------------------------------------------------------------------
  // 2. Webhook Endpoints Management
  // ---------------------------------------------------------------------------

  /**
   * Register a new webhook endpoint (returns signing secret once).
   */
  async createWebhookEndpoint(payload) {
    return apiClient("/webhooks", {
      method: "POST",
      body: JSON.stringify(payload),
    });
  },

  /**
   * List configured webhooks for active workspace.
   */
  async listWebhookEndpoints() {
    return apiClient("/webhooks");
  },

  /**
   * Get single webhook endpoint details.
   */
  async getWebhookEndpoint(endpointId) {
    return apiClient(`/webhooks/${endpointId}`);
  },

  /**
   * Update webhook endpoint configuration (URL, subscribed events, active state).
   */
  async updateWebhookEndpoint(endpointId, payload) {
    return apiClient(`/webhooks/${endpointId}`, {
      method: "PATCH",
      body: JSON.stringify(payload),
    });
  },

  /**
   * Delete a webhook endpoint.
   */
  async deleteWebhookEndpoint(endpointId) {
    return apiClient(`/webhooks/${endpointId}`, {
      method: "DELETE",
    });
  },

  /**
   * Send a safe synthetic test payload to the webhook endpoint.
   */
  async testWebhookEndpoint(endpointId) {
    return apiClient(`/webhooks/${endpointId}/test`, {
      method: "POST",
    });
  },

  /**
   * Rotate HMAC signing secret for a webhook endpoint.
   */
  async rotateWebhookSecret(endpointId) {
    return apiClient(`/webhooks/${endpointId}/rotate-secret`, {
      method: "POST",
    });
  },

  /**
   * List recent delivery attempts for a specific webhook endpoint.
   */
  async listWebhookDeliveries(endpointId) {
    return apiClient(`/webhooks/${endpointId}/deliveries`);
  },

  // ---------------------------------------------------------------------------
  // 3. Notification Preferences
  // ---------------------------------------------------------------------------

  /**
   * Get notification preferences for current workspace and user.
   */
  async getPreferences() {
    return apiClient("/notification-preferences");
  },

  /**
   * Update notification channel preferences.
   */
  async updatePreferences(preferences) {
    return apiClient("/notification-preferences", {
      method: "PUT",
      body: JSON.stringify({ preferences }),
    });
  },

  // ---------------------------------------------------------------------------
  // 4. Delivery Audit Logs
  // ---------------------------------------------------------------------------

  /**
   * List delivery audit logs across all channels.
   */
  async listDeliveries(params = {}) {
    const query = new URLSearchParams();
    if (params.notification_id) query.set("notification_id", params.notification_id);
    if (params.channel) query.set("channel", params.channel);
    if (params.status) query.set("status", params.status);
    if (params.limit) query.set("limit", String(params.limit));
    if (params.offset) query.set("offset", String(params.offset));
    const queryString = query.toString() ? `?${query.toString()}` : "";
    return apiClient(`/notification-deliveries${queryString}`);
  },

  /**
   * Get delivery audit details by ID.
   */
  async getDelivery(deliveryId) {
    return apiClient(`/notification-deliveries/${deliveryId}`);
  },
};
