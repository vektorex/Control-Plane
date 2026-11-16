import { apiClient } from "@/lib/api";

export const catalogService = {
  async listCatalogItems(params = {}) {
    return apiClient("/catalog", { params });
  },

  async getCatalogItem(itemId) {
    return apiClient(`/catalog/${itemId}`);
  },

  async registerItem(payload) {
    return apiClient("/catalog", {
      method: "POST",
      body: payload,
    });
  },

  async searchItems(query, filters = null) {
    return apiClient("/catalog/search", {
      method: "POST",
      params: { query },
      body: filters ? { filters } : undefined,
    });
  },

  async checkCompatibility(itemId, request) {
    return apiClient(`/catalog/${itemId}/compatibility`, {
      method: "POST",
      body: request,
    });
  },

  async searchCapabilities(query) {
    return this.searchItems(query);
  },
};

export default catalogService;
