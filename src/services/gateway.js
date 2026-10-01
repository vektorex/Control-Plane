import { apiClient } from "@/lib/api";

export async function listGatewayModels(params = {}) {
  return apiClient("/gateway/models", { params });
}

export async function listGatewayProviders() {
  return apiClient("/gateway/providers");
}

export async function getGatewayHealth() {
  return apiClient("/gateway/health");
}

export async function previewGatewayRouting(data) {
  return apiClient("/gateway/preview", {
    method: "POST",
    body: data,
  });
}

export async function testGatewayPrompt(data) {
  return apiClient("/gateway/test", {
    method: "POST",
    body: data,
  });
}

export async function getGatewayPolicy() {
  return apiClient("/gateway/policies");
}

export async function updateGatewayPolicy(data) {
  return apiClient("/gateway/policies", {
    method: "PATCH",
    body: data,
  });
}
