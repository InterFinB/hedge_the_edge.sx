"use client";

import { useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import { createClient } from "@/lib/supabase/client";

export default function SignOutButton() {
  const supabase = useMemo(() => createClient(), []);
  const router = useRouter();
  const [loading, setLoading] = useState(false);

  async function handleSignOut() {
    setLoading(true);

    let email = "";

    try {
      const {
        data: { user },
      } = await supabase.auth.getUser();

      email = user?.email?.trim().toLowerCase() ?? "";

      if (email) {
        localStorage.setItem("hte_last_approved_email", email);
      }

      await supabase.auth.signOut();
    } finally {
      const destination = email
        ? `/access-approved?email=${encodeURIComponent(email)}`
        : "/access-approved";

      router.push(destination);
      router.refresh();
      setLoading(false);
    }
  }

  return (
    <button
      onClick={handleSignOut}
      disabled={loading}
      className="rounded-2xl border border-neutral-300 bg-white px-4 py-2 text-sm font-medium text-neutral-800 transition hover:bg-neutral-50 disabled:opacity-60"
    >
      {loading ? "Signing out..." : "Sign out"}
    </button>
  );
}