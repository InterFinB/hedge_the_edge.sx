import { NextResponse } from "next/server";
import { createClient } from "@/lib/supabase/server";

export async function GET(request: Request) {
  const requestUrl = new URL(request.url);
  const code = requestUrl.searchParams.get("code");
  const tokenHash = requestUrl.searchParams.get("token_hash");
  const typeParam = requestUrl.searchParams.get("type");

  const supabase = await createClient();

  if (code) {
    const { error: exchangeError } =
      await supabase.auth.exchangeCodeForSession(code);

    if (exchangeError) {
      return NextResponse.redirect(
        new URL("/login?error=auth_callback_failed", requestUrl.origin)
      );
    }
  } else if (tokenHash && typeParam) {
    const allowedTypes = [
      "signup",
      "invite",
      "magiclink",
      "recovery",
      "email_change",
      "email",
    ] as const;

    const normalizedType = allowedTypes.includes(
      typeParam as (typeof allowedTypes)[number]
    )
      ? (typeParam as (typeof allowedTypes)[number])
      : null;

    if (!normalizedType) {
      return NextResponse.redirect(
        new URL("/login?error=invalid_token_type", requestUrl.origin)
      );
    }

    const verifyType =
      normalizedType === "magiclink" ? "email" : normalizedType;

    const { error: verifyError } = await supabase.auth.verifyOtp({
      token_hash: tokenHash,
      type: verifyType,
    });

    if (verifyError) {
      return NextResponse.redirect(
        new URL("/login?error=otp_verification_failed", requestUrl.origin)
      );
    }
  } else {
    return NextResponse.redirect(new URL("/login", requestUrl.origin));
  }

  const {
    data: { user },
    error: userError,
  } = await supabase.auth.getUser();

  if (userError || !user?.id || !user.email) {
    return NextResponse.redirect(
      new URL("/login?error=user_not_found", requestUrl.origin)
    );
  }

  const { data: existingProfile, error: profileFetchError } = await supabase
    .from("profiles")
    .select("id, status")
    .eq("id", user.id)
    .maybeSingle();

  if (profileFetchError) {
    return NextResponse.redirect(
      new URL("/login?error=profile_fetch_failed", requestUrl.origin)
    );
  }

  if (!existingProfile) {
    const { error: insertError } = await supabase.from("profiles").insert({
      id: user.id,
      email: user.email,
      status: "pending",
    });

    if (insertError) {
      return NextResponse.redirect(
        new URL("/login?error=profile_create_failed", requestUrl.origin)
      );
    }

    return NextResponse.redirect(
      new URL("/awaiting-approval", requestUrl.origin)
    );
  }

  if (existingProfile.status !== "approved") {
    return NextResponse.redirect(
      new URL("/awaiting-approval", requestUrl.origin)
    );
  }

  return NextResponse.redirect(new URL("/", requestUrl.origin));
}