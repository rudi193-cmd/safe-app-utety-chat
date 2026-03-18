// AUTH PROVIDER: supabase (Option A)
// To swap to Willow OAuth (Option C), replace signInWith* functions to redirect
// to http://localhost:8420/api/auth/google?redirect={origin}/auth/callback
// and update getUser()/getSession() to call /api/auth/session instead.
// The rest of the codebase uses only this module — one-file swap.

import { supabase } from './supabase';

export async function signInWithGoogle() {
  return supabase.auth.signInWithOAuth({
    provider: 'google',
    options: {
      redirectTo: `${window.location.origin}/auth/callback`,
    },
  });
}

export async function signInWithGitHub() {
  return supabase.auth.signInWithOAuth({
    provider: 'github',
    options: {
      redirectTo: `${window.location.origin}/auth/callback`,
    },
  });
}

export async function signInWithEmail(email: string) {
  return supabase.auth.signInWithOtp({
    email,
    options: {
      emailRedirectTo: `${window.location.origin}/auth/callback`,
    },
  });
}

export async function getUser() {
  return (await supabase.auth.getUser()).data.user;
}

export async function getSession() {
  return (await supabase.auth.getSession()).data.session;
}

export async function signOut() {
  return supabase.auth.signOut();
}
