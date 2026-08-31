import { hashUnit } from "../lib/format";

/**
 * Referenzbild-Platzhalter im Stil einer Federzeichnung.
 * Bewusst KEIN persönliches Foto – die Silhouette dient nur der Wiedererkennung
 * und wird ersetzt, sobald ein eigenes Foto hochgeladen ist.
 */

function Bird() {
  return (
    <g>
      <ellipse cx="58" cy="56" rx="21" ry="15" transform="rotate(-16 58 56)" />
      <circle cx="38" cy="37" r="11" />
      <path d="M27.5 36.5 15 39.5l12.5 4" />
      <path d="M74 62c7 3 13 6 19 12-8-1-14-2-20-5" />
      <path d="M50 52c7-2 15 1 20 8" />
      <path d="M52 70l-2 12M62 70l3 12" />
      <path d="M40 86h34" strokeWidth="1.6" />
      <circle cx="35" cy="35" r="1.6" fill="currentColor" stroke="none" />
    </g>
  );
}

function Mammal() {
  return (
    <g>
      <ellipse cx="56" cy="50" rx="25" ry="13" />
      <path d="M34 45c-5-3-8-9-8-14" />
      <ellipse cx="24" cy="27" rx="9" ry="6" transform="rotate(-18 24 27)" />
      <path d="M17 24l-6-3M20 21c-1-6 2-10 5-13M27 19c2-5 6-7 10-8M24 16c3-1 6-3 7-6" />
      <path d="M40 61l-3 22M52 62v22M64 61l2 22M74 58l4 24" />
      <path d="M79 46c5 2 8 6 7 11" />
      <circle cx="20" cy="26" r="1.4" fill="currentColor" stroke="none" />
    </g>
  );
}

function Butterfly() {
  return (
    <g>
      <path d="M50 32v40" />
      <path d="M49 34c-6-14-20-22-30-16-9 6-6 22 4 28 7 4 18 3 26-4z" />
      <path d="M51 34c6-14 20-22 30-16 9 6 6 22-4 28-7 4-18 3-26-4z" />
      <path d="M49 54c-5 9-16 15-24 12-7-3-7-13 0-18 6-4 17-2 24 2z" />
      <path d="M51 54c5 9 16 15 24 12 7-3 7-13 0-18-6-4-17-2-24 2z" />
      <path d="M49 32c-2-6-6-9-11-11M51 32c2-6 6-9 11-11" />
      <circle cx="37" cy="19" r="1.6" fill="currentColor" stroke="none" />
      <circle cx="63" cy="19" r="1.6" fill="currentColor" stroke="none" />
      <circle cx="28" cy="40" r="4" />
      <circle cx="72" cy="40" r="4" />
    </g>
  );
}

function Insect() {
  return (
    <g>
      <ellipse cx="50" cy="30" rx="7" ry="6" />
      <path d="M50 36v44" />
      <path d="M46 46h8M46 56h8M46 66h8" strokeWidth="1.2" />
      <path d="M47 40C34 32 18 34 10 41c8 8 26 10 37 4z" />
      <path d="M53 40c13-8 29-6 37 1-8 8-26 10-37 4z" />
      <path d="M47 52C36 46 24 48 17 54c8 6 22 6 30 1z" />
      <path d="M53 52c11-6 23-4 30 2-8 6-22 6-30 1z" />
      <path d="M46 27l-6-8M54 27l6-8" strokeWidth="1.2" />
    </g>
  );
}

function Amphibian() {
  return (
    <g>
      <ellipse cx="50" cy="58" rx="24" ry="17" />
      <circle cx="38" cy="40" r="6" />
      <circle cx="62" cy="40" r="6" />
      <circle cx="38" cy="40" r="1.8" fill="currentColor" stroke="none" />
      <circle cx="62" cy="40" r="1.8" fill="currentColor" stroke="none" />
      <path d="M42 47c4 3 12 3 16 0" />
      <path d="M28 52c-9 2-14 9-13 17 5 2 10-2 12-7M72 52c9 2 14 9 13 17-5 2-10-2-12-7" />
      <path d="M15 69l-6 5 8 1M85 69l6 5-8 1" strokeWidth="1.2" />
      <path d="M34 74c-2 6 0 10 4 12M66 74c2 6 0 10-4 12" />
    </g>
  );
}

