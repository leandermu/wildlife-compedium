import { Link } from "react-router-dom";
import type { Activity } from "../types";
import { formatRelativeTime } from "../lib/format";

export function ActivityList({ entries }: { entries: Activity[] }) {
  return (
    <ol className="divide-y divide-rule border-y border-rule">
      {entries.map((entry, index) => {
        const action = entry.kind === "photographed"
          ? "fotografiert"
          : entry.kind === "seen" ? "gesehen" : "hinzugefügt";
        return (
          <li key={`${entry.kind}-${entry.species_id}-${entry.occurred_at}-${index}`}>
            <Link
              to={`/arten/${entry.species_slug}`}
              className="flex items-center gap-3 px-2 py-3 transition-colors hover:bg-paper-2"
            >
              <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-paper-2 text-lg" aria-hidden>
                {entry.profile_avatar}
              </span>
              <p className="min-w-0 flex-1 text-[14px] text-ink-2">
                <strong className="font-semibold text-ink">{entry.profile_name}</strong>
                {` hat `}
                <span className="font-serif text-[15px] text-ink">{entry.species_name}</span>
                {` ${action}`}
              </p>
              <time dateTime={entry.occurred_at} className="shrink-0 text-[12px] text-ink-3">
                {formatRelativeTime(entry.occurred_at)}
              </time>
            </Link>
          </li>
        );
      })}
    </ol>
  );
}
