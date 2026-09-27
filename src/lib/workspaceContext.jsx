"use client";

import React, { createContext, useContext, useState, useEffect } from "react";
import { workspaceService } from "@/services/workspaces";

const WorkspaceContext = createContext(null);

export function WorkspaceProvider({ children }) {
  const [workspaces, setWorkspaces] = useState([]);
  const [activeWorkspace, setActiveWorkspace] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchWorkspaces = async () => {
    try {
      setIsLoading(true);
      const res = await workspaceService.listWorkspaces();
      let list = res?.workspaces || [];
      
      // Auto-create default development workspace if empty
      if (list.length === 0) {
        try {
          const created = await workspaceService.createWorkspace({
            name: "Default Workspace",
            slug: "default-workspace",
          });
          list = [created];
        } catch (createErr) {
          console.warn("[WorkspaceProvider] Default creation skipped:", createErr);
        }
      }

      setWorkspaces(list);
      setActiveWorkspace((prev) => {
        if (prev && list.find((w) => w.id === prev.id)) {
          return list.find((w) => w.id === prev.id);
        }
        return list[0] || null;
      });
      setError(null);
    } catch (err) {
      console.error("[WorkspaceContext] Failed to load workspaces:", err);
      setError(err.message);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchWorkspaces();
  }, []);

  const createWorkspace = async ({ name, slug }) => {
    const ws = await workspaceService.createWorkspace({ name, slug });
    await fetchWorkspaces();
    setActiveWorkspace(ws);
    return ws;
  };

  return (
    <WorkspaceContext.Provider
      value={{
        workspaces,
        activeWorkspace,
        setActiveWorkspace,
        fetchWorkspaces,
        createWorkspace,
        isLoading,
        error,
      }}
    >
      {children}
    </WorkspaceContext.Provider>
  );
}

export function useWorkspace() {
  const context = useContext(WorkspaceContext);
  if (!context) {
    throw new Error("useWorkspace must be used within a WorkspaceProvider");
  }
  return context;
}
