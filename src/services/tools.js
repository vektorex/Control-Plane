import { apiClient } from "@/lib/api";

/**
 * Service methods for the Provider-Independent Tool System (Step 9).
 */
export const toolService = {
  /**
   * List all available tools registered for the authenticated user
   */
  async listTools() {
    return apiClient("/tools");
  },

  /**
   * Execute a registered tool directly with normalized ToolResult output
   */
  async executeTool(toolName, input) {
    return apiClient(`/tools/${toolName}/execute`, {
      method: "POST",
      body: { input },
    });
  },
};
