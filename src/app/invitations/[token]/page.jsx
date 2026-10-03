"use client";

import React, { useState, useEffect } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import {
  Building2,
  CheckCircle2,
  AlertTriangle,
  Loader2,
  ArrowRight,
  ShieldCheck,
} from "lucide-react";
import { organizationService } from "@/services/organizations";
import { useAuth } from "@/lib/authContext";

export default function AcceptInvitationPage() {
  const { token } = useParams();
  const router = useRouter();
  const { user, loading: authLoading } = useAuth();

  const [accepting, setAccepting] = useState(false);
  const [success, setSuccess] = useState(false);
  const [error, setError] = useState(null);

  const handleAccept = async () => {
    try {
      setAccepting(true);
      setError(null);
      await organizationService.acceptInvitation(token);
      setSuccess(true);
      setTimeout(() => {
        router.push("/app/organizations");
      }, 2000);
    } catch (err) {
      setError(err.message || "Failed to accept invitation");
    } finally {
      setAccepting(false);
    }
  };

  if (authLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-[#07090e] text-slate-100">
        <Loader2 className="w-8 h-8 animate-spin text-indigo-400" />
      </div>
    );
  }

  if (!user) {
    return (
      <div className="min-h-screen flex items-center justify-center p-4 bg-[#07090e] text-slate-100">
        <div className="w-full max-w-md p-8 rounded-2xl bg-slate-900 border border-slate-800 text-center space-y-4">
          <Building2 className="w-12 h-12 text-indigo-400 mx-auto" />
          <h1 className="text-xl font-bold text-white">Sign In Required</h1>
          <p className="text-xs text-slate-400">
            Please log in or create an account to accept your organization invitation.
          </p>
          <Link
            href={`/login?redirect=/invitations/${token}`}
            className="inline-flex items-center justify-center w-full px-4 py-2.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold shadow-md shadow-indigo-900/30 transition-all"
          >
            Sign In to Accept
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex items-center justify-center p-4 bg-[#07090e] text-slate-100">
      <div className="w-full max-w-md p-8 rounded-2xl bg-slate-900 border border-slate-800 shadow-2xl text-center space-y-5">
        <div className="w-14 h-14 rounded-2xl bg-indigo-500/10 border border-indigo-500/20 flex items-center justify-center text-indigo-400 mx-auto">
          <Building2 className="w-7 h-7" />
        </div>

        <div>
          <h1 className="text-xl font-bold text-white">Organization Invitation</h1>
          <p className="text-xs text-slate-400 mt-1">
            You have been invited to collaborate in a workspace organization on the AI Work Layer.
          </p>
        </div>

        {error && (
          <div className="p-3 rounded-lg bg-rose-500/10 border border-rose-500/20 text-rose-400 text-xs flex items-center gap-2 text-left">
            <AlertTriangle className="w-4 h-4 shrink-0" />
            <span>{error}</span>
          </div>
        )}

        {success ? (
          <div className="p-4 rounded-xl bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-xs flex flex-col items-center gap-2">
            <CheckCircle2 className="w-6 h-6 text-emerald-400" />
            <span className="font-semibold text-white">Invitation Accepted!</span>
            <p className="text-slate-400">Redirecting to your organizations dashboard...</p>
          </div>
        ) : (
          <div className="pt-2 space-y-3">
            <button
              onClick={handleAccept}
              disabled={accepting}
              className="w-full inline-flex items-center justify-center gap-2 px-4 py-2.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold shadow-md shadow-indigo-900/30 transition-all cursor-pointer disabled:opacity-50"
            >
              {accepting ? (
                <Loader2 className="w-4 h-4 animate-spin" />
              ) : (
                <ShieldCheck className="w-4 h-4" />
              )}
              <span>{accepting ? "Validating & Joining..." : "Accept Invitation & Join"}</span>
            </button>

            <Link
              href="/app"
              className="block text-xs text-slate-500 hover:text-slate-400"
            >
              Decline and return to app
            </Link>
          </div>
        )}
      </div>
    </div>
  );
}
