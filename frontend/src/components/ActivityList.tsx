import { Link } from "react-router-dom";
import type { Activity } from "../types";
import { formatRelativeTime } from "../lib/format";

export function ActivityList({ entries }: { entries: Activity[] }) {
  return (
    <ol className="divide-y divide-rule border-y border-rule">
      {entries.map((entry, index) => {
        const isAchievement = entry.kind === "achievement";
        const action = entry.kind === "photographed"
          ? "fotografiert"
          : entry.kind === "seen" ? "gesehen" : "hinzugefügt";
        return (
          <li key={`${entry.kind}-${entry.species_id ?? entry.achievement_id}-${entry.occurred_at}-${index}`}>
            <Link
              to={isAchievement
                ? `/auszeichnungen#${entry.achievement_id}`
                : `/arten/${entry.species_slug}`}
              className="flex items-center gap-3 px-2 py-3 transition-colors hover:bg-paper-2"
            >
              <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-paper-2 text-lg" aria-hidden>
                {isAchievement ? entry.achievement_icon : entry.profile_avatar}
              </span>
              <p className="min-w-0 flex-1 text-[14px] text-ink-2">
                <strong className="font-semibold text-ink">{entry.profile_name}</strong>
                {isAchievement ? (
                  <>
                    {` hat bei `}
                    <span className="font-serif text-[15px] text-ink">{entry.achievement_name}</span>
                    {` Level ${entry.achievement_level} abgeschlossen`}
                  </>
                ) : (
                  <>
                    {` hat `}
                    <span className="font-serif text-[15px] text-ink">{entry.species_name}</span>
                    {` ${action}`}
                  </>
                )}
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
