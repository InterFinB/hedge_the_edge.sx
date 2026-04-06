"use client";

import { FormEvent, useEffect, useMemo, useState } from "react";
import { useSearchParams } from "next/navigation";
import { createClient } from "@/lib/supabase/client";

export default function AccessApprovedClient() {
  const supabase = useMemo(() => createClient(), []);
  const searchParams = useSearchParams();

  const [email, setEmail] = useState("");
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const initialEmail = searchParams.get("email") ?? "";
    setEmail(initialEmail);
  }, [searchParams]);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setLoading(true);
    setMessage(null);
    setError(null);

    const trimmedEmail = email.trim();

    const { error } = await supabase.auth.signInWithOtp({
      email: trimmedEmail,
      options: {
        emailRedirectTo: `${window.location.origin}/auth/callback`,
      },
    });

    if (error) {
      setError(error.message);
      setLoading(false);
      return;
    }

    setMessage(
      "Your secure sign-in link has been sent. Open it from your inbox to enter Hedge The Edge."
    );
    setLoading(false);
  }

  return (
    <main className="min-h-screen bg-neutral-50 text-neutral-950">
      <div className="mx-auto flex min-h-screen max-w-5xl items-center px-6 py-16">
        <div className="grid w-full gap-10 md:grid-cols-[1.1fr_0.9fr]">
          <section className="space-y-6">
            <div className="inline-flex items-center rounded-full border border-neutral-200 bg-white px-3 py-1 text-xs font-medium uppercase tracking-[0.24em] text-neutral-600">
              Access active
            </div>

            <div className="space-y-4">
              <h1 className="text-4xl font-semibold tracking-tight sm:text-5xl">
                Your access is ready
              </h1>
              <p className="max-w-xl text-base leading-7 text-neutral-600 sm:text-lg">
                You already have access to Hedge The Edge. Enter your approved
                email address below and we’ll send your secure sign-in link.
              </p>
            </div>

            <div className="rounded-3xl border border-neutral-200 bg-white p-5 shadow-sm">
              <p className="text-sm leading-6 text-neutral-700">
                This page is only for approved users. After you submit your email,
                use the sign-in link from your inbox and you’ll be taken straight
                into the app.
              </p>
            </div>
          </section>

          <section className="rounded-3xl border border-neutral-200 bg-white p-6 shadow-sm sm:p-8">
            <div className="space-y-2">
              <h2 className="text-2xl font-semibold tracking-tight">
                Enter the app
              </h2>
              <p className="text-sm leading-6 text-neutral-600">
                Use the same email address that was approved.
              </p>
            </div>

            <form className="mt-6 space-y-4" onSubmit={handleSubmit}>
              <div className="space-y-2">
                <label
                  htmlFor="email"
                  className="text-sm font-medium text-neutral-800"
                >
                  Approved email address
                </label>
                <input
                  id="email"
                  type="email"
                  value={email}
                  onChange={(event) => setEmail(event.target.value)}
                  placeholder="you@example.com"
                  required
                  className="w-full rounded-2xl border border-neutral-300 bg-white px-4 py-3 text-sm outline-none transition focus:border-neutral-500"
                />
              </div>

              <button
                type="submit"
                disabled={loading}
                className="w-full rounded-2xl bg-neutral-950 px-4 py-3 text-sm font-medium text-white transition hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-60"
              >
                {loading ? "Sending sign-in link..." : "Send my sign-in link"}
              </button>
            </form>

            {message ? (
              <p className="mt-4 rounded-2xl border border-green-200 bg-green-50 px-4 py-3 text-sm leading-6 text-green-800">
                {message}
              </p>
            ) : null}

            {error ? (
              <p className="mt-4 rounded-2xl border border-red-200 bg-red-50 px-4 py-3 text-sm leading-6 text-red-700">
                {error}
              </p>
            ) : null}
          </section>
        </div>
      </div>
    </main>
  );
}