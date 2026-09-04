const MONTHS = [
  "Januar", "Februar", "März", "April", "Mai", "Juni",
  "Juli", "August", "September", "Oktober", "November", "Dezember",
];

/** ISO date -> 03.06.2027 */
export function formatDate(iso: string | null | undefined): string {
  if (!iso) return "";
  const [y, m, d] = iso.slice(0, 10).split("-");
  if (!y || !m || !d) return iso;
  return `${d}.${m}.${y}`;
}

export function formatDateLong(iso: string | null | undefined): string {
  if (!iso) return "";
  const [y, m, d] = iso.slice(0, 10).split("-");
  const month = MONTHS[Number(m) - 1];
  return month ? `${Number(d)}. ${month} ${y}` : formatDate(iso);
}

export function formatRelativeTime(iso: string): string {
  // SQLite stores UTC timestamps without a timezone suffix. Browsers otherwise
  // interpret them as local time, shifting recent edits by the local offset.
  const timestamp = /(?:z|[+-]\d{2}:\d{2})$/i.test(iso) ? iso : `${iso}Z`;
  const elapsed = Date.now() - new Date(timestamp).getTime();
  if (!Number.isFinite(elapsed) || elapsed < 0) return formatDate(iso);
  const minutes = Math.floor(elapsed / 60_000);
  if (minutes < 1) return "gerade eben";
  if (minutes < 60) return `vor ${minutes} Min.`;
  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `vor ${hours} Std.`;
  const days = Math.floor(hours / 24);
  if (days === 1) return "gestern";
  if (days < 14) return `vor ${days} Tagen`;
  return formatDate(iso);
}

export function formatNumber(n: number): string {
  return n.toLocaleString("de-DE");
}

export function formatBytes(bytes: number): string {
  if (!Number.isFinite(bytes) || bytes <= 0) return "0 B";
  const units = ["B", "KB", "MB", "GB", "TB"];
  const unitIndex = Math.min(Math.floor(Math.log(bytes) / Math.log(1024)), units.length - 1);
  const value = bytes / 1024 ** unitIndex;
  return `${value.toLocaleString("de-DE", {
    minimumFractionDigits: 0,
    maximumFractionDigits: unitIndex === 0 ? 0 : value < 10 ? 2 : 1,
  })} ${units[unitIndex]}`;
}

export function percent(collected: number, total: number): number {
  return total === 0 ? 0 : Math.round((collected / total) * 100);
}

export const DIFFICULTY_LABEL: Record<number, string> = {
  1: "Häufig",
  2: "Ungewöhnlich",
  3: "Anspruchsvoll",
  4: "Sehr selten",
  5: "Legendär",
};

export const STATUS_LABEL: Record<string, string> = {
  locked: "Noch nicht fotografiert",
  unlocked: "Freigeschaltet",
};

/** Stable pseudo-random 0..1 from a string — used for placeholder artwork. */
export function hashUnit(seed: string, salt = 0): number {
  let h = 2166136261 ^ salt;
  for (let i = 0; i < seed.length; i++) {
    h ^= seed.charCodeAt(i);
    h = Math.imul(h, 16777619);
  }
  return ((h >>> 0) % 10000) / 10000;
}
