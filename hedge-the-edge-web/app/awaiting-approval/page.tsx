import Link from "next/link";

export default function AwaitingApprovalPage() {
  return (
    <main className="min-h-screen bg-neutral-50 text-neutral-950">
      <div className="mx-auto flex min-h-screen max-w-3xl items-center px-6 py-16">
        <div className="w-full rounded-3xl border border-neutral-200 bg-white p-8 shadow-sm sm:p-10">
          <div className="space-y-4">
            <div className="inline-flex items-center rounded-full border border-neutral-200 bg-neutral-50 px-3 py-1 text-xs font-medium uppercase tracking-[0.24em] text-neutral-600">
              Access Pending
            </div>

            <h1 className="text-3xl font-semibold tracking-tight sm:text-4xl">
              Your access request is awaiting approval
            </h1>

            <p className="max-w-2xl text-base leading-7 text-neutral-600">
              Your email has been registered successfully, but your account is not
              approved yet. Once approved, you will be able to access Hedge The Edge.
            </p>

            <p className="max-w-2xl text-base leading-7 text-neutral-600">
              After approval, return to the login page and use your magic link again.
            </p>
          </div>

          <div className="mt-8">
            <Link
              href="/login"
              className="inline-flex rounded-2xl bg-neutral-950 px-4 py-3 text-sm font-medium text-white transition hover:opacity-90"
            >
              Back to login
            </Link>
          </div>
        </div>
      </div>
    </main>
  );
}