import { NextResponse } from "next/server";
import { Resend } from "resend";

const resend = new Resend(process.env.RESEND_API_KEY);

type WebhookRecord = {
  id?: string;
  email?: string | null;
  status?: string | null;
  approved_at?: string | null;
};

type WebhookPayload = {
  type?: string;
  table?: string;
  schema?: string;
  record?: WebhookRecord | null;
  old_record?: WebhookRecord | null;
};

export async function POST(request: Request) {
  const secret = request.headers.get("x-webhook-secret");

  if (
    !process.env.APPROVAL_WEBHOOK_SECRET ||
    secret !== process.env.APPROVAL_WEBHOOK_SECRET
  ) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  }

  if (!process.env.RESEND_API_KEY) {
    return NextResponse.json(
      { error: "Missing RESEND_API_KEY" },
      { status: 500 }
    );
  }

  if (!process.env.APPROVAL_EMAIL_FROM) {
    return NextResponse.json(
      { error: "Missing APPROVAL_EMAIL_FROM" },
      { status: 500 }
    );
  }

  if (!process.env.APP_BASE_URL) {
    return NextResponse.json(
      { error: "Missing APP_BASE_URL" },
      { status: 500 }
    );
  }

  let payload: WebhookPayload;

  try {
    payload = (await request.json()) as WebhookPayload;
  } catch {
    return NextResponse.json({ error: "Invalid JSON body" }, { status: 400 });
  }

  const record = payload.record;
  const oldRecord = payload.old_record;

  if (!record?.email) {
    return NextResponse.json({
      skipped: true,
      reason: "No email on record",
    });
  }

  const newStatus = record.status ?? null;
  const oldStatus = oldRecord?.status ?? null;
  const justApproved = newStatus === "approved" && oldStatus !== "approved";

  if (!justApproved) {
    return NextResponse.json({
      skipped: true,
      reason: "Status did not change to approved",
    });
  }

  const approvedAccessUrl = `${process.env.APP_BASE_URL}/access-approved?email=${encodeURIComponent(
    record.email
  )}`;

  const { data, error } = await resend.emails.send({
    from: process.env.APPROVAL_EMAIL_FROM,
    to: [record.email],
    subject: "Your Hedge The Edge access has been approved",
    html: `
      <div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Arial, sans-serif; background-color: #f9fafb; padding: 40px 20px;">
        <div style="max-width: 520px; margin: 0 auto; background: white; border-radius: 16px; padding: 32px; box-shadow: 0 10px 25px rgba(0,0,0,0.05);">
          <p style="font-size: 12px; letter-spacing: 0.12em; text-transform: uppercase; color: #6b7280; margin-bottom: 8px;">
            Access approved
          </p>

          <h2 style="font-size: 24px; margin-bottom: 16px; color: #111827;">
            Your access has been approved
          </h2>

          <p style="font-size: 15px; color: #374151; line-height: 1.6;">
            Your access to <strong>Hedge The Edge</strong> is now active.
          </p>

          <p style="font-size: 15px; color: #374151; line-height: 1.6; margin-top: 12px;">
            Click below to continue to your sign-in page and enter the app.
          </p>

          <div style="margin: 24px 0;">
            <a
              href="${approvedAccessUrl}"
              style="display: inline-block; background: #111827; color: white; text-decoration: none; padding: 12px 20px; border-radius: 10px; font-size: 14px;"
            >
              Continue to sign in
            </a>
          </div>

          <p style="font-size: 13px; color: #6b7280;">
            If the button doesn’t work, use this link:
          </p>

          <p style="font-size: 13px; word-break: break-all;">
            <a href="${approvedAccessUrl}" style="color: #2563eb;">${approvedAccessUrl}</a>
          </p>

          <hr style="margin: 24px 0; border: none; border-top: 1px solid #e5e7eb;" />

          <p style="font-size: 12px; color: #9ca3af;">
            Hedge The Edge · Portfolio Intelligence
          </p>
        </div>
      </div>
    `,
  });

  if (error) {
    return NextResponse.json({ error }, { status: 500 });
  }

  return NextResponse.json({ ok: true, data });
}