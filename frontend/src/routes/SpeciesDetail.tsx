import { useCallback, useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { api } from "../api";
import type { Observation, Photo, SpeciesDetail } from "../types";
import { PlaceholderArt } from "../components/PlaceholderArt";
import { PhotoUpload } from "../components/PhotoUpload";
import { DifficultyStars, LockIcon, SectionTitle, Spinner } from "../components/ui";
import { formatDate, formatDateLong } from "../lib/format";

const GROUP_LABEL: Record<string, string> = {
  bird: "Vögel", mammal: "Säugetiere", butterfly: "Schmetterlinge", insect: "Insekten",
  amphibian: "Amphibien", reptile: "Reptilien", fish: "Fische", other: "Sonstige",
};
const HABITAT_LABEL: Record<string, string> = {
  garden: "Garten", city: "Stadt", park: "Park", forest: "Wald", field: "Feld & Wiese",
  water: "Gewässer", moor: "Moor", heath: "Heide & Trockenrasen", alps: "Berge & Alpen",
  coast: "Küste", night: "Nacht", savanna: "Savanne", rainforest: "Regenwald",
  ocean: "Offenes Meer",
};
const REGION_LABEL: Record<string, string> = {
  bavaria: "Bayern", germany: "Deutschland", europe: "Europa", world: "Welt & Expedition",
};

export function SpeciesDetailPage() {
  const { slug = "" } = useParams();
  const [species, setSpecies] = useState<SpeciesDetail | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [lightbox, setLightbox] = useState<Photo | null>(null);
  const [lightboxInfo, setLightboxInfo] = useState(false);
  const [justUnlocked, setJustUnlocked] = useState(false);
  const [obsDate, setObsDate] = useState("");
  const [obsTime, setObsTime] = useState("");
  const [obsPlace, setObsPlace] = useState("");
  const [obsNote, setObsNote] = useState("");
  const [editingPhoto, setEditingPhoto] = useState<Photo | null>(null);
  const [editingObservation, setEditingObservation] = useState<Observation | null>(null);

  const load = useCallback(
    (announceUnlock = false) =>
      api
        .speciesDetail(slug)
        .then((s) => {
          setSpecies((prev) => {
            if (announceUnlock && prev?.status === "locked" && s.status !== "locked") {
              setJustUnlocked(true);
              setTimeout(() => setJustUnlocked(false), 2600);
            }
            return s;
          });
        })
        .catch((e) => setError(String(e.message ?? e))),
    [slug],
  );

  useEffect(() => {
    setSpecies(null);
    setError(null);
    load();
  }, [load]);

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => e.key === "Escape" && setLightbox(null);
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, []);

  if (error) return <p className="py-20 text-center text-ink-3">{error}</p>;
  if (!species) return <Spinner />;

  const unlocked = species.status !== "locked";
  const hero = species.photos.find((p) => p.is_best_photo) ?? species.photos[0];

  const openPhoto = (photo: Photo) => {
    setLightboxInfo(false);
    setLightbox(photo);
  };

  const setBest = async (id: number) => {
    await api.updatePhoto(id, { is_best_photo: true });
    load();
  };
  const removePhoto = async (id: number) => {
    if (!confirm("Dieses Foto wirklich löschen?")) return;
    await api.deletePhoto(id);
    load();
  };
  const addObservation = async (e: React.FormEvent) => {
    e.preventDefault();
    await api.createObservation({
      species_id: species.id,
      date: obsDate || null,
      time: obsTime || null,
      location_name: obsPlace,
      notes: obsNote,
    });
    setObsDate("");
    setObsTime("");
    setObsPlace("");
    setObsNote("");
    load();
  };

  return (
    <article className="animate-fade-up">
      <Link to="/arten" className="label-caps no-print mb-6 inline-block hover:text-ink-2">
        ← Zurück zur Übersicht
      </Link>

      {/* Kopf */}
      <header className="border-b border-rule pb-8 text-center">
        <p className="label-caps">
          {GROUP_LABEL[species.group] ?? species.group}
          {species.order_name && ` · ${species.order_name}`}
          {species.family && ` · ${species.family}`}
        </p>
        <h1 className="mt-2 font-serif text-4xl leading-tight text-ink sm:text-5xl">
          {species.common_name}
        </h1>
        <p className="mt-1 font-serif text-xl italic text-ink-3">{species.scientific_name}</p>
        <div className="mt-4 flex flex-wrap items-center justify-center gap-x-6 gap-y-2">
          <DifficultyStars value={species.difficulty} showLabel size="md" />
          {species.regions.map((r) => (
            <span key={r} className="label-caps text-moss-2">
              {REGION_LABEL[r] ?? r} ✓
            </span>
          ))}
        </div>
      </header>

      <div className="mt-10 grid gap-10 lg:grid-cols-[1.35fr_1fr]">
        {/* Bildspalte */}
        <div>
          <figure className="relative overflow-hidden rounded-sm border border-rule-2 bg-paper shadow-[var(--shadow-card)]">
            <div className="aspect-[4/3] bg-paper-2">
              {unlocked && hero?.url ? (
                <button
                  onClick={() => openPhoto(hero)}
                  className="h-full w-full cursor-zoom-in"
                  aria-label="Foto vergrößern"
                >
                  <img
                    src={hero.url}
                    alt={`Eigenes Foto: ${species.common_name}`}
                    className="h-full w-full object-cover"
                  />
                </button>
              ) : species.reference_image_url ? (
                <div className="relative h-full">
                  <img
                    src={species.reference_image_url}
                    alt={`Referenzbild: ${species.common_name}`}
                    className="h-full w-full object-cover opacity-[0.62] mix-blend-multiply"
                  />
                  <span className="pointer-events-none absolute inset-0 bg-paper/25" />
                </div>
              ) : (
                <div className="flex h-full items-center justify-center text-ink-3">
                  <PlaceholderArt
                    group={species.group}
                    seed={species.slug}
                    className="h-[75%] w-[75%] opacity-70"
                  />
                </div>
              )}
            </div>
            {justUnlocked && (
              <div className="pointer-events-none absolute inset-0 flex items-center justify-center bg-paper/60">
                <span className="animate-seal rounded-full border-4 border-moss px-8 py-4 font-serif text-2xl tracking-wide text-moss-2">
                  Freigeschaltet
                </span>
              </div>
            )}
            <figcaption className="flex flex-wrap items-center justify-between gap-3 border-t border-rule px-4 py-3">
              {unlocked ? (
                <>
                  <span className="label-caps text-moss-2">
                    {species.status === "mastered" ? "★ Meisterhaft" : "✓ Freigeschaltet"}
                  </span>
                  <span className="text-[13px] text-ink-3">
                    {hero?.location_name && `📍 ${hero.location_name}`}
                    {hero?.date && ` · 📅 ${formatDate(hero.date)}`}
                  </span>
                </>
              ) : (
                <>
                  <span className="label-caps inline-flex items-center gap-1.5">
                    <LockIcon /> Noch nicht fotografiert
                  </span>
                  <span className="text-[12px] text-ink-3">
                    {species.reference_image_url ? (
                      <>
                        Referenzbild
                        {species.reference_credit && ` · ${species.reference_credit}`}
                        {species.reference_source && (
                          <>
                            {" · "}
                            <a
                              href={species.reference_source}
                              target="_blank"
                              rel="noreferrer"
                              className="link-quiet"
                            >
                              Quelle
                            </a>
                          </>
                        )}
                      </>
                    ) : (
                      "Referenzskizze"
                    )}
                  </span>
                </>
              )}
            </figcaption>
          </figure>

          {/* Weitere Fotos */}
          {species.photos.length > 0 && (
            <section className="mt-8">
              <SectionTitle>
                {species.photos.length === 1
                  ? "Dein Foto"
                  : `Deine ${species.photos.length} Fotos`}
              </SectionTitle>
              <div className="grid grid-cols-2 gap-4 sm:grid-cols-3">
                {species.photos.map((p) => (
                  <figure
                    key={p.id}
                    className={`group overflow-hidden rounded-sm border bg-paper ${
                      p.is_best_photo ? "border-ochre" : "border-rule"
                    }`}
                  >
                    <button
                      onClick={() => openPhoto(p)}
                      className="block aspect-square w-full cursor-zoom-in bg-paper-2"
                    >
                      {p.thumb_url && (
                        <img
                          src={p.thumb_url}
                          alt={p.caption || species.common_name}
                          loading="lazy"
                          className="h-full w-full object-cover"
                        />
                      )}
                    </button>
                    <figcaption className="space-y-1 px-3 py-2 text-[12px] text-ink-3">
                      <p className="text-ink-2">{formatDate(p.date) || "ohne Datum"}</p>
                      {p.location_name && <p className="truncate">{p.location_name}</p>}
                      {p.caption && <p className="truncate italic">{p.caption}</p>}
                      <div className="no-print flex items-center gap-3 pt-1">
                        {p.is_best_photo ? (
                          <span className="text-ochre-2">★ Bestes Foto</span>
                        ) : (
                          <button
                            onClick={() => setBest(p.id)}
                            className="hover:text-ochre-2"
                          >
                            Als bestes wählen
                          </button>
                        )}
                        <button onClick={() => setEditingPhoto(p)} className="hover:text-ink">
                          {p.observation_id ? "Foto & Begegnung bearbeiten" : "Foto bearbeiten"}
                        </button>
                        <button
                          onClick={() => removePhoto(p.id)}
                          className="ml-auto hover:text-rust"
                        >
                          Löschen
                        </button>
                      </div>
                    </figcaption>
                  </figure>
                ))}
              </div>
            </section>
          )}

          {/* Steckbrief */}
          <section className="mt-10">
            <SectionTitle>Steckbrief</SectionTitle>
            {species.description && (
              <p className="mb-6 font-serif text-[1.05rem] leading-relaxed text-ink-2">
                {species.description}
              </p>
            )}
            <dl className="divide-y divide-rule border-y border-rule">
              <Row label="Wissenschaftlich" value={<em>{species.scientific_name}</em>} />
              <Row label="Familie" value={species.family} />
              <Row label="Ordnung" value={species.order_name} />
              <Row label="Größe" value={species.size} />
              <Row label="Spannweite" value={species.wingspan} />
              <Row label="Gewicht" value={species.weight} />
              <Row
                label="Lebensraum"
                value={species.habitats.map((h) => HABITAT_LABEL[h] ?? h).join(" · ")}
              />
              <Row
                label="Verbreitung"
                value={species.regions.map((r) => REGION_LABEL[r] ?? r).join(" · ")}
              />
              {species.countries.length > 0 && (
                <Row label="Länder" value={species.countries.join(", ")} />
              )}
              <Row
                label="Schwierigkeit"
                value={<DifficultyStars value={species.difficulty} showLabel />}
              />
            </dl>
            {species.tags.length > 0 && (
              <div className="mt-5 flex flex-wrap gap-2">
                {species.tags.map((t) => (
                  <Link
                    key={t}
                    to={`/arten?tag=${encodeURIComponent(t)}`}
                    className="rounded-full border border-rule bg-paper-2/60 px-3 py-1 text-[12px] text-ink-3 hover:border-rule-2 hover:text-ink-2"
                  >
                    #{t}
                  </Link>
                ))}
              </div>
            )}
          </section>
        </div>

        {/* Seitenspalte */}
        <aside className="no-print space-y-8">
          <section className="paper-card rounded-sm p-5">
            <h2 className="mb-4 font-serif text-xl">📷 Eigenes Foto</h2>
            {!unlocked && (
              <p className="mb-4 rounded-sm bg-paper-2 px-3 py-2 text-[13px] text-ink-3">
                Diese Art ist noch nicht freigeschaltet. Dein erstes Foto schaltet sie frei.
              </p>
            )}
            <PhotoUpload species={species} onDone={() => load(true)} />
          </section>

          <section className="paper-card rounded-sm p-5">
            <h2 className="mb-1 font-serif text-xl">Begegnungen</h2>
            <p className="mb-4 text-[13px] text-ink-3">
              {species.observations.length === 0
                ? "Noch keine Begegnung notiert."
                : `${species.observations.length} Begegnung${species.observations.length === 1 ? "" : "en"} dokumentiert.`}
            </p>

            {species.observations.length > 0 && (
              <ol className="mb-5 space-y-2.5 border-l border-rule pl-4">
                {species.observations.map((o) => (
                  <li key={o.id} className="relative text-[13px]">
                    <span
                      className={`absolute -left-[21px] top-1.5 h-2 w-2 rounded-full ${
                        o.has_photo ? "bg-moss" : "bg-rule-2"
                      }`}
                    />
                    <p className="text-ink-2">
                      {formatDateLong(o.date) || "ohne Datum"}
                      {o.time && ` · ${o.time.slice(0, 5)} Uhr`}
                      {o.has_photo && <span className="ml-1.5 text-moss-2">📷</span>}
                    </p>
                    {o.location_name && (
                      o.latitude !== null && o.longitude !== null ? (
                        <a
                          href={`https://www.google.com/maps/search/?api=1&query=${o.latitude},${o.longitude}`}
                          target="_blank"
                          rel="noreferrer"
                          className="text-ink-3 underline decoration-rule-2 underline-offset-2 hover:text-moss-2"
                          title="In Google Maps öffnen"
                        >
                          {o.location_name} ↗
                        </a>
                      ) : <p className="text-ink-3">{o.location_name}</p>
                    )}
                    {o.notes && <p className="italic text-ink-3">{o.notes}</p>}
                    <button
                      type="button"
                      onClick={() => setEditingObservation(o)}
                      className="mt-1 text-[11px] text-ink-3 underline decoration-rule-2 underline-offset-2 hover:text-ink"
                    >
                      {o.has_photo ? "Foto & Begegnung bearbeiten" : "Begegnung bearbeiten"}
                    </button>
                  </li>
                ))}
              </ol>
            )}

            <form onSubmit={addObservation} className="space-y-2.5 border-t border-rule pt-4">
              <p className="label-caps">Begegnung ohne Foto notieren</p>
              <div className="grid grid-cols-2 gap-2 sm:grid-cols-3">
                <input
                  type="date"
                  value={obsDate}
                  onInput={(e) => setObsDate(e.currentTarget.value)}
                  className="rounded-sm border border-rule bg-paper px-2 py-1.5 text-[13px] focus:outline-none"
                />
                <input
                  type="time"
                  value={obsTime}
                  onInput={(e) => setObsTime(e.currentTarget.value)}
                  className="rounded-sm border border-rule bg-paper px-2 py-1.5 text-[13px] focus:outline-none"
                />
                <input
                  value={obsPlace}
                  onChange={(e) => setObsPlace(e.target.value)}
                  placeholder="Ort"
                  className="rounded-sm border border-rule bg-paper px-2 py-1.5 text-[13px] focus:outline-none"
                />
              </div>
              <input
                value={obsNote}
                onChange={(e) => setObsNote(e.target.value)}
                placeholder="Notiz"
                className="w-full rounded-sm border border-rule bg-paper px-2 py-1.5 text-[13px] focus:outline-none"
              />
              <button
                type="submit"
                className="w-full rounded-sm border border-rule-2 bg-paper-2 px-3 py-1.5 text-[13px] text-ink-2 hover:bg-paper-3"
              >
                Begegnung eintragen
              </button>
            </form>
          </section>
        </aside>
      </div>

      {lightbox && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-ink/85 p-2 sm:p-6"
          onClick={() => setLightbox(null)}
          role="dialog"
          aria-modal="true"
          aria-label={`Foto von ${species.common_name}`}
        >
          <div
            className="relative flex max-h-[calc(100vh-1rem)] max-w-[min(96rem,calc(100vw-1rem))] flex-col overflow-hidden rounded-lg bg-ink shadow-2xl sm:max-h-[calc(100vh-3rem)] lg:flex-row"
            onClick={(event) => event.stopPropagation()}
          >
            <div className="relative flex min-h-0 flex-1 items-center justify-center bg-black/25">
              {lightbox.url && (
                <img
                  src={lightbox.url}
                  alt={lightbox.caption || species.common_name}
                  className="max-h-[70vh] max-w-full object-contain lg:max-h-[calc(100vh-3rem)]"
                />
              )}
              <div className="absolute right-3 top-3 flex gap-2">
                <button
                  type="button"
                  onClick={() => setLightboxInfo((visible) => !visible)}
                  className={`flex h-10 w-10 items-center justify-center rounded-full border text-lg font-serif italic backdrop-blur transition ${lightboxInfo ? "border-paper bg-paper text-ink" : "border-paper/40 bg-ink/55 text-paper hover:bg-ink/75"}`}
                  aria-label={lightboxInfo ? "Bildinformationen ausblenden" : "Bildinformationen anzeigen"}
                  aria-pressed={lightboxInfo}
                  title="Bildinformationen"
                >
                  i
                </button>
                <button
                  type="button"
                  onClick={() => setLightbox(null)}
                  className="flex h-10 w-10 items-center justify-center rounded-full border border-paper/40 bg-ink/55 text-2xl text-paper backdrop-blur transition hover:bg-ink/75"
                  aria-label="Schließen"
                >
                  ×
                </button>
              </div>
            </div>
            {lightboxInfo && <PhotoInfo photo={lightbox} />}
          </div>
        </div>
      )}

      {editingPhoto && (
        <EditEntryDialog
          title={editingPhoto.observation_id ? "Foto & Begegnung bearbeiten" : "Foto bearbeiten"}
          date={editingPhoto.date ?? ""}
          time={editingPhoto.time?.slice(0, 5) ?? ""}
          location={editingPhoto.location_name}
          note={editingPhoto.caption}
          onClose={() => setEditingPhoto(null)}
          onSave={async (values) => {
            await api.updatePhoto(editingPhoto.id, {
              date: values.date || null,
              time: values.time || null,
              location_name: values.location,
              caption: values.note,
            });
            setEditingPhoto(null);
            setLightbox(null);
            await load();
          }}
        />
      )}

      {editingObservation && (
        <EditEntryDialog
          title={editingObservation.has_photo ? "Foto & Begegnung bearbeiten" : "Begegnung bearbeiten"}
          date={editingObservation.date ?? ""}
          time={editingObservation.time?.slice(0, 5) ?? ""}
          location={editingObservation.location_name}
          note={editingObservation.notes}
          onClose={() => setEditingObservation(null)}
          onSave={async (values) => {
            await api.updateObservation(editingObservation.id, {
              date: values.date || null,
              time: values.time || null,
              location_name: values.location,
              notes: values.note,
            });
            setEditingObservation(null);
            await load();
          }}
        />
      )}
    </article>
  );
}

