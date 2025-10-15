import { useEffect, useState } from "react";

function App() {
  const [birds, setBirds] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  console.log("BIRDS:", birds)


  async function loadBirds() {
    try {
      setLoading(true);
      setError("");
      const res = await fetch("/api/birds", { credentials: "include" });
      if (!res.ok) {
        const text = await res.text();
        throw new Error(`Request failed (${res.status}): ${text || res.statusText}`);
      }
      const data = await res.json();
      setBirds(data);
    } catch (err) {
      setError(err.message || "Failed to fetch birds.");
      setBirds(null);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadBirds();
  }, []);

  const renderBirds = () => {
    if (!birds) return null;

    // If it's an array of strings
    if (Array.isArray(birds) && birds.every((b) => typeof b === "string")) {
      return (
        <ul className="list-disc pl-6">
          {birds.map((b, i) => (
            <li key={i}>{b}</li>
          ))}
        </ul>
      );
    }

    // If it's an array of objects with a common `name` field
    if (
      Array.isArray(birds) &&
      birds.length > 0 &&
      birds.every((b) => b && typeof b === "object" && ("name" in b || "species" in b))
    ) {
      return (
        <ul className="divide-y divide-gray-200 rounded-md border">
          {birds.map((b, i) => (
            <li key={i} className="p-3">
              <div className="font-medium">{b.name || b.species || `Bird #${i + 1}`}</div>
              <div className="text-sm text-gray-600">
                {Object.entries(b)
                  .filter(([k]) => k !== "name" && k !== "species")
                  .map(([k, v]) => (
                    <span key={k} className="mr-3">
                      <span className="font-mono text-xs uppercase tracking-wide text-gray-500">{k}:</span> {String(v)}
                    </span>
                  ))}
              </div>
            </li>
          ))}
        </ul>
      );
    }

    // Fallback: pretty-print whatever the API returned
    return (
      <pre className="overflow-auto rounded-md border bg-gray-50 p-3 text-sm">
        {JSON.stringify(birds, null, 2)}
      </pre>
    );
  };

  return (
    <div className="mx-auto max-w-2xl p-6">
      <div className="mb-4 flex items-center justify-between">
        <h1 className="text-2xl font-semibold">Birds</h1>
        <button
          onClick={loadBirds}
          className="rounded-md border px-3 py-1 text-sm hover:bg-gray-50 active:scale-[.99]"
        >
          Refresh
        </button>
      </div>

      {loading && <div className="text-gray-600">Loading…</div>}
      {error && (
        <div className="mb-3 rounded-md border border-red-200 bg-red-50 p-3 text-sm text-red-700">
          {error}
        </div>
      )}

      {!loading && !error && renderBirds()}

      <footer className="mt-6 text-xs text-gray-500">
        Fetching from <code className="rounded bg-gray-100 px-1">/birds</code>
      </footer>
    </div>
  );
}

export default App;
