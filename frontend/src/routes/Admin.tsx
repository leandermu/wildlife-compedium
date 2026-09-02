import { useEffect, useRef, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { api } from "../api";
import type { Meta, SpeciesDetail, SpeciesListItem } from "../types";
import { SectionTitle } from "../components/ui";
import { formatNumber, formatRelativeTime } from "../lib/format";

const EMPTY = {
  common_name: "", scientific_name: "", group: "other", class_name: "Aves",
  family: "", order_name: "", activity: "diurnal" as "diurnal" | "nocturnal",
  description: "", size: "", wingspan: "", weight: "", difficulty: 1,
  habitats: [] as string[], regions: [] as string[], tags: [] as string[],
};

const parseTags = (value: string) =>
  value.split(",").map((tag) => tag.trim()).filter(Boolean);

export function AdminPage() {
  const [searchParams, setSearchParams] = useSearchParams();
  const [meta, setMeta] = useState<Meta | null>(null);
  const [form, setForm] = useState({ ...EMPTY });
  const [tagInput, setTagInput] = useState("");
  const [editing, setEditing] = useState<SpeciesDetail | null>(null);
  const [message, setMessage] = useState<{ kind: "ok" | "err"; text: string } | null>(null);
  const [isSavingSpecies, setIsSavingSpecies] = useState(false);
  const [createMode, setCreateMode] = useState<"automatic" | "manual">("automatic");
  const [referenceImage, setReferenceImage] = useState<File | null>(null);
  const [search, setSearch] = useState("");
  const [results, setResults] = useState<SpeciesListItem[]>([]);
  const [total, setTotal] = useState(0);
  const [backupInfo, setBackupInfo] = useState<string | null>(null);
  const [backupError, setBackupError] = useState(false);
  const [backupLoading, setBackupLoading] = useState(false);
  const backupRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    api.meta().then(setMeta);
  }, []);

  const refresh = () => {
    api.species({ q: search || undefined, page_size: 24, sort: "updated_desc" }).then((r) => {
      setResults(r.items);
      setTotal(r.total);
    });
  };
  useEffect(() => {
    const t = setTimeout(refresh, 250);
    return () => clearTimeout(t);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [search]);

  const toggleList = (key: "habitats" | "regions" | "tags", value: string) =>
    setForm((f) => ({
      ...f,
      [key]: f[key].includes(value) ? f[key].filter((v) => v !== value) : [...f[key], value],
    }));

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setMessage(null);
    try {
      if (!editing) {
        setIsSavingSpecies(true);
        let imported: SpeciesDetail;
        if (createMode === "automatic") {
          imported = await api.createSpeciesAutomatically(form.common_name);
        } else {
          const fd = new FormData();
          fd.append("data", JSON.stringify({
            ...form,
            difficulty: Number(form.difficulty),
            tags: [...new Set([...form.tags, ...parseTags(tagInput)])],
          }));
          if (referenceImage) fd.append("image", referenceImage);
          imported = await api.createSpeciesManual(fd);
        }
        setMessage({ kind: "ok", text: `„${imported.common_name}" wurde angelegt.` });
        setForm({ ...EMPTY });
        setTagInput("");
        setReferenceImage(null);
        refresh();
        return;
      }
      const payload = {
        ...form,
        difficulty: Number(form.difficulty),
        tags: [...new Set([...form.tags, ...parseTags(tagInput)])],
      };
      await api.updateSpecies(editing.slug, payload);
      setMessage({ kind: "ok", text: `„${form.common_name}" aktualisiert.` });
      setForm({ ...EMPTY });
      setTagInput("");
      setEditing(null);
      setSearchParams({});
      refresh();
    } catch (err) {
      setMessage({ kind: "err", text: err instanceof Error ? err.message : "Fehler" });
    } finally {
      setIsSavingSpecies(false);
    }
  };

  const edit = async (slug: string) => {
    const s = await api.speciesDetail(slug);
    setEditing(s);
    setForm({
      common_name: s.common_name, scientific_name: s.scientific_name, group: s.group,
      class_name: s.class_name, family: s.family, order_name: s.order_name,
      activity: s.activity, description: s.description,
      size: s.size, wingspan: s.wingspan, weight: s.weight, difficulty: s.difficulty,
      habitats: s.habitats, regions: s.regions,
      tags: s.tags.filter((tag) => meta?.tags.some((option) => option.value === tag)),
    });
    setTagInput(
      s.tags.filter((tag) => !meta?.tags.some((option) => option.value === tag)).join(", "),
    );
    window.scrollTo({ top: 0, behavior: "smooth" });
  };

  const requestedEdit = searchParams.get("edit");
  useEffect(() => {
    if (!meta || !requestedEdit || editing?.slug === requestedEdit) return;
    void edit(requestedEdit);
    // The edit function intentionally reads the loaded vocabulary once.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [meta, requestedEdit, editing?.slug]);

  const remove = async (s: SpeciesListItem) => {
    if (
      !confirm(
        `„${s.common_name}" endgültig löschen?` +
          (s.photo_count > 0 ? `\n\nAchtung: ${s.photo_count} eigene Fotos gehen verloren!` : ""),
      )
    )
      return;
    await api.deleteSpecies(s.slug);
    refresh();
  };

  const loadBackup = async (file: File) => {
    if (!confirm(
      "Backup laden?\n\nDer aktuelle Stand mit allen Arten, Profilen, Einträgen und Fotos wird vollständig durch das Backup ersetzt.",
    )) {
      if (backupRef.current) backupRef.current.value = "";
      return;
    }
    setBackupLoading(true);
    setBackupError(false);
    setBackupInfo("Backup wird geprüft und geladen …");
    try {
      const result = await api.restoreBackup(file);
      setBackupInfo(
        `${result.species} Arten, ${result.profiles} Profile, ${result.observations} Begegnungen und ${result.photos} Fotos geladen. Die Seite wird neu geladen …`,
      );
      localStorage.removeItem("wc-profile-id");
      window.setTimeout(() => window.location.reload(), 1200);
    } catch (err) {
      setBackupInfo(err instanceof Error ? err.message : "Backup konnte nicht geladen werden");
      setBackupError(true);
      setBackupLoading(false);
    }
    if (backupRef.current) backupRef.current.value = "";
  };

  return (
    <div className="animate-fade-up space-y-12">
      <header className="border-b border-rule pb-6">
        <p className="label-caps">Datenpflege</p>
        <h1 className="mt-2 font-serif text-4xl">Verwaltung</h1>
        <p className="mt-2 text-ink-3">
          Arten anlegen und den gemeinsamen Artenkatalog pflegen.
        </p>
      </header>

      {/* Formular */}
      <section>
        <SectionTitle
          right={
            editing && (
              <button
                onClick={() => {
                  setEditing(null);
                  setSearchParams({});
                  setForm({ ...EMPTY });
                  setTagInput("");
                }}
                className="text-[13px] text-ink-3 hover:text-ink-2"
              >
                Bearbeitung abbrechen
              </button>
            )
          }
        >
          {editing ? `„${editing.common_name}" bearbeiten` : "Neue Art anlegen"}
        </SectionTitle>

        <form onSubmit={submit} className="paper-card space-y-4 rounded-sm p-5">
          {!editing && (
            <>
              <div className="grid max-w-md grid-cols-2 gap-1 rounded-lg bg-paper-2 p-1">
                <button type="button" onClick={() => setCreateMode("automatic")}
                  className={`rounded-md px-3 py-2 text-sm ${createMode === "automatic" ? "bg-paper text-ink shadow-sm" : "text-ink-3"}`}>
                  Automatisch
                </button>
                <button type="button" onClick={() => setCreateMode("manual")}
                  className={`rounded-md px-3 py-2 text-sm ${createMode === "manual" ? "bg-paper text-ink shadow-sm" : "text-ink-3"}`}>
                  Manuell erstellen
                </button>
              </div>
              <p className="max-w-2xl text-[14px] text-ink-2">
                {createMode === "automatic"
                  ? "Gib nur den Namen ein. Taxonomie und Vorkommen werden aus strukturierten Artendaten ergänzt; Kurztext und Bild stammen, wenn verfügbar, aus der deutschsprachigen Wikipedia."
                  : "Trage die Angaben selbst ein. Ein hochgeladenes Bild wird automatisch als einheitliches Referenz- und Vorschaubild aufbereitet."}
              </p>
              {createMode === "automatic" && (
                <Input label="Name des Tiers *" value={form.common_name} required
                  placeholder="z. B. Eisvogel"
                  onChange={(v) => setForm({ ...form, common_name: v })} />
              )}
            </>
          )}
          {(editing || createMode === "manual") && (
            <>
          <div className="grid gap-4 sm:grid-cols-2">
            <Input label="Art (deutscher Name) *" value={form.common_name} required
              onChange={(v) => setForm({ ...form, common_name: v })} />
            <Input label="Art (wissenschaftlicher Name)" value={form.scientific_name}
              onChange={(v) => setForm({ ...form, scientific_name: v })} />
            <label className="block">
              <span className="label-caps mb-1.5 block">Klasse</span>
              <select
                value={form.class_name}
                onChange={(event) => setForm({ ...form, class_name: event.target.value })}
                className="w-full rounded-sm border border-rule bg-paper px-3 py-2 text-[14px] focus:outline-none"
              >
                {!meta?.classes.some((item) => item.value === form.class_name) && form.class_name && (
                  <option value={form.class_name}>
                    {classLabel(form.class_name, form.group)}
                  </option>
                )}
                {meta?.classes.map((item) => (
                  <option key={item.value} value={item.value}>{item.label}</option>
                ))}
              </select>
            </label>
            <Input label="Ordnung" value={form.order_name}
              onChange={(v) => setForm({ ...form, order_name: v })} />
            <Input label="Familie" value={form.family}
              onChange={(v) => setForm({ ...form, family: v })} />
            <label className="block">
              <span className="label-caps mb-1.5 block">Schwierigkeit</span>
              <select
                value={form.difficulty}
                onChange={(e) => setForm({ ...form, difficulty: Number(e.target.value) })}
                className="w-full rounded-sm border border-rule bg-paper px-3 py-2 text-[14px] focus:outline-none"
              >
                {meta?.difficulties.map((d) => (
                  <option key={d.value} value={d.value}>
                    {"★".repeat(Number(d.value))} {d.label}
                  </option>
                ))}
              </select>
            </label>
            <Input label="Größe" value={form.size} placeholder="17–19 cm"
              onChange={(v) => setForm({ ...form, size: v })} />
            <Input label="Spannweite" value={form.wingspan}
              onChange={(v) => setForm({ ...form, wingspan: v })} />
            <Input label="Gewicht" value={form.weight}
              onChange={(v) => setForm({ ...form, weight: v })} />
          </div>

          <label className="block">
            <span className="label-caps mb-1.5 block">Beschreibung</span>
            <textarea
              value={form.description}
              onChange={(e) => setForm({ ...form, description: e.target.value })}
              rows={3}
              className="w-full rounded-sm border border-rule bg-paper px-3 py-2 text-[14px] focus:outline-none"
            />
          </label>

          <Chips label="Lebensraum" options={meta?.habitats ?? []} selected={form.habitats}
            onToggle={(v) => toggleList("habitats", v)} />
          <Chips label="Region / Kontinent" options={meta?.regions ?? []} selected={form.regions}
            onToggle={(v) => toggleList("regions", v)} />

          <Chips
            label="Aktivität"
            options={meta?.activities ?? []}
            selected={[form.activity]}
            onToggle={(value) => setForm({ ...form, activity: value as "diurnal" | "nocturnal" })}
          />

          <Chips label="Merkmale" options={meta?.tags ?? []} selected={form.tags}
            onToggle={(v) => toggleList("tags", v)} />

          <Input label="Weitere Merkmale (Komma-getrennt)" value={tagInput}
            onChange={setTagInput} />
          {!editing && (
            <label className="block rounded-sm border border-dashed border-rule-2 bg-paper-2/50 p-4">
              <span className="label-caps mb-1.5 block">Referenzbild (optional)</span>
              <input
                type="file"
                accept="image/*,.heic,.heif,image/heic,image/heif"
                onChange={(event) => setReferenceImage(event.target.files?.[0] ?? null)}
                className="block w-full text-sm text-ink-2 file:mr-3 file:rounded-sm file:border file:border-rule file:bg-paper file:px-3 file:py-2"
              />
              <span className="mt-2 block text-xs text-ink-3">
                {referenceImage ? referenceImage.name : "JPG, PNG, WebP, TIFF oder HEIC/HEIF"}
              </span>
            </label>
          )}
            </>
          )}

          {message && (
            <p className={`text-[13px] ${message.kind === "ok" ? "text-moss-2" : "text-rust"}`}>
              {message.text}
            </p>
          )}

          <button
            type="submit"
            disabled={isSavingSpecies}
            className="rounded-sm bg-moss px-6 py-2.5 text-[15px] text-paper hover:bg-moss-2"
          >
            {isSavingSpecies ? "Wird gespeichert …" : editing ? "Änderungen speichern" : "Anlegen"}
          </button>
        </form>
      </section>

      {/* Liste */}
      <section>
        <SectionTitle right={<span className="text-[13px] text-ink-3">{formatNumber(total)} Arten · letzte Änderung zuerst</span>}>
          Arten bearbeiten
        </SectionTitle>
        <input
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="Art suchen …"
          className="mb-4 w-full max-w-md rounded-sm border border-rule bg-paper px-3 py-2 text-[14px] focus:outline-none"
        />
        <div className="overflow-x-auto">
          <table className="w-full min-w-[640px] border-collapse text-[14px]">
            <thead>
              <tr className="border-b border-rule-2 text-left">
                {["Art", "Klasse", "Familie", "Letzte Änderung", "Fotos", ""].map((h) => (
                  <th key={h} className="label-caps py-2 pr-4 font-semibold">{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {results.map((s) => (
                <tr key={s.id} className="border-b border-rule hover:bg-paper-2/60">
                  <td className="py-2 pr-4">
                    <Link to={`/arten/${s.slug}`} className="link-quiet text-ink">
                      {s.common_name}
                    </Link>
                    <span className="ml-2 font-serif italic text-ink-3">{s.scientific_name}</span>
                  </td>
                  <td className="py-2 pr-4 text-ink-2">{classLabel(s.class_name, s.group)}</td>
                  <td className="py-2 pr-4 text-ink-2">{s.family}</td>
                  <td className="py-2 pr-4 text-ink-3">
                    {s.updated_at ? formatRelativeTime(s.updated_at) : "–"}
                  </td>
                  <td className="py-2 pr-4 text-ink-2">{s.photo_count}</td>
                  <td className="py-2 text-right whitespace-nowrap">
                    <button onClick={() => setSearchParams({ edit: s.slug })} className="text-ink-3 hover:text-ink">
                      Bearbeiten
                    </button>
                    <button onClick={() => remove(s)} className="ml-4 text-ink-3 hover:text-rust">
                      Löschen
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      {/* Backup */}
      <section className="border-t border-rule pt-10">
        <SectionTitle>Backup</SectionTitle>
        <div className="paper-card grid gap-5 rounded-sm p-5 md:grid-cols-2">
          <div>
            <h3 className="font-serif text-xl text-ink">Backup speichern</h3>
            <p className="mt-1.5 text-[14px] leading-6 text-ink-2">
              Sichert den kompletten Stand: alle Profile, Arten, Begegnungen, Fotos,
              Vorschaubilder und Auszeichnungen.
            </p>
            <a
              href={api.backupUrl()}
              className="mt-4 inline-flex rounded-sm bg-moss px-5 py-2.5 text-[14px] text-paper transition hover:bg-moss-2"
            >
              Backup speichern
            </a>
          </div>

          <div className="border-t border-rule pt-5 md:border-l md:border-t-0 md:pl-5 md:pt-0">
            <h3 className="font-serif text-xl text-ink">Backup laden</h3>
            <p className="mt-1.5 text-[14px] leading-6 text-ink-2">
              Stellt einen zuvor gesicherten Gesamtstand wieder her und ersetzt den
              derzeitigen Inhalt vollständig.
            </p>
            <input
              ref={backupRef}
              type="file"
              accept=".wcbackup,.zip,application/zip"
              disabled={backupLoading}
              onChange={(event) => event.target.files?.[0] && loadBackup(event.target.files[0])}
              className="mt-4 block w-full text-[14px] text-ink-2 file:mr-3 file:rounded-sm file:border file:border-rule-2 file:bg-paper-2 file:px-4 file:py-2 file:text-ink-2 hover:file:bg-paper-3 disabled:opacity-50"
            />
          </div>

          {backupInfo && (
            <p className={`md:col-span-2 text-[13px] ${backupError ? "text-rust" : backupLoading ? "text-ochre" : "text-moss-2"}`}>
              {backupInfo}
            </p>
          )}
        </div>
      </section>
    </div>
  );
}

const CLASS_LABEL: Record<string, string> = {
  Aves: "Vögel",
  Mammalia: "Säugetiere",
  Insecta: "Insekten",
  Amphibia: "Amphibien",
  Reptilia: "Reptilien",
  Actinopterygii: "Strahlenflosser",
  Chondrichthyes: "Knorpelfische",
  Arachnida: "Spinnentiere",
  Gastropoda: "Schnecken",
  Malacostraca: "Höhere Krebse",
  Animalia: "Tiere",
};

const GROUP_CLASS_LABEL: Record<string, string> = {
  bird: "Vögel", mammal: "Säugetiere", butterfly: "Insekten", insect: "Insekten",
  amphibian: "Amphibien", reptile: "Reptilien", fish: "Fische", other: "Tiere",
};

function classLabel(value: string, group: string): string {
  return CLASS_LABEL[value] ?? GROUP_CLASS_LABEL[group] ?? "Tiere";
}

function Input({
  label, value, onChange, placeholder, required,
}: {
  label: string; value: string; onChange: (v: string) => void;
  placeholder?: string; required?: boolean;
}) {
  return (
    <label className="block">
      <span className="label-caps mb-1.5 block">{label}</span>
      <input
        value={value}
        required={required}
        placeholder={placeholder}
        onChange={(e) => onChange(e.target.value)}
        className="w-full rounded-sm border border-rule bg-paper px-3 py-2 text-[14px] focus:border-rule-2 focus:outline-none"
      />
    </label>
  );
}

function Chips({
  label, options, selected, onToggle,
}: {
  label: string;
  options: { value: string; label: string }[];
  selected: string[];
  onToggle: (v: string) => void;
}) {
  return (
    <div>
      <span className="label-caps mb-2 block">{label}</span>
      <div className="flex flex-wrap gap-1.5">
        {options.map((o) => (
          <button
            key={o.value}
            type="button"
            onClick={() => onToggle(o.value)}
            className={`rounded-full border px-3 py-1 text-[13px] transition-colors ${
              selected.includes(o.value)
                ? "border-moss bg-moss text-paper"
                : "border-rule bg-paper text-ink-2 hover:bg-paper-2"
            }`}
          >
            {o.label}
          </button>
        ))}
      </div>
    </div>
  );
}
