import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../api";
import type { Achievement } from "../types";
import { ProgressBar, Spinner } from "../components/ui";
import { formatDate } from "../lib/format";

export function AchievementsPage() {
  const [items, setItems] = useState<Achievement[] | null>(null);

  useEffect(() => {
    api.achievements().then(setItems);
  }, []);

  if (!items) return <Spinner />;

  const unlocked = items.filter((i) => i.unlocked).length;

  return (
    <div className="animate-fade-up">
      <header className="border-b border-rule pb-6 text-center">
        <p className="label-caps">Ehrentafel</p>
        <h1 className="mt-2 font-serif text-4xl">Auszeichnungen</h1>
        <p className="mt-2 text-ink-3">
          {unlocked} von {items.length} begonnen oder erreicht
        </p>
      </header>

      <section className="mt-8 columns-1 gap-5 sm:columns-2 xl:columns-3">
        {items.map((a) => (
          <div key={a.id} className="mb-5 break-inside-avoid">
            <Card item={a} />
          </div>
        ))}
      </section>
    </div>
  );
}

function Card({ item }: { item: Achievement }) {
  const done = item.tiers.length > 0 && item.tiers.every((t) => t.unlocked);
  const filterParams = new URLSearchParams();
  for (const [key, values] of Object.entries(item.filter ?? {})) {
    values.forEach((value) => filterParams.append(key, String(value)));
  }
  const card = (
    <article
      id={item.id}
      className={`flex flex-col rounded-sm border p-5 transition-colors ${filterParams.size > 0 ? "h-full hover:border-moss hover:shadow-[var(--shadow-card)]" : ""} ${
        done
          ? "border-ochre bg-paper shadow-[var(--shadow-card)]"
          : item.unlocked
            ? "border-rule-2 bg-paper"
            : "border-rule bg-paper-2/50"
      }`}
    >
      <div className="flex items-start gap-3">
        <span className={`text-2xl ${item.unlocked ? "" : "opacity-40 grayscale"}`} aria-hidden>
          {item.icon}
        </span>
        <div className="min-w-0 flex-1">
          <h3 className="font-serif text-xl leading-tight text-ink">{item.name}</h3>
        </div>
        <span className={`shrink-0 rounded-full border px-2.5 py-1 text-[11px] font-semibold ${
          item.unlocked ? "border-moss bg-sage/15 text-moss-2" : "border-rule text-ink-3"
        }`}>
          Level {item.level}
        </span>
        {done && <span className="text-ochre" title="Vollständig">★</span>}
      </div>

      <p className="mt-3 text-[14px] text-ink-2">{item.description}</p>

      <div className="mt-4">
        <div className="mb-1.5 flex items-baseline justify-between text-[13px]">
          <span className="text-ink-3">Fortschritt</span>
          <span className="font-serif text-ink">
            {item.progress} / {item.target}
          </span>
        </div>
        <ProgressBar collected={Math.min(item.progress, item.target)} total={item.target} />
      </div>

      {item.tiers.length > 0 && (
        <div className="mt-3 flex flex-wrap gap-1.5">
          {item.tiers.map((t) => (
            <span
              key={t.threshold}
              className={`rounded-full border px-2 py-0.5 text-[11px] ${
                t.unlocked
                  ? "border-moss bg-moss text-paper"
                  : "border-rule text-ink-3"
              }`}
            >
              {t.unlocked ? "✓ " : ""}{t.label} · {t.threshold}
            </span>
          ))}
        </div>
      )}

      {item.species.length > 0 && (
        <ul className="mt-4 space-y-1 border-t border-rule pt-3">
          {item.species.map((s) => (
            <li key={s.slug} className="flex items-center gap-2 text-[13px]">
              <span className={s.collected ? "text-moss-2" : "text-rule-2"}>
                {s.collected ? "☑" : "☐"}
              </span>
              <Link
                to={`/arten/${s.slug}`}
                className={`link-quiet ${s.collected ? "text-ink-2" : "text-ink-3"}`}
              >
                {s.common_name}
              </Link>
            </li>
          ))}
        </ul>
      )}

      {item.unlocked_at && (
        <p className="mt-auto pt-3 text-[12px] text-ink-3">
          Erreicht am {formatDate(item.unlocked_at)}
        </p>
      )}
    </article>
  );

  if (filterParams.size === 0) return card;

  return (
    <Link
      to={`/arten?${filterParams.toString()}`}
      className="block h-full rounded-sm focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-moss"
      aria-label={`${item.name} öffnen`}
    >
      {card}
    </Link>
  );
}
