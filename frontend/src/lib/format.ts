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

export function formatNumber(n: number): string {
  return n.toLocaleString("de-DE");
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
  mastered: "Meisterhaft",
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
