"use client";

import React from "react";
import { AuthProvider } from "@/lib/authContext";
import { WorkspaceProvider } from "@/lib/workspaceContext";

export function AppProviders({ children }) {
  return (
    <AuthProvider>
      <WorkspaceProvider>{children}</WorkspaceProvider>
    </AuthProvider>
  );
}
