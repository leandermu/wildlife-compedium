import { Link } from "react-router-dom";
import type { SpeciesListItem } from "../types";
import { formatDate } from "../lib/format";
import { PlaceholderArt } from "./PlaceholderArt";
import { DifficultyStars, LockIcon } from "./ui";

const GROUP_LABEL: Record<string, string> = {
  bird: "Vogel", mammal: "Säugetier", butterfly: "Schmetterling", insect: "Insekt",
  amphibian: "Amphibie", reptile: "Reptil", fish: "Fisch", other: "Sonstiges",
};

export function SpeciesCard({ species }: { species: SpeciesListItem }) {
  const unlocked = species.status !== "locked";
  const photo = species.best_photo_thumb_url ?? species.best_photo_url;

  return (
    <Link
      to={`/arten/${species.slug}`}
      className={`group relative flex flex-col overflow-hidden rounded-sm border transition-all duration-300 ${
        unlocked
          ? "border-rule-2 bg-paper shadow-[var(--shadow-card)] hover:-translate-y-0.5 hover:shadow-[var(--shadow-lift)]"
          : "border-rule bg-paper-2/60 hover:border-rule-2 hover:bg-paper-2"
      }`}
    >
      {/* Kopfzeile: Name */}
      <div className="px-4 pt-4 text-center">
        <h3
          className={`font-serif text-[1.35rem] leading-tight ${
            unlocked ? "text-ink" : "text-ink-2"
          }`}
        >
          {species.common_name}
        </h3>
        <p className="mt-0.5 font-serif text-[0.9rem] italic text-ink-3">
          {species.scientific_name}
        </p>
      </div>

      {/* Bildfeld */}
      <div className="relative mx-4 mt-3 aspect-[4/3] overflow-hidden rounded-sm bg-paper-2">
        {unlocked && photo ? (
          <img
            src={photo}
            alt={`Eigenes Foto: ${species.common_name}`}
            loading="lazy"
            decoding="async"
            onError={(event) => {
              if (species.best_photo_url && !event.currentTarget.dataset.fallback) {
                event.currentTarget.dataset.fallback = "true";
                event.currentTarget.src = species.best_photo_url;
              }
            }}
            className="h-full w-full object-cover transition-transform duration-500 group-hover:scale-[1.03]"
          />
        ) : species.reference_thumb_url ? (
          /* Referenzplatte: zeigt, was zu finden ist – aber sichtbar noch nicht deins */
          <>
            <img
              src={species.reference_thumb_url}
              alt={`Referenzbild: ${species.common_name}`}
              loading="lazy"
              decoding="async"
              className="h-full w-full object-cover opacity-[0.62] mix-blend-multiply transition-all duration-500 group-hover:opacity-80 group-hover:scale-[1.02]"
            />
            <span className="pointer-events-none absolute inset-0 bg-paper/25" />
          </>
        ) : (
          <div className="flex h-full w-full items-center justify-center bg-paper-2 text-ink-3">
            <PlaceholderArt
              group={species.group}
              seed={species.slug}
              className="h-[82%] w-[82%] opacity-70 transition-opacity duration-300 group-hover:opacity-90"
            />
          </div>
        )}
        {unlocked && (
          <span className="pointer-events-none absolute inset-0 ring-1 ring-inset ring-ink/10" />
        )}
      </div>

      {/* Fußzeile */}
      <div className="flex flex-1 flex-col px-4 pb-4 pt-3">
        <div className="flex items-center justify-between">
          <DifficultyStars value={species.difficulty} />
          <span className="label-caps">{GROUP_LABEL[species.group] ?? species.group}</span>
        </div>

        <div className="my-2.5 h-px bg-rule/70" />

        {unlocked ? (
          <div className="space-y-1 text-[13px] text-ink-2">
            <p className="flex items-center gap-1.5">
              <span aria-hidden>📅</span>
              {formatDate(species.display_photo_date) || "ohne Datum"}
            </p>
            {species.display_photo_location && (
              <p className="flex items-center gap-1.5 truncate">
                <span aria-hidden>📍</span>
                <span className="truncate">{species.display_photo_location}</span>
              </p>
            )}
            {species.photo_count > 1 && (
              <p className="text-ink-3">{species.photo_count} Fotos</p>
            )}
          </div>
        ) : (
          <div className="space-y-1 text-[13px] text-ink-3">
            <p className="truncate">{species.family}</p>
            <p className="truncate">{species.size}</p>
          </div>
        )}

        <div className="mt-auto pt-3">
          {unlocked ? (
            <span className="label-caps text-moss-2">
              ✓ Freigeschaltet
            </span>
          ) : (
            <span className="label-caps inline-flex items-center gap-1.5">
              <LockIcon /> Noch nicht fotografiert
            </span>
          )}
        </div>
      </div>
    </Link>
  );
}

export function SpeciesCardSkeleton() {
  return (
    <div className="animate-pulse rounded-sm border border-rule bg-paper-2/50">
      <div className="px-4 pt-4">
        <div className="mx-auto h-5 w-2/3 rounded bg-paper-3" />
        <div className="mx-auto mt-2 h-3 w-1/2 rounded bg-paper-3" />
      </div>
      <div className="mx-4 mt-3 aspect-[4/3] rounded-sm bg-paper-3" />
      <div className="space-y-2 px-4 pb-4 pt-3">
        <div className="h-3 w-1/2 rounded bg-paper-3" />
        <div className="h-3 w-1/3 rounded bg-paper-3" />
      </div>
    </div>
  );
}
