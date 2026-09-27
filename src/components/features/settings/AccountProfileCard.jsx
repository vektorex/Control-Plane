"use client";

import React from "react";
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { useAuth } from "@/lib/authContext";
import { useWorkspace } from "@/lib/workspaceContext";
import { User, Mail, Shield, Key, LogOut, CheckCircle2 } from "lucide-react";

export function AccountProfileCard() {
  const { user, signOut } = useAuth();
  const { activeWorkspace } = useWorkspace();

  const userEmail = user?.email || "developer@worklayer.internal";
  const authUserId = user?.id || user?.sub || "local-dev-user";

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>Authenticated Profile & Security</CardTitle>
          <CardDescription>
            Multi-tenant identity verified via Supabase Auth and independent backend JWT signature validation.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="p-4 rounded-xl bg-slate-950/60 border border-slate-800 space-y-1.5">
              <div className="flex items-center gap-2 text-xs font-semibold text-slate-400 uppercase tracking-wider">
                <Mail className="w-3.5 h-3.5 text-indigo-400" />
                <span>Account Email</span>
              </div>
              <div className="text-sm font-medium text-slate-200">{userEmail}</div>
              <div className="text-[11px] text-emerald-400 flex items-center gap-1">
                <CheckCircle2 className="w-3 h-3" />
                <span>Verified Identity</span>
              </div>
            </div>

            <div className="p-4 rounded-xl bg-slate-950/60 border border-slate-800 space-y-1.5">
              <div className="flex items-center gap-2 text-xs font-semibold text-slate-400 uppercase tracking-wider">
                <Shield className="w-3.5 h-3.5 text-indigo-400" />
                <span>Active Workspace Scope</span>
              </div>
              <div className="text-sm font-medium text-slate-200">
                {activeWorkspace?.name || "Default Workspace"}
              </div>
              <div className="text-[11px] text-slate-400 font-mono">
                slug: {activeWorkspace?.slug || "default"}
              </div>
            </div>
          </div>

          <div className="p-4 rounded-xl bg-slate-950/40 border border-slate-800/80 space-y-2">
            <div className="flex items-center gap-2 text-xs font-semibold text-slate-400 uppercase tracking-wider">
              <Key className="w-3.5 h-3.5 text-indigo-400" />
              <span>Identity Provider Subject ID</span>
            </div>
            <div className="text-xs font-mono text-slate-300 break-all bg-slate-900/80 p-2.5 rounded-lg border border-slate-800">
              {authUserId}
            </div>
          </div>
        </CardContent>
        <CardFooter className="flex items-center justify-between">
          <span className="text-xs text-slate-400">
            Session is securely persisted and automatically refreshed.
          </span>
          <Button
            type="button"
            variant="danger"
            size="sm"
            icon={LogOut}
            onClick={() => signOut()}
          >
            Sign Out of Account
          </Button>
        </CardFooter>
      </Card>
    </div>
  );
}
