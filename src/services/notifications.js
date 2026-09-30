import { apiClient } from "@/lib/api";

/**
 * Service methods for User In-App Notifications (Step 18).
 */
export const notificationService = {
  /**
   * List notifications for current user in active workspace.
   */
  async listNotifications(params = {}) {
    const query = new URLSearchParams();
    if (params.unread_only) query.set("unread_only", "true");
    if (params.limit) query.set("limit", String(params.limit));
    const queryString = query.toString() ? `?${query.toString()}` : "";
    return apiClient(`/notifications${queryString}`);
  },

  /**
   * Mark a specific notification as read.
   */
  async markAsRead(notificationId) {
    return apiClient(`/notifications/${notificationId}/read`, {
      method: "POST",
    });
  },

  /**
   * Mark all notifications as read for current user.
   */
  async markAllAsRead() {
    return apiClient("/notifications/read-all", {
      method: "POST",
    });
  },
};
