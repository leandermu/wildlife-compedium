import { useEffect, useRef, useState } from "react";
import { api } from "../api";
import type { Profile, SpeciesDetail } from "../types";
import { LazyLocationPicker } from "./LazyLocationPicker";

/** Foto-Upload mit Metadaten. Das Datum wird, wenn leer, aus den EXIF-Daten
 *  der Datei übernommen (serverseitig). */
export function PhotoUpload({
  species,
  onDone,
}: {
  species: SpeciesDetail;
  onDone: () => void;
}) {
  const [file, setFile] = useState<File | null>(null);
  const [preview, setPreview] = useState<string | null>(null);
  const [date, setDate] = useState("");
  const [time, setTime] = useState("");
  const [location, setLocation] = useState("");
  const [latitude, setLatitude] = useState<number | null>(null);
  const [longitude, setLongitude] = useState<number | null>(null);
  const [caption, setCaption] = useState("");
  const [encounterType, setEncounterType] = useState<"wild" | "captive">("wild");
  const [animalSex, setAnimalSex] = useState<"unknown" | "female" | "male">("unknown");
  const [measurement, setMeasurement] = useState("");
  const [observedWeight, setObservedWeight] = useState("");
  const [profiles, setProfiles] = useState<Profile[]>([]);
  const [observerProfileId, setObserverProfileId] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [dragging, setDragging] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);
  const activeProfile = profiles.find(
    (profile) => String(profile.id) === localStorage.getItem("wc-profile-id"),
  );
  const isShared = Boolean(activeProfile?.is_shared);
  const personalProfiles = profiles.filter((profile) => !profile.is_shared);
  const isFish = species.group === "fish" || ["Actinopterygii", "Chondrichthyes"].includes(species.class_name);

  useEffect(() => {
    api.profiles().then(setProfiles).catch(() => setProfiles([]));
  }, []);

  const pick = (f: File | null) => {
    setError(null);
    if (!f) return;
    const suffix = f.name.toLowerCase().split(".").pop();
    const isHeif = suffix === "heic" || suffix === "heif";
    if (!f.type.startsWith("image/") && !isHeif) {
      setError("Bitte eine Bilddatei auswählen.");
      return;
    }
    setFile(f);
    setPreview((old) => {
      if (old) URL.revokeObjectURL(old);
      return isHeif ? null : URL.createObjectURL(f);
    });
  };

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!file) return;
    setBusy(true);
    setError(null);
    try {
      const fd = new FormData();
      fd.append("species_id", String(species.id));
      fd.append("file", file);
      if (date) fd.append("date", date);
      if (time) fd.append("time", time);
      if (location) fd.append("location_name", location);
      if (latitude !== null && longitude !== null) {
        fd.append("latitude", String(latitude));
        fd.append("longitude", String(longitude));
      }
      if (caption) fd.append("caption", caption);
      fd.append("encounter_type", encounterType);
      fd.append("animal_sex", animalSex);
      if (isFish && measurement) fd.append("measurement", measurement);
      if (isFish && observedWeight) fd.append("observed_weight", observedWeight);
      if (isShared) fd.append("observer_profile_id", observerProfileId);
      await api.uploadPhoto(fd);
      setFile(null);
      setPreview(null);
      setDate("");
      setTime("");
      setLocation("");
      setLatitude(null);
      setLongitude(null);
      setCaption("");
      setEncounterType("wild");
      setAnimalSex("unknown");
      setMeasurement("");
      setObservedWeight("");
      setObserverProfileId("");
      if (inputRef.current) inputRef.current.value = "";
      onDone();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Upload fehlgeschlagen");
    } finally {
      setBusy(false);
    }
  };

  return (
    <form onSubmit={submit} className="space-y-4">
      <div
        onDragOver={(e) => {
          e.preventDefault();
          setDragging(true);
        }}
        onDragLeave={() => setDragging(false)}
        onDrop={(e) => {
          e.preventDefault();
          setDragging(false);
          pick(e.dataTransfer.files?.[0] ?? null);
        }}
        onClick={() => inputRef.current?.click()}
        className={`cursor-pointer rounded-sm border-2 border-dashed px-6 py-8 text-center transition-colors ${
          dragging ? "border-moss bg-paper-2" : "border-rule-2 hover:bg-paper-2/60"
        }`}
      >
        {file ? (
          <div className="space-y-3">
            {preview ? (
              <img
                src={preview}
                alt="Vorschau"
                className="mx-auto max-h-56 rounded-sm object-contain shadow-[var(--shadow-card)]"
              />
            ) : (
              <div className="mx-auto flex h-28 w-28 flex-col items-center justify-center rounded-sm border border-rule bg-paper-2 text-ink-3">
                <span className="font-serif text-xl text-ink-2">HEIC</span>
                <span className="mt-1 text-[11px]">Vorschau nach Upload</span>
              </div>
            )}
            <p className="text-[13px] text-ink-3">
              {file?.name} · andere Datei wählen?
            </p>
          </div>
        ) : (
          <>
            <p className="font-serif text-lg text-ink-2">
              {isShared ? "Foto zur gemeinsamen Sammlung hinzufügen" : "Eigenes Foto hinzufügen"}
            </p>
            <p className="mt-1 text-[13px] text-ink-3">
              Datei hierher ziehen oder klicken zum Auswählen
            </p>
          </>
        )}
        <input
          ref={inputRef}
          type="file"
          accept="image/*,.heic,.heif,image/heic,image/heif"
          className="hidden"
          onChange={(e) => pick(e.target.files?.[0] ?? null)}
        />
      </div>

      <div className="grid gap-3 sm:grid-cols-3">
        <Field label="Datum">
          <input
            type="date"
            value={date}
            onInput={(e) => setDate(e.currentTarget.value)}
            className="w-full rounded-sm border border-rule bg-paper px-3 py-2 text-[14px] focus:border-rule-2 focus:outline-none"
          />
        </Field>
        <Field label="Uhrzeit">
          <input
            type="time"
            value={time}
            onInput={(e) => setTime(e.currentTarget.value)}
            className="w-full rounded-sm border border-rule bg-paper px-3 py-2 text-[14px] focus:border-rule-2 focus:outline-none"
          />
        </Field>
        <Field label="Ort (optional)">
          <input
            value={location}
            onChange={(e) => setLocation(e.target.value)}
            placeholder="z. B. Loisach, Bayern"
            className="w-full rounded-sm border border-rule bg-paper px-3 py-2 text-[14px] focus:border-rule-2 focus:outline-none"
          />
        </Field>
      </div>
      <LazyLocationPicker
        latitude={latitude}
        longitude={longitude}
        onChange={(nextLatitude, nextLongitude) => {
          setLatitude(nextLatitude);
          setLongitude(nextLongitude);
          if (nextLatitude === null && nextLongitude === null && location.startsWith("GPS:")) {
            setLocation("");
          }
          if (
            nextLatitude !== null
            && nextLongitude !== null
            && (!location.trim() || location.startsWith("GPS:"))
          ) {
            setLocation(`GPS: ${nextLatitude.toFixed(5)}, ${nextLongitude.toFixed(5)}`);
          }
        }}
      />
      <Field label="Notiz (optional)">
        <input
          value={caption}
          onChange={(e) => setCaption(e.target.value)}
          placeholder="Wie war die Begegnung?"
          className="w-full rounded-sm border border-rule bg-paper px-3 py-2 text-[14px] focus:border-rule-2 focus:outline-none"
        />
      </Field>
      <p className="-mt-2 text-[12px] text-ink-3">
        Datum, Uhrzeit, Ort und Notiz gehören zur Fotobegegnung und werden gemeinsam bearbeitet.
      </p>

      {isShared && (
        <Field label="Beobachtet von">
          <select
            value={observerProfileId}
            onChange={(event) => setObserverProfileId(event.target.value)}
            required
            className="w-full rounded-sm border border-rule bg-paper px-3 py-2 text-[14px] focus:border-rule-2 focus:outline-none"
          >
            <option value="">Profil auswählen …</option>
            {personalProfiles.map((profile) => (
              <option key={profile.id} value={profile.id}>{profile.avatar} {profile.name}</option>
            ))}
          </select>
        </Field>
      )}

      <fieldset>
        <legend className="label-caps mb-1.5 block">Beobachtungsart</legend>
        <div className="flex flex-wrap gap-4 text-[14px] text-ink-2">
          <label className="flex cursor-pointer items-center gap-2">
            <input
              type="radio"
              name="encounter-type"
              value="wild"
              checked={encounterType === "wild"}
              onChange={() => setEncounterType("wild")}
            />
            Freie Wildbahn
          </label>
          <label className="flex cursor-pointer items-center gap-2">
            <input
              type="radio"
              name="encounter-type"
              value="captive"
              checked={encounterType === "captive"}
              onChange={() => setEncounterType("captive")}
            />
            Gefangenschaft
          </label>
        </div>
      </fieldset>

      <fieldset>
        <legend className="label-caps mb-1.5 block">Geschlecht</legend>
        <div className="flex flex-wrap gap-4 text-[14px] text-ink-2">
          {([[
            "unknown", "Unbestimmt",
          ], ["female", "Weiblich"], ["male", "Männlich"]] as const).map(([value, label]) => (
            <label key={value} className="flex cursor-pointer items-center gap-2">
              <input
                type="radio"
                name="animal-sex"
                checked={animalSex === value}
                onChange={() => setAnimalSex(value)}
              />
              {label}
            </label>
          ))}
        </div>
      </fieldset>

      {isFish && (
        <div className="grid gap-3 sm:grid-cols-2">
          <Field label="Maß (optional)">
            <input
              value={measurement}
              onChange={(event) => setMeasurement(event.target.value)}
              placeholder="z. B. 42 cm"
              maxLength={80}
              className="w-full rounded-sm border border-rule bg-paper px-3 py-2 text-[14px] focus:border-rule-2 focus:outline-none"
            />
          </Field>
          <Field label="Gewicht (optional)">
            <input
              value={observedWeight}
              onChange={(event) => setObservedWeight(event.target.value)}
              placeholder="z. B. 1,2 kg"
              maxLength={80}
              className="w-full rounded-sm border border-rule bg-paper px-3 py-2 text-[14px] focus:border-rule-2 focus:outline-none"
            />
          </Field>
        </div>
      )}

      {error && <p className="text-[13px] text-rust">{error}</p>}

      <button
        type="submit"
        disabled={!file || busy || (isShared && !observerProfileId)}
        className="w-full rounded-sm bg-moss px-5 py-2.5 text-[15px] text-paper transition-colors hover:bg-moss-2 disabled:cursor-not-allowed disabled:bg-rule-2"
      >
        {busy
          ? "Wird hochgeladen …"
          : encounterType === "captive"
            ? "Gefangenschaftsbegegnung speichern"
            : species.status === "locked"
            ? "Art freischalten"
            : "Foto hinzufügen"}
      </button>
      <p className="text-center text-[12px] text-ink-3">
        JPG, PNG, WebP, TIFF und HEIC/HEIF. Datum, GPS und weitere EXIF-Daten
        werden automatisch übernommen und am Foto angezeigt.
      </p>
    </form>
  );
}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <label className="block">
      <span className="label-caps mb-1.5 block">{label}</span>
      {children}
    </label>
  );
}