function EditEntryDialog({
  title, date, time, location, note, onClose, onSave,
}: {
  title: string;
  date: string;
  time: string;
  location: string;
  note: string;
  onClose: () => void;
  onSave: (values: { date: string; time: string; location: string; note: string }) => Promise<void>;
}) {
  const [values, setValues] = useState({ date, time, location, note });
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  return (
    <div className="fixed inset-0 z-[60] flex items-center justify-center bg-ink/55 p-4" role="dialog" aria-modal="true">
      <form
        className="w-full max-w-lg space-y-4 rounded-xl border border-rule bg-paper p-5 shadow-2xl"
        onSubmit={async (event) => {
          event.preventDefault();
          setBusy(true);
          setError("");
          try {
            await onSave(values);
          } catch (err) {
            setError(err instanceof Error ? err.message : "Änderung konnte nicht gespeichert werden");
            setBusy(false);
          }
        }}
      >
        <div className="flex items-center justify-between">
          <h2 className="font-serif text-xl">{title}</h2>
          <button type="button" onClick={onClose} className="text-2xl text-ink-3" aria-label="Schließen">×</button>
        </div>
        <div className="grid grid-cols-2 gap-3">
          <label className="block text-xs text-ink-3">Datum
            <input type="date" value={values.date} onInput={(e) => {
              const value = e.currentTarget.value;
              setValues((current) => ({ ...current, date: value }));
            }}
              className="mt-1 w-full rounded-sm border border-rule bg-paper px-3 py-2 text-sm text-ink" />
          </label>
          <label className="block text-xs text-ink-3">Uhrzeit
            <input type="time" value={values.time} onInput={(e) => {
              const value = e.currentTarget.value;
              setValues((current) => ({ ...current, time: value }));
            }}
              className="mt-1 w-full rounded-sm border border-rule bg-paper px-3 py-2 text-sm text-ink" />
          </label>
        </div>
        <label className="block text-xs text-ink-3">Ort
          <input value={values.location} onChange={(e) => setValues((current) => ({ ...current, location: e.target.value }))}
            className="mt-1 w-full rounded-sm border border-rule bg-paper px-3 py-2 text-sm text-ink" />
        </label>
        <label className="block text-xs text-ink-3">Notiz
          <textarea rows={3} value={values.note} onChange={(e) => setValues((current) => ({ ...current, note: e.target.value }))}
            className="mt-1 w-full rounded-sm border border-rule bg-paper px-3 py-2 text-sm text-ink" />
        </label>
        {error && <p className="text-xs text-rust">{error}</p>}
        <div className="flex justify-end gap-2">
          <button type="button" onClick={onClose} className="rounded-sm border border-rule px-4 py-2 text-sm">Abbrechen</button>
          <button type="submit" disabled={busy} className="rounded-sm bg-moss px-4 py-2 text-sm text-paper disabled:opacity-50">
            {busy ? "Speichert …" : "Speichern"}
          </button>
        </div>
      </form>
    </div>
  );
}

