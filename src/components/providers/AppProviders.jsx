"use client";

import React from "react";
import { AuthProvider } from "@/lib/authContext";
import { OrganizationProvider } from "@/lib/organizationContext";
import { WorkspaceProvider } from "@/lib/workspaceContext";

export function AppProviders({ children }) {
  return (
    <AuthProvider>
      <OrganizationProvider>
        <WorkspaceProvider>{children}</WorkspaceProvider>
      </OrganizationProvider>
    </AuthProvider>
  );
}
