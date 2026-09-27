import { createClient } from "@supabase/supabase-js";

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL;
const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY;

/**
 * Creates the Supabase client for authentication and session management.
 * If credentials are not configured (e.g. local offline dev), provides a safe fallback.
 */
let supabase = null;

if (supabaseUrl && supabaseAnonKey) {
  supabase = createClient(supabaseUrl, supabaseAnonKey, {
    auth: {
      persistSession: true,
      autoRefreshToken: true,
      detectSessionInUrl: true,
    },
  });
} else {
  // In development without configured Supabase credentials, provide a mock auth client for graceful local UI development
  if (typeof window !== "undefined") {
    console.warn(
      "[Supabase] NEXT_PUBLIC_SUPABASE_URL or NEXT_PUBLIC_SUPABASE_ANON_KEY is not configured. Using local development auth mode."
    );
  }

  // Local storage mock auth provider for offline development
  const getStoredUser = () => {
    if (typeof window === "undefined") return null;
    try {
      const data = localStorage.getItem("ai_work_layer_dev_user");
      return data ? JSON.parse(data) : null;
    } catch {
      return null;
    }
  };

  const setStoredUser = (user, token) => {
    if (typeof window === "undefined") return;
    try {
      if (user) {
        localStorage.setItem("ai_work_layer_dev_user", JSON.stringify({ user, token }));
      } else {
        localStorage.removeItem("ai_work_layer_dev_user");
      }
    } catch {}
  };

  supabase = {
    auth: {
      async signUp({ email, password }) {
        const userId = `dev-user-${btoa(email).replace(/[^a-zA-Z0-9]/g, "").slice(0, 16) || "default"}`;
        const user = { id: userId, email, user_metadata: { email } };
        // Create a valid JWT token signed with DEV secret format or base64 structure
        // Header: {"alg":"HS256","typ":"JWT"} -> eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9
        const header = btoa(JSON.stringify({ alg: "HS256", typ: "JWT" }));
        const payload = btoa(
          JSON.stringify({
            sub: userId,
            email,
            aud: "authenticated",
            role: "authenticated",
            exp: Math.floor(Date.now() / 1000) + 86400,
          })
        );
        const token = `${header}.${payload}.dev_local_signature`;
        setStoredUser(user, token);
        return { data: { user, session: { access_token: token, user } }, error: null };
      },
      async signInWithPassword({ email, password }) {
        if (!email || !password) {
          return { data: { user: null, session: null }, error: { message: "Email and password required." } };
        }
        const userId = `dev-user-${btoa(email).replace(/[^a-zA-Z0-9]/g, "").slice(0, 16) || "default"}`;
        const user = { id: userId, email, user_metadata: { email } };
        const header = btoa(JSON.stringify({ alg: "HS256", typ: "JWT" }));
        const payload = btoa(
          JSON.stringify({
            sub: userId,
            email,
            aud: "authenticated",
            role: "authenticated",
            exp: Math.floor(Date.now() / 1000) + 86400,
          })
        );
        const token = `${header}.${payload}.dev_local_signature`;
        setStoredUser(user, token);
        return { data: { user, session: { access_token: token, user } }, error: null };
      },
      async signOut() {
        setStoredUser(null, null);
        return { error: null };
      },
      async getSession() {
        const stored = getStoredUser();
        if (stored?.user && stored?.token) {
          return {
            data: {
              session: {
                access_token: stored.token,
                user: stored.user,
              },
            },
            error: null,
          };
        }
        return { data: { session: null }, error: null };
      },
      async getUser() {
        const stored = getStoredUser();
        return { data: { user: stored?.user || null }, error: null };
      },
      onAuthStateChange(callback) {
        // Return unsubscribe function
        return {
          data: {
            subscription: {
              unsubscribe: () => {},
            },
          },
        };
      },
    },
  };
}

export { supabase };