const META_LABELS: Record<string, string> = {
  camera_make: "Hersteller",
  camera_model: "Kamera",
  lens_make: "Objektivhersteller",
  lens_model: "Objektiv",
  focal_length: "Brennweite",
  aperture: "Blende",
  shutter: "Belichtungszeit",
  iso: "ISO",
  software: "Software",
  artist: "Fotograf/in",
  copyright: "Copyright",
  file_format: "Dateiformat",
  color_mode: "Farbmodus",
  width: "Breite",
  height: "Höhe",
};

function metadataValue(value: unknown): string {
  if (value === null || value === undefined) return "";
  if (typeof value === "string" || typeof value === "number" || typeof value === "boolean") {
    return String(value);
  }
  if (Array.isArray(value)) return value.map(metadataValue).join(", ");
  if (typeof value === "object" && "encoding" in value) return "Binärdaten gespeichert";
  return JSON.stringify(value);
}

function flattenMetadata(value: unknown, prefix = ""): Array<[string, string]> {
  if (!value || typeof value !== "object" || Array.isArray(value)) return [];
  return Object.entries(value as Record<string, unknown>).flatMap(([key, item]) => {
    const label = prefix ? `${prefix} · ${key}` : key;
    if (item && typeof item === "object" && !Array.isArray(item) && !("encoding" in item)) {
      return flattenMetadata(item, label);
    }
    return [[label, metadataValue(item)] as [string, string]];
  });
}

