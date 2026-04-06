import { Suspense } from "react";
import AccessApprovedClient from "./AccessApprovedClient";

export default function AccessApprovedPage() {
  return (
    <Suspense
      fallback={
        <main className="min-h-screen bg-neutral-50 text-neutral-950">
          <div className="mx-auto flex min-h-screen max-w-5xl items-center px-6 py-16">
            <div className="w-full rounded-3xl border border-neutral-200 bg-white p-8 shadow-sm">
              <p className="text-sm text-neutral-600">Loading access page...</p>
            </div>
          </div>
        </main>
      }
    >
      <AccessApprovedClient />
    </Suspense>
  );
}