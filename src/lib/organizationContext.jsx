"use client";

import React, { createContext, useContext, useState, useEffect, useCallback } from "react";
import { organizationService } from "@/services/organizations";
import { useAuth } from "@/lib/authContext";

const OrganizationContext = createContext(null);

export function OrganizationProvider({ children }) {
  const { user } = useAuth();
  const [organizations, setOrganizations] = useState([]);
  const [activeOrganization, setActiveOrganizationState] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);

  const setActiveOrganization = useCallback((org) => {
    setActiveOrganizationState(org);
    if (typeof window !== "undefined") {
      if (org?.id) {
        localStorage.setItem("ai_layer_active_org_id", org.id);
      } else {
        localStorage.removeItem("ai_layer_active_org_id");
      }
    }
  }, []);

  const fetchOrganizations = useCallback(async () => {
    if (!user) {
      setOrganizations([]);
      setActiveOrganization(null);
      setIsLoading(false);
      return;
    }

    try {
      setIsLoading(true);
      const res = await organizationService.listOrganizations();
      const list = res?.organizations || [];

      setOrganizations(list);
      
      // Determine active organization
      const storedOrgId = typeof window !== "undefined" ? localStorage.getItem("ai_layer_active_org_id") : null;
      let matchedOrg = null;
      if (storedOrgId) {
        matchedOrg = list.find((o) => o.id === storedOrgId);
      }
      if (!matchedOrg && list.length > 0) {
        matchedOrg = list[0];
      }
      
      setActiveOrganization(matchedOrg);
      setError(null);
    } catch (err) {
      console.error("[OrganizationContext] Failed to load organizations:", err);
      setError(err.message);
    } finally {
      setIsLoading(false);
    }
  }, [user, setActiveOrganization]);

  useEffect(() => {
    fetchOrganizations();
  }, [fetchOrganizations]);

  const createOrganization = async ({ name, slug }) => {
    const org = await organizationService.createOrganization({ name, slug });
    await fetchOrganizations();
    setActiveOrganization(org);
    return org;
  };

  return (
    <OrganizationContext.Provider
      value={{
        organizations,
        activeOrganization,
        setActiveOrganization,
        fetchOrganizations,
        createOrganization,
        isLoading,
        error,
      }}
    >
      {children}
    </OrganizationContext.Provider>
  );
}

export function useOrganization() {
  const context = useContext(OrganizationContext);
  if (!context) {
    throw new Error("useOrganization must be used within an OrganizationProvider");
  }
  return context;
}