function PhotoInfo({ photo }: { photo: Photo }) {
  const metadata = photo.photo_metadata ?? {};
  const curated = Object.entries(META_LABELS)
    .map(([key, label]) => [label, metadataValue(metadata[key])] as const)
    .filter(([, value]) => value);
  const exifRows = [
    ...flattenMetadata(metadata.exif, "EXIF"),
    ...flattenMetadata(metadata.exif_ifds, "EXIF"),
  ];
  const latitude = Number(metadata.latitude);
  const longitude = Number(metadata.longitude);
  const hasGps = Number.isFinite(latitude) && Number.isFinite(longitude);

  return (
    <aside className="max-h-[45vh] w-full shrink-0 overflow-y-auto bg-paper p-5 text-ink lg:max-h-[calc(100vh-3rem)] lg:w-96">
      <p className="label-caps">Bildinformationen</p>
      <h2 className="mt-1 truncate font-serif text-xl">{photo.original_filename || "Foto"}</h2>

      <dl className="mt-4 divide-y divide-rule border-y border-rule text-[13px]">
        {photo.date && <InfoRow label="Aufgenommen" value={`${formatDateLong(photo.date)}${photo.time ? ` · ${photo.time.slice(0, 5)} Uhr` : ""}`} />}
        {photo.location_name && <InfoRow label="Ort" value={photo.location_name} />}
        {photo.caption && <InfoRow label="Notiz" value={photo.caption} />}
        {curated.map(([label, value]) => (
          <InfoRow key={label} label={label} value={value} />
        ))}
      </dl>

      {hasGps && (
        <a
          href={`https://www.google.com/maps/search/?api=1&query=${latitude},${longitude}`}
          target="_blank"
          rel="noreferrer"
          className="mt-4 inline-flex text-[13px] text-moss-2 underline decoration-rule-2 underline-offset-2"
        >
          Aufnahmeort in Google Maps öffnen ↗
        </a>
      )}

      {exifRows.length > 0 && (
        <details className="mt-5 border-t border-rule pt-4">
          <summary className="cursor-pointer text-[13px] font-medium text-ink-2">
            Alle EXIF-Daten ({exifRows.length})
          </summary>
          <dl className="mt-3 space-y-2 text-[11px]">
            {exifRows.map(([label, value], index) => (
              <div key={`${label}-${index}`} className="border-b border-rule/70 pb-2">
                <dt className="break-words text-ink-3">{label}</dt>
                <dd className="mt-0.5 break-words text-ink-2">{value}</dd>
              </div>
            ))}
          </dl>
        </details>
      )}
    </aside>
  );
}

function InfoRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="grid grid-cols-[7rem_1fr] gap-3 py-2">
      <dt className="text-ink-3">{label}</dt>
      <dd className="break-words text-ink-2">{value}</dd>
    </div>
  );
}

function Row({ label, value }: { label: string; value: React.ReactNode }) {
  if (!value || (typeof value === "string" && !value.trim())) return null;
  return (
    <div className="grid grid-cols-[9rem_1fr] gap-4 py-2.5">
      <dt className="label-caps pt-0.5">{label}</dt>
      <dd className="text-[15px] text-ink-2">{value}</dd>
    </div>
  );
}
