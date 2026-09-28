import { apiClient } from "@/lib/api";

export const documentService = {
  /**
   * List all documents belonging to a workspace
   */
  async listWorkspaceDocuments(workspaceId, params = {}) {
    return apiClient(`/workspaces/${workspaceId}/documents`, { params });
  },

  /**
   * Upload a document to a workspace with optional project binding
   */
  async uploadDocument(workspaceId, file, { projectId } = {}) {
    const formData = new FormData();
    formData.append("file", file);
    if (projectId) {
      formData.append("project_id", projectId);
    }

    return apiClient(`/workspaces/${workspaceId}/documents`, {
      method: "POST",
      body: formData,
    });
  },

  /**
   * Get single document details & processing status
   */
  async getDocument(documentId) {
    return apiClient(`/documents/${documentId}`);
  },

  /**
   * Get extracted document chunks (useful for RAG transparency)
   */
  async getDocumentChunks(documentId, params = {}) {
    return apiClient(`/documents/${documentId}/chunks`, { params });
  },

  /**
   * Delete a document, chunks, and storage object
   */
  async deleteDocument(documentId) {
    return apiClient(`/documents/${documentId}`, {
      method: "DELETE",
    });
  },

  /**
   * Trigger manual re-ingestion for an existing document
   */
  async reprocessDocument(documentId) {
    return apiClient(`/documents/${documentId}/reprocess`, {
      method: "POST",
    });
  },
};
