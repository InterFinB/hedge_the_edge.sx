import { NextResponse } from "next/server";
import { createClient } from "@/lib/supabase/server";

export async function GET(request: Request) {
  const requestUrl = new URL(request.url);
  const code = requestUrl.searchParams.get("code");

  if (!code) {
    return NextResponse.redirect(new URL("/login", requestUrl.origin));
  }

  const supabase = await createClient();

  const { error: exchangeError } = await supabase.auth.exchangeCodeForSession(code);

  if (exchangeError) {
    return NextResponse.redirect(new URL("/login?error=auth_callback_failed", requestUrl.origin));
  }

  const {
    data: { user },
    error: userError,
  } = await supabase.auth.getUser();

  if (userError || !user?.id || !user.email) {
    return NextResponse.redirect(new URL("/login?error=user_not_found", requestUrl.origin));
  }

  const { data: existingProfile, error: profileFetchError } = await supabase
    .from("profiles")
    .select("id, status")
    .eq("id", user.id)
    .maybeSingle();

  if (profileFetchError) {
    return NextResponse.redirect(new URL("/login?error=profile_fetch_failed", requestUrl.origin));
  }

  if (!existingProfile) {
    const { error: insertError } = await supabase.from("profiles").insert({
      id: user.id,
      email: user.email,
      status: "pending",
    });

    if (insertError) {
      return NextResponse.redirect(new URL("/login?error=profile_create_failed", requestUrl.origin));
    }

    return NextResponse.redirect(new URL("/awaiting-approval", requestUrl.origin));
  }

  if (existingProfile.status !== "approved") {
    return NextResponse.redirect(new URL("/awaiting-approval", requestUrl.origin));
  }

  return NextResponse.redirect(new URL("/", requestUrl.origin));
}