"use client";

import React, { createContext, useContext, useEffect, useState, useCallback } from "react";
import { useRouter } from "next/navigation";
import { supabase } from "./supabaseClient";

const AuthContext = createContext({
  user: null,
  session: null,
  loading: true,
  error: null,
  signUp: async () => {},
  signIn: async () => {},
  signOut: async () => {},
  getToken: async () => null,
});

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [session, setSession] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const router = useRouter();

  // Initialize and check active session
  useEffect(() => {
    let mounted = true;

    async function initializeAuth() {
      try {
        const { data, error: sessionError } = await supabase.auth.getSession();
        if (sessionError) {
          throw sessionError;
        }

        if (mounted) {
          setSession(data?.session || null);
          setUser(data?.session?.user || null);
        }
      } catch (err) {
        console.error("[AuthProvider] Session resolution error:", err);
        if (mounted) {
          setError(err.message || "Failed to resolve session");
        }
      } finally {
        if (mounted) {
          setLoading(false);
        }
      }
    }

    initializeAuth();

    // Listen for auth state changes
    const { data: authListener } = supabase.auth.onAuthStateChange(
      (event, currentSession) => {
        if (!mounted) return;
        setSession(currentSession);
        setUser(currentSession?.user || null);
        setLoading(false);

        if (event === "SIGNED_OUT") {
          router.push("/login");
        }
      }
    );

    return () => {
      mounted = false;
      if (authListener?.subscription?.unsubscribe) {
        authListener.subscription.unsubscribe();
      }
    };
  }, [router]);

  const signUp = useCallback(async (email, password) => {
    setError(null);
    try {
      const { data, error: signUpError } = await supabase.auth.signUp({
        email,
        password,
      });
      if (signUpError) throw signUpError;
      setUser(data.user);
      setSession(data.session);
      return { data, error: null };
    } catch (err) {
      setError(err.message);
      return { data: null, error: err };
    }
  }, []);

  const signIn = useCallback(async (email, password) => {
    setError(null);
    try {
      const { data, error: signInError } = await supabase.auth.signInWithPassword({
        email,
        password,
      });
      if (signInError) throw signInError;
      setUser(data.user);
      setSession(data.session);
      return { data, error: null };
    } catch (err) {
      setError(err.message);
      return { data: null, error: err };
    }
  }, []);

  const signOut = useCallback(async () => {
    setError(null);
    try {
      await supabase.auth.signOut();
      setUser(null);
      setSession(null);
      router.push("/login");
    } catch (err) {
      console.error("[AuthProvider] Sign out error:", err);
    }
  }, [router]);

  const getToken = useCallback(async () => {
    if (session?.access_token) {
      return session.access_token;
    }
    const { data } = await supabase.auth.getSession();
    return data?.session?.access_token || null;
  }, [session]);

  const value = {
    user,
    session,
    loading,
    error,
    signUp,
    signIn,
    signOut,
    getToken,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
}
