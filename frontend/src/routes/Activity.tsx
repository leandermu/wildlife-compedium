import { useEffect, useState } from "react";
import { api } from "../api";
import type { Activity } from "../types";
import { ActivityList } from "../components/ActivityList";
import { Empty, Spinner } from "../components/ui";

const PAGE_SIZE = 50;

export function ActivityPage() {
  const [entries, setEntries] = useState<Activity[]>([]);
  const [page, setPage] = useState(1);
  const [pages, setPages] = useState(1);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [loadingMore, setLoadingMore] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    api.activities(1, PAGE_SIZE)
      .then((result) => {
        setEntries(result.items);
        setPages(result.pages);
        setTotal(result.total);
      })
      .catch((reason) => setError(reason instanceof Error ? reason.message : String(reason)))
      .finally(() => setLoading(false));
  }, []);

  const loadMore = async () => {
    const nextPage = page + 1;
    setLoadingMore(true);
    try {
      const result = await api.activities(nextPage, PAGE_SIZE);
      setEntries((current) => [...current, ...result.items]);
      setPage(nextPage);
      setPages(result.pages);
      setTotal(result.total);
    } finally {
      setLoadingMore(false);
    }
  };

  if (loading) return <Spinner label="Aktivitäten werden geladen …" />;
  if (error) return <p className="py-20 text-center text-rust">{error}</p>;

  return (
    <section className="mx-auto max-w-4xl animate-fade-up">
      <div className="mb-6 border-b border-rule pb-4">
        <p className="label-caps">Compedium-Chronik</p>
        <h1 className="mt-1 font-serif text-3xl text-ink">Alle Aktivitäten</h1>
        <p className="mt-1 text-sm text-ink-3">
          {total} {total === 1 ? "Eintrag" : "Einträge"}
        </p>
      </div>

      {entries.length === 0 ? (
        <Empty title="Noch keine Aktivitäten" hint="Fotos, Begegnungen, neue Arten und erreichte Level erscheinen hier." />
      ) : (
        <>
          <ActivityList entries={entries} />
          {page < pages && (
            <div className="mt-8 text-center">
              <button
                type="button"
                onClick={loadMore}
                disabled={loadingMore}
                className="rounded-full border border-rule-2 bg-paper px-6 py-2.5 text-sm text-ink-2 transition-colors hover:bg-paper-2 disabled:opacity-50"
              >
                {loadingMore ? "Lädt …" : "Weitere Aktivitäten laden"}
              </button>
            </div>
          )}
        </>
      )}
    </section>
  );
}
