import { NextResponse } from "next/server";
import { createClient } from "@supabase/supabase-js";

const supabaseAdmin = createClient(
  process.env.NEXT_PUBLIC_SUPABASE_URL!,
  process.env.SUPABASE_SERVICE_ROLE_KEY!
);

export async function POST(request: Request) {
  if (!process.env.APP_BASE_URL) {
    return NextResponse.json(
      { error: "Missing APP_BASE_URL" },
      { status: 500 }
    );
  }

  if (!process.env.NEXT_PUBLIC_SUPABASE_URL) {
    return NextResponse.json(
      { error: "Missing NEXT_PUBLIC_SUPABASE_URL" },
      { status: 500 }
    );
  }

  if (!process.env.SUPABASE_SERVICE_ROLE_KEY) {
    return NextResponse.json(
      { error: "Missing SUPABASE_SERVICE_ROLE_KEY" },
      { status: 500 }
    );
  }

  let body: { email?: string };

  try {
    body = (await request.json()) as { email?: string };
  } catch {
    return NextResponse.json({ error: "Invalid JSON body" }, { status: 400 });
  }

  const email = body.email?.trim().toLowerCase();

  if (!email) {
    return NextResponse.json(
      { error: "Email is required" },
      { status: 400 }
    );
  }

  const { data: profile, error: profileError } = await supabaseAdmin
    .from("profiles")
    .select("email, status")
    .eq("email", email)
    .maybeSingle();

  if (profileError) {
    return NextResponse.json(
      { error: "Failed to check approval status" },
      { status: 500 }
    );
  }

  if (!profile || profile.status !== "approved") {
    return NextResponse.json(
      { error: "This email is not approved yet." },
      { status: 403 }
    );
  }

  const { data, error } = await supabaseAdmin.auth.admin.generateLink({
    type: "magiclink",
    email,
    options: {
      redirectTo: `${process.env.APP_BASE_URL}/`,
    },
  });

  const tokenHash = data?.properties?.hashed_token;

  if (error || !tokenHash) {
    return NextResponse.json(
      { error: "Failed to generate login link" },
      { status: 500 }
    );
  }

  const callbackUrl =
    `${process.env.APP_BASE_URL}/auth/callback` +
    `?token_hash=${encodeURIComponent(tokenHash)}` +
    `&type=email`;

  return NextResponse.json({ redirectTo: callbackUrl });
}