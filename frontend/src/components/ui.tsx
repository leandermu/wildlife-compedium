import { Link } from "react-router-dom";
import { DIFFICULTY_LABEL, percent } from "../lib/format";

export function DifficultyStars({
  value,
  showLabel = false,
  size = "sm",
}: {
  value: number;
  showLabel?: boolean;
  size?: "sm" | "md";
}) {
  const px = size === "md" ? "text-base" : "text-xs";
  return (
    <span className="inline-flex items-center gap-2" title={DIFFICULTY_LABEL[value]}>
      <span className={`${px} tracking-[0.18em] text-ochre`} aria-hidden>
        {"★".repeat(value)}
        <span className="text-rule-2">{"★".repeat(5 - value)}</span>
      </span>
      {showLabel && <span className="label-caps">{DIFFICULTY_LABEL[value]}</span>}
      <span className="sr-only">
        Schwierigkeit {value} von 5 – {DIFFICULTY_LABEL[value]}
      </span>
    </span>
  );
}

export function ProgressBar({
  collected,
  total,
  thick = false,
}: {
  collected: number;
  total: number;
  thick?: boolean;
}) {
  const pct = percent(collected, total);
  return (
    <div
      className={`w-full overflow-hidden rounded-full bg-paper-3 ${thick ? "h-2.5" : "h-1.5"}`}
      role="progressbar"
      aria-valuenow={collected}
      aria-valuemin={0}
      aria-valuemax={total}
      aria-label={`${collected} von ${total}`}
    >
      <div
        className="h-full rounded-full bg-gradient-to-r from-moss-2 to-moss transition-[width] duration-700 ease-out"
        style={{ width: `${pct}%` }}
      />
    </div>
  );
}

export function StatusSeal({ status }: { status: string }) {
  if (status === "locked") {
    return (
      <span className="label-caps inline-flex items-center gap-1.5 text-ink-3">
        <LockIcon /> Noch nicht fotografiert
      </span>
    );
  }
  return (
    <span className="label-caps inline-flex items-center gap-1.5 text-moss-2">
      ✓ Freigeschaltet
    </span>
  );
}

export function LockIcon({ className = "h-3 w-3" }: { className?: string }) {
  return (
    <svg viewBox="0 0 16 16" className={className} fill="none" stroke="currentColor" strokeWidth="1.5" aria-hidden>
      <rect x="3" y="7" width="10" height="7" rx="1.5" />
      <path d="M5.5 7V5a2.5 2.5 0 0 1 5 0v2" />
    </svg>
  );
}

export function Pill({
  children,
  active = false,
  onClick,
  count,
  as = "button",
  to,
}: {
  children: React.ReactNode;
  active?: boolean;
  onClick?: () => void;
  count?: number;
  as?: "button" | "link";
  to?: string;
}) {
  const cls = `inline-flex items-center gap-1.5 rounded-full border px-3 py-1 text-[13px] transition-colors ${
    active
      ? "border-moss bg-moss text-paper"
      : "border-rule bg-paper text-ink-2 hover:border-rule-2 hover:bg-paper-2"
  }`;
  if (as === "link" && to) {
    return (
      <Link to={to} className={cls}>
        {children}
      </Link>
    );
  }
  return (
    <button type="button" onClick={onClick} className={cls} aria-pressed={active}>
      {children}
      {count !== undefined && (
        <span className={active ? "text-paper-3" : "text-ink-3"}>{count}</span>
      )}
    </button>
  );
}

export function SectionTitle({
  children,
  right,
}: {
  children: React.ReactNode;
  right?: React.ReactNode;
}) {
  return (
    <div className="mb-4 flex items-baseline justify-between gap-4">
      <h2 className="font-serif text-2xl text-ink">{children}</h2>
      {right}
    </div>
  );
}

export function Empty({ title, hint }: { title: string; hint?: string }) {
  return (
    <div className="paper-card rounded-sm px-8 py-14 text-center">
      <p className="font-serif text-xl text-ink-2">{title}</p>
      {hint && <p className="mt-2 text-sm text-ink-3">{hint}</p>}
    </div>
  );
}

export function Spinner({ label = "Lädt …" }: { label?: string }) {
  return (
    <div className="flex items-center justify-center gap-3 py-16 text-ink-3">
      <span className="h-4 w-4 animate-spin rounded-full border-2 border-rule-2 border-t-moss" />
      <span className="text-sm">{label}</span>
    </div>
  );
}
