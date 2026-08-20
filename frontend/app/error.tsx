"use client";

export default function Error({
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  return (
    <main className="flex min-h-screen items-center justify-center px-6">
      <div className="max-w-md rounded-2xl border border-rose-200 bg-rose-50 p-6 text-center">
        <h1 className="text-lg font-semibold text-rose-950">
          The workspace could not load
        </h1>
        <p className="mt-2 text-sm text-rose-800">
          Try again, or check that the backend service is running.
        </p>
        <button
          className="mt-5 rounded-lg bg-rose-700 px-4 py-2 text-sm font-medium text-white hover:bg-rose-800"
          onClick={() => reset()}
          type="button"
        >
          Try again
        </button>
      </div>
    </main>
  );
}
