import { NextResponse, type NextRequest } from "next/server";
import { createServerClient } from "@supabase/ssr";

export async function proxy(request: NextRequest) {
  const response = NextResponse.next();

  const supabase = createServerClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY!,
    {
      cookies: {
        getAll() {
          return request.cookies.getAll();
        },
        setAll(cookiesToSet) {
          cookiesToSet.forEach(({ name, value, options }) => {
            response.cookies.set(name, value, options);
          });
        },
      },
    }
  );

  const pathname = request.nextUrl.pathname;

  const isPublicPath =
    pathname === "/login" ||
    pathname === "/awaiting-approval" ||
    pathname === "/access-approved" ||
    pathname.startsWith("/auth/callback") ||
    pathname.startsWith("/api/send-approval-email") ||
    pathname.startsWith("/api/direct-approved-login");

  if (isPublicPath) {
    return response;
  }

  const {
    data: { user },
  } = await supabase.auth.getUser();

  if (!user) {
    const loginUrl = request.nextUrl.clone();
    loginUrl.pathname = "/login";
    loginUrl.search = "";
    return NextResponse.redirect(loginUrl);
  }

  const { data: profile, error } = await supabase
    .from("profiles")
    .select("status")
    .eq("id", user.id)
    .maybeSingle();

  if (error || !profile) {
    const awaitingUrl = request.nextUrl.clone();
    awaitingUrl.pathname = "/awaiting-approval";
    awaitingUrl.search = "";
    return NextResponse.redirect(awaitingUrl);
  }

  if (profile.status !== "approved") {
    const awaitingUrl = request.nextUrl.clone();
    awaitingUrl.pathname = "/awaiting-approval";
    awaitingUrl.search = "";
    return NextResponse.redirect(awaitingUrl);
  }

  if (
    pathname === "/login" ||
    pathname === "/awaiting-approval" ||
    pathname.startsWith("/auth/callback")
  ) {
    const homeUrl = request.nextUrl.clone();
    homeUrl.pathname = "/";
    homeUrl.search = "";
    return NextResponse.redirect(homeUrl);
  }

  return response;
}

export const config = {
  matcher: [
    "/((?!_next/static|_next/image|favicon.ico|.*\\.(?:svg|png|jpg|jpeg|gif|webp)$).*)",
  ],
};