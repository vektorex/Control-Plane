import { apiClient } from "@/lib/api";

export const contractsService = {
  async listContracts(params = {}) {
    try {
      return await apiClient("/contracts", { params });
    } catch (err) {
      // Graceful fallback if list endpoint is pending in backend
      if (err.status === 404 || err.status === 405) {
        return [];
      }
      throw err;
    }
  },

  async getContract(contractId) {
    return apiClient(`/contracts/${contractId}`);
  },

  async createContract(payload) {
    return apiClient("/contracts", {
      method: "POST",
      body: payload,
    });
  },

  async proposeContract(contractId) {
    return apiClient(`/contracts/${contractId}/propose`, {
      method: "POST",
    });
  },

  async approveContract(contractId) {
    return apiClient(`/contracts/${contractId}/approve`, {
      method: "POST",
    });
  },

  async activateContract(contractId) {
    return apiClient(`/contracts/${contractId}/activate`, {
      method: "POST",
    });
  },

  async listBreaches(contractId) {
    return apiClient(`/contracts/${contractId}/breaches`);
  },

  async getAnalytics(contractId) {
    return apiClient(`/contracts/${contractId}/analytics`);
  },
};

export const contractService = contractsService;
export default contractsService;
