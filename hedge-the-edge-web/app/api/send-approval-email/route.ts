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

  if (!process.env.APPROVAL_WEBHOOK_SECRET || secret !== process.env.APPROVAL_WEBHOOK_SECRET) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  }

  if (!process.env.RESEND_API_KEY) {
    return NextResponse.json({ error: "Missing RESEND_API_KEY" }, { status: 500 });
  }

  if (!process.env.APPROVAL_EMAIL_FROM) {
    return NextResponse.json({ error: "Missing APPROVAL_EMAIL_FROM" }, { status: 500 });
  }

  if (!process.env.APP_BASE_URL) {
    return NextResponse.json({ error: "Missing APP_BASE_URL" }, { status: 500 });
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
    return NextResponse.json({ skipped: true, reason: "No email on record" });
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

  const loginUrl = `${process.env.APP_BASE_URL}/login`;

  const { data, error } = await resend.emails.send({
    from: process.env.APPROVAL_EMAIL_FROM,
    to: [record.email],
    subject: "Your Hedge The Edge access has been approved",
    html: `
      <div style="font-family: Arial, sans-serif; line-height: 1.6; color: #111827;">
        <h2 style="margin-bottom: 16px;">Your access has been approved</h2>
        <p>Hi,</p>
        <p>Your access to <strong>Hedge The Edge</strong> has now been approved.</p>
        <p>You can sign in here:</p>
        <p><a href="${loginUrl}">${loginUrl}</a></p>
        <p>Enter your email address and use the magic link sent to your inbox to access the app.</p>
        <p>Best,<br/>Hedge The Edge</p>
      </div>
    `,
  });

  if (error) {
    return NextResponse.json({ error }, { status: 500 });
  }

  return NextResponse.json({ ok: true, data });
}