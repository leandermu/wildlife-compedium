import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../api";
import type { Dashboard as DashboardData } from "../types";
import { formatDate, formatNumber, percent } from "../lib/format";
import { ActivityList } from "../components/ActivityList";
import { ProgressBar, SectionTitle, Spinner } from "../components/ui";

const GROUP_ICON: Record<string, string> = {
  bird: "🐦", mammal: "🦌", butterfly: "🦋", insect: "🐝",
  amphibian: "🐸", reptile: "🦎", fish: "🐟", other: "🐾",
};

export function Dashboard() {
  const [data, setData] = useState<DashboardData | null>(null);
  const [isShared, setIsShared] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api.dashboard().then(setData).catch((e) => setError(String(e.message ?? e)));
    api.profiles().then((profiles) => {
      const activeId = localStorage.getItem("wc-profile-id");
      setIsShared(Boolean(profiles.find((profile) => String(profile.id) === activeId)?.is_shared));
    });
  }, []);

  if (error) {
    return (
      <div className="paper-card mx-auto max-w-lg rounded-sm p-8 text-center">
        <h2 className="font-serif text-xl">Keine Verbindung zum Compedium</h2>
        <p className="mt-2 text-sm text-ink-3">{error}</p>
        <p className="mt-4 text-sm text-ink-3">
          Läuft das Backend? <code className="text-ink-2">uvicorn app.main:app --reload</code>
        </p>
      </div>
    );
  }
  if (!data) return <Spinner label="Compedium wird aufgeschlagen …" />;

  const pct = percent(data.collected, data.total_species);

  return (
    <div className="animate-fade-up space-y-14">
      {/* Titelblatt */}
      <section className="relative overflow-hidden rounded-sm border border-rule bg-paper px-6 py-12 text-center shadow-[var(--shadow-card)] sm:px-12">
        <p className="label-caps">
          {isShared ? "Eure Sammlung der Tierwelt" : "Deine Sammlung der Tierwelt"}
        </p>
        <h1 className="mt-3 font-serif text-4xl leading-tight text-ink sm:text-5xl">
          {formatNumber(data.collected)}
          <span className="text-ink-3"> / {formatNumber(data.total_species)}</span>
          <span className="ml-3 font-sans text-lg font-medium text-ink-3">Arten entdeckt</span>
        </h1>

        <div className="mx-auto mt-8 max-w-2xl">
          <ProgressBar collected={data.collected} total={data.total_species} thick />
          <div className="mt-2 flex justify-between text-[13px] text-ink-3">
            <span>{pct} % des Compediums</span>
            <span>noch {formatNumber(data.total_species - data.collected)} Arten</span>
          </div>
        </div>

        <dl className="mx-auto mt-10 grid max-w-3xl grid-cols-2 gap-y-6 sm:grid-cols-3">
          {[
            ["Eigene Fotos", formatNumber(data.photo_count)],
            ["Begegnungen", formatNumber(data.observation_count)],
            ["Auszeichnungen", `${data.achievements_unlocked} / ${data.achievements_total}`],
          ].map(([label, value]) => (
            <div key={label}>
              <dd className="font-serif text-2xl text-ink">{value}</dd>
              <dt className="label-caps mt-0.5">{label}</dt>
            </div>
          ))}
        </dl>
      </section>

      {/* Gemeinsame Aktivität */}
      {data.activity.length > 0 && (
        <section>
          <SectionTitle
            right={
              <Link to="/aktivitaeten" className="link-quiet text-sm text-ink-2">
                Alle Aktivitäten
              </Link>
            }
          >
            Aktivität
          </SectionTitle>
          <ActivityList entries={data.activity} />
        </section>
      )}

      {/* Sammlung nach Gruppe */}
      <section>
        <SectionTitle
          right={
            <Link to="/arten" className="link-quiet text-sm text-ink-2">
              Alle Arten ansehen
            </Link>
          }
        >
          {isShared ? "Eure Sammlung" : "Deine Sammlung"}
        </SectionTitle>
        <div className="grid gap-x-10 gap-y-5 sm:grid-cols-2 lg:grid-cols-3">
          {data.by_group.map((b) => (
            <Link
              key={b.key}
              to={`/arten?group=${b.key}`}
              className="group block rounded-sm px-3 py-2 transition-colors hover:bg-paper-2"
            >
              <div className="flex items-baseline justify-between gap-3">
                <span className="flex items-center gap-2 text-[15px] text-ink-2 group-hover:text-ink">
                  <span aria-hidden>{GROUP_ICON[b.key] ?? "🐾"}</span>
                  {b.label}
                </span>
                <span className="font-serif text-[15px] tabular-nums text-ink-3">
                  {b.collected} / {b.total}
                </span>
              </div>
              <div className="mt-2">
                <ProgressBar collected={b.collected} total={b.total} />
              </div>
            </Link>
          ))}
        </div>
      </section>

      {/* Regionen */}
      <section>
        <SectionTitle>Nach Region</SectionTitle>
        <div className="grid gap-x-10 gap-y-5 sm:grid-cols-2 lg:grid-cols-4">
          {data.by_region.map((b) => (
            <Link
              key={b.key}
              to={`/arten?region=${b.key}`}
              className="rounded-sm px-3 py-2 transition-colors hover:bg-paper-2"
            >
              <div className="flex items-baseline justify-between gap-3">
                <span className="text-[15px] text-ink-2">{b.label}</span>
                <span className="font-serif text-[15px] tabular-nums text-ink-3">
                  {b.collected} / {b.total}
                </span>
              </div>
              <div className="mt-2">
                <ProgressBar collected={b.collected} total={b.total} />
              </div>
            </Link>
          ))}
        </div>
      </section>

      {/* Zuletzt entdeckt */}
      <section>
        <SectionTitle>Zuletzt entdeckt</SectionTitle>
        {data.recent.length === 0 ? (
          <div className="rounded-sm border border-dashed border-rule-2 px-8 py-12 text-center">
            <p className="font-serif text-xl text-ink-2">Noch nichts gesammelt</p>
            <p className="mx-auto mt-2 max-w-md text-sm text-ink-3">
              Lade dein erstes Foto hoch – eine Art gilt erst dann als gesammelt, wenn du
              sie selbst fotografiert hast.
            </p>
            <Link
              to="/arten"
              className="mt-5 inline-block rounded-full bg-moss px-5 py-2 text-sm text-paper transition-colors hover:bg-moss-2"
            >
              Erste Art auswählen
            </Link>
          </div>
        ) : (
          <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-4 xl:grid-cols-6">
            {data.recent.map((r) => (
              <Link
                key={r.species_id}
                to={`/arten/${r.slug}`}
                className="group overflow-hidden rounded-sm border border-rule-2 bg-paper shadow-[var(--shadow-card)] transition-transform hover:-translate-y-0.5"
              >
                <div className="aspect-square overflow-hidden bg-paper-2">
                  {r.thumb_url && (
                    <img
                      src={r.thumb_url}
                      alt={r.common_name}
                      loading="lazy"
                      onError={(event) => {
                        if (r.photo_url && !event.currentTarget.dataset.fallback) {
                          event.currentTarget.dataset.fallback = "true";
                          event.currentTarget.src = r.photo_url;
                        }
                      }}
                      className="h-full w-full object-cover transition-transform duration-500 group-hover:scale-105"
                    />
                  )}
                </div>
                <div className="px-3 py-2">
                  <p className="truncate font-serif text-[15px] text-ink">{r.common_name}</p>
                  <p className="truncate text-[12px] text-ink-3">
                    {formatDate(r.date)}
                    {r.location_name && ` · ${r.location_name}`}
                  </p>
                </div>
              </Link>
            ))}
          </div>
        )}
      </section>

      {/* Nächste Herausforderungen */}
      {data.challenges.length > 0 && (
        <section>
          <SectionTitle>Nächste Herausforderungen</SectionTitle>
          <ul className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
            {data.challenges.map((c) => (
              <li key={c.label}>
                <Link
                  to={`/arten?${new URLSearchParams(c.filter).toString()}`}
                  className="flex items-center justify-between gap-4 rounded-sm border border-rule bg-paper px-4 py-3 transition-colors hover:border-rule-2 hover:bg-paper-2"
                >
                  <span className="text-[15px] text-ink-2">{c.label}</span>
                  <span className="font-serif text-lg text-ochre">{c.remaining}</span>
                </Link>
              </li>
            ))}
          </ul>
        </section>
      )}
    </div>
  );
}
