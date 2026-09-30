import { apiClient } from "@/lib/api";

/**
 * Service methods for the Secure Provider-Independent Connector System (Step 16).
 */
export const connectorService = {
  /**
   * List all registered connectors in the system
   */
  async listConnectors() {
    return apiClient("/connectors");
  },

  /**
   * Get metadata and configuration schema for a specific connector
   */
  async getConnector(connectorName) {
    return apiClient(`/connectors/${connectorName}`);
  },

  /**
   * List all supported operations for a connector
   */
  async getOperations(connectorName) {
    return apiClient(`/connectors/${connectorName}/operations`);
  },

  /**
   * Get current connection status for a connector in the active workspace
   */
  async getStatus(connectorName) {
    return apiClient(`/connectors/${connectorName}/status`);
  },

  /**
   * Connect and securely store credentials (encrypted via AES-256-GCM)
   */
  async connect(connectorName, { credential, credentialType = "pat", metadata = {} }) {
    return apiClient(`/connectors/${connectorName}/connect`, {
      method: "POST",
      body: {
        credential,
        credential_type: credentialType,
        metadata,
      },
    });
  },

  /**
   * Disconnect and purge encrypted credentials for the workspace
   */
  async disconnect(connectorName) {
    return apiClient(`/connectors/${connectorName}/disconnect`, {
      method: "DELETE",
    });
  },

  /**
   * Test active connection and retrieve verified account information
   */
  async testConnection(connectorName) {
    return apiClient(`/connectors/${connectorName}/test`, {
      method: "POST",
    });
  },

  /**
   * List operation-level permissions for a connector
   */
  async getPermissions(connectorName) {
    return apiClient(`/connectors/${connectorName}/permissions`);
  },

  /**
   * Update operation-level permission (enable/disable or set level)
   */
  async updatePermission(connectorName, { operation, enabled, permissionLevel = "read" }) {
    return apiClient(`/connectors/${connectorName}/permissions`, {
      method: "PATCH",
      body: {
        operation,
        enabled,
        permission_level: permissionLevel,
      },
    });
  },

  /**
   * Execute a connector operation directly
   */
  async executeOperation(connectorName, operation, args = {}) {
    return apiClient(`/connectors/${connectorName}/execute`, {
      method: "POST",
      body: {
        operation,
        arguments: args,
      },
    });
  },
};