function Reptile() {
  return (
    <g>
      <path d="M22 52c8-8 22-10 34-6 10 3 18 3 26-1" />
      <ellipse cx="18" cy="50" rx="9" ry="6" transform="rotate(-10 18 50)" />
      <path d="M82 45c9-2 14 2 12 9-2 6-9 8-14 12" />
      <path d="M32 54l-6 12M44 57l-2 13M60 56l4 13M72 52l8 11" />
      <path d="M26 66l-6 4M42 70l-6 4M64 69l6 4M80 63l6 3" strokeWidth="1.2" />
      <path d="M40 46c6-4 14-4 20-1" strokeWidth="1.2" />
      <circle cx="14" cy="48" r="1.5" fill="currentColor" stroke="none" />
    </g>
  );
}

function Fish() {
  return (
    <g>
      <path d="M20 50c14-16 44-18 58-4 4 4 4 12 0 16-14 14-44 12-58-4z" />
      <path d="M78 46c6-5 10-8 16-9-3 8-3 15 0 23-6-1-10-4-16-9" />
      <path d="M40 34c6-8 16-10 22-6M40 66c6 8 16 10 22 6" />
      <path d="M31 47c5 3 11 3 16 0M31 55c5 3 11 3 16 0" strokeWidth="1.2" />
      <circle cx="28" cy="48" r="2" fill="currentColor" stroke="none" />
      <circle cx="28" cy="48" r="5" />
    </g>
  );
}

function Paw() {
  return (
    <g>
      <ellipse cx="50" cy="62" rx="17" ry="14" />
      <ellipse cx="31" cy="42" rx="7" ry="9" transform="rotate(-20 31 42)" />
      <ellipse cx="44" cy="33" rx="7" ry="9" />
      <ellipse cx="58" cy="33" rx="7" ry="9" />
      <ellipse cx="70" cy="42" rx="7" ry="9" transform="rotate(20 70 42)" />
    </g>
  );
}

const SHAPES: Record<string, () => React.JSX.Element> = {
  bird: Bird,
  mammal: Mammal,
  butterfly: Butterfly,
  insect: Insect,
  amphibian: Amphibian,
  reptile: Reptile,
  fish: Fish,
  other: Paw,
};

export function PlaceholderArt({
  group,
  seed,
  className = "",
}: {
  group: string;
  seed: string;
  className?: string;
}) {
  const Shape = SHAPES[group] ?? Paw;
  const drift = hashUnit(seed);
  const tilt = (hashUnit(seed, 7) - 0.5) * 6;

  return (
    <svg
      viewBox="0 0 100 100"
      className={className}
      role="img"
      aria-label="Referenzskizze – noch kein eigenes Foto"
      preserveAspectRatio="xMidYMid meet"
    >
      <defs>
        <pattern
          id={`hatch-${seed}`}
          width="6"
          height="6"
          patternUnits="userSpaceOnUse"
          patternTransform={`rotate(${35 + drift * 20})`}
        >
          <line x1="0" y1="0" x2="0" y2="6" stroke="currentColor" strokeWidth="0.5" opacity="0.18" />
        </pattern>
      </defs>
      <circle cx="50" cy="50" r="44" fill={`url(#hatch-${seed})`} opacity="0.5" />
      <circle
        cx="50"
        cy="50"
        r="44"
        fill="none"
        stroke="currentColor"
        strokeWidth="0.6"
        opacity="0.35"
      />
      <g
        fill="none"
        stroke="currentColor"
        strokeWidth="1.7"
        strokeLinecap="round"
        strokeLinejoin="round"
        opacity="0.75"
        transform={`rotate(${tilt} 50 50)`}
      >
        <Shape />
      </g>
    </svg>
  );
}
