import { apiClient } from "@/lib/api";

/**
 * Frontend client service for Step 30: Multimodal AI and Unified Artifact Intelligence.
 */
export const artifactService = {
  /**
   * Upload a new artifact (image, document, audio, video, table).
   * @param {File} file - Browser File instance
   * @param {Object} options - { projectId, metadata }
   */
  async uploadArtifact(file, { projectId = null, metadata = {} } = {}) {
    const formData = new FormData();
    formData.append("file", file);
    if (projectId) {
      formData.append("project_id", projectId);
    }
    if (metadata && Object.keys(metadata).length > 0) {
      formData.append("metadata", JSON.stringify(metadata));
    }

    return apiClient("/artifacts", {
      method: "POST",
      body: formData,
    });
  },

  /**
   * List artifacts with filtering by type, status, project, and pagination.
   */
  async listArtifacts(params = {}) {
    return apiClient("/artifacts", { params });
  },

  /**
   * Get an artifact by ID including metadata, parts count, and status.
   */
  async getArtifact(artifactId) {
    return apiClient(`/artifacts/${artifactId}`);
  },

  /**
   * Delete an artifact and clean up its parts and storage references.
   */
  async deleteArtifact(artifactId) {
    return apiClient(`/artifacts/${artifactId}`, {
      method: "DELETE",
    });
  },

  /**
   * Trigger media processing/extraction on an uploaded artifact.
   */
  async processArtifact(artifactId) {
    return apiClient(`/artifacts/${artifactId}/process`, {
      method: "POST",
    });
  },

  /**
   * Fetch extracted artifact parts (images, tables, audio transcripts, frames, text).
   */
  async getArtifactParts(artifactId) {
    return apiClient(`/artifacts/${artifactId}/parts`);
  },

  /**
   * Get lightweight status and progress polling information.
   */
  async getArtifactStatus(artifactId) {
    return apiClient(`/artifacts/${artifactId}/status`);
  },

  /**
   * Run multimodal reasoning/analysis on an artifact through AI Gateway.
   * @param {string} artifactId
   * @param {Object} payload - { instruction: string, mode: "auto" | "vision" | "audio" | "video" | "table" }
   */
  async analyzeArtifact(artifactId, payload) {
    return apiClient(`/artifacts/${artifactId}/analyze`, {
      method: "POST",
      body: payload,
    });
  },

  /**
   * Trigger immediate synchronous extraction of parts from an artifact.
   */
  async extractArtifact(artifactId) {
    return apiClient(`/artifacts/${artifactId}/extract`, {
      method: "POST",
    });
  },
};
