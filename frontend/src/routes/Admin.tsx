import { useEffect, useRef, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../api";
import type { Meta, SpeciesDetail, SpeciesListItem } from "../types";
import { SectionTitle } from "../components/ui";
import { formatNumber } from "../lib/format";

const EMPTY = {
  common_name: "", scientific_name: "", group: "bird", family: "", order_name: "",
  description: "", size: "", wingspan: "", weight: "", difficulty: 1,
  habitats: [] as string[], regions: [] as string[], tags: [] as string[],
};

export function AdminPage() {
  const [meta, setMeta] = useState<Meta | null>(null);
  const [form, setForm] = useState({ ...EMPTY });
  const [editing, setEditing] = useState<SpeciesDetail | null>(null);
  const [message, setMessage] = useState<{ kind: "ok" | "err"; text: string } | null>(null);
  const [isImportingWikipedia, setIsImportingWikipedia] = useState(false);
  const [search, setSearch] = useState("");
  const [results, setResults] = useState<SpeciesListItem[]>([]);
  const [total, setTotal] = useState(0);
  const [importInfo, setImportInfo] = useState<string | null>(null);
  const fileRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    api.meta().then(setMeta);
  }, []);

  const refresh = () => {
    api.species({ q: search || undefined, page_size: 24, sort: "name" }).then((r) => {
      setResults(r.items);
      setTotal(r.total);
    });
  };
  useEffect(() => {
    const t = setTimeout(refresh, 250);
    return () => clearTimeout(t);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [search]);

  const toggleList = (key: "habitats" | "regions", value: string) =>
    setForm((f) => ({
      ...f,
      [key]: f[key].includes(value) ? f[key].filter((v) => v !== value) : [...f[key], value],
    }));

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setMessage(null);
    try {
      if (!editing) {
        setIsImportingWikipedia(true);
        const imported = await api.createSpeciesFromWikipedia(form.common_name);
        setMessage({ kind: "ok", text: `„${imported.common_name}" wurde mit Wikipedia-Daten angelegt.` });
        setForm({ ...EMPTY });
        refresh();
        return;
      }
      const payload = {
        ...form,
        difficulty: Number(form.difficulty),
        tags: form.tags,
      };
      await api.updateSpecies(editing.slug, payload);
      setMessage({ kind: "ok", text: `„${form.common_name}" aktualisiert.` });
      setForm({ ...EMPTY });
      setEditing(null);
      refresh();
    } catch (err) {
      setMessage({ kind: "err", text: err instanceof Error ? err.message : "Fehler" });
    } finally {
      setIsImportingWikipedia(false);
    }
  };

  const edit = async (slug: string) => {
    const s = await api.speciesDetail(slug);
    setEditing(s);
    setForm({
      common_name: s.common_name, scientific_name: s.scientific_name, group: s.group,
      family: s.family, order_name: s.order_name, description: s.description,
      size: s.size, wingspan: s.wingspan, weight: s.weight, difficulty: s.difficulty,
      habitats: s.habitats, regions: s.regions, tags: s.tags,
    });
    window.scrollTo({ top: 0, behavior: "smooth" });
  };

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

  const doImport = async (file: File) => {
    setImportInfo("Import läuft …");
    try {
      const r = await api.importFile(file);
      setImportInfo(
        `${r.created} neu, ${r.updated} aktualisiert, ${r.skipped} übersprungen` +
          (r.errors.length ? ` – Fehler: ${r.errors.slice(0, 3).join("; ")}` : ""),
      );
      refresh();
    } catch (err) {
      setImportInfo(err instanceof Error ? err.message : "Import fehlgeschlagen");
    }
    if (fileRef.current) fileRef.current.value = "";
  };

  return (
    <div className="animate-fade-up space-y-12">
      <header className="border-b border-rule pb-6">
        <p className="label-caps">Datenpflege</p>
        <h1 className="mt-2 font-serif text-4xl">Verwaltung</h1>
        <p className="mt-2 text-ink-3">
          Arten anlegen, bearbeiten, importieren und die gesamte Sammlung exportieren.
        </p>
      </header>

      {/* Export */}
      <section>
        <SectionTitle>Sichern &amp; Exportieren</SectionTitle>
        <p className="mb-4 max-w-2xl text-[14px] text-ink-2">
          Die Sammlung soll niemals von dieser App abhängen. Alle Daten lassen sich
          jederzeit vollständig herausziehen.
        </p>
        <div className="flex flex-wrap gap-3">
          {[
            ["ZIP mit allen Fotos", api.exportUrl("zip"), "Vollständige Sicherung"],
            ["Arten als JSON", api.exportUrl("json"), "Komplette Datenbank"],
            ["Arten als CSV", api.exportUrl("csv", "?what=species"), "Für Tabellen"],
            ["Fotos als CSV", api.exportUrl("csv", "?what=photos"), "Fotoliste"],
            ["Begegnungen als CSV", api.exportUrl("csv", "?what=observations"), "Beobachtungen"],
          ].map(([label, href, hint]) => (
            <a
              key={label}
              href={href}
              className="rounded-sm border border-rule bg-paper px-4 py-2.5 transition-colors hover:border-rule-2 hover:bg-paper-2"
            >
              <span className="block text-[14px] text-ink">{label}</span>
              <span className="block text-[12px] text-ink-3">{hint}</span>
            </a>
          ))}
        </div>
      </section>

      {/* Import */}
      <section>
        <SectionTitle>Arten importieren</SectionTitle>
        <div className="paper-card rounded-sm p-5">
          <p className="mb-3 text-[14px] text-ink-2">
            CSV oder JSON mit den Spalten <code>common_name</code>, <code>scientific_name</code>,{" "}
            <code>group</code>, <code>family</code>, <code>habitats</code>,{" "}
            <code>regions</code>, <code>difficulty</code> … Mehrfachwerte per Komma.
            Bestehende Arten werden anhand des Namens aktualisiert.
          </p>
          <input
            ref={fileRef}
            type="file"
            accept=".csv,.json,text/csv,application/json"
            onChange={(e) => e.target.files?.[0] && doImport(e.target.files[0])}
            className="block w-full text-[14px] file:mr-3 file:rounded-sm file:border file:border-rule-2 file:bg-paper-2 file:px-4 file:py-2 file:text-ink-2 hover:file:bg-paper-3"
          />
          {importInfo && <p className="mt-3 text-[13px] text-moss-2">{importInfo}</p>}
        </div>
      </section>

      {/* Formular */}
      <section>
        <SectionTitle
          right={
            editing && (
              <button
                onClick={() => {
                  setEditing(null);
                  setForm({ ...EMPTY });
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
              <p className="max-w-2xl text-[14px] text-ink-2">
                Gib nur den Namen ein. Beschreibung, Einordnung und Referenzbild werden aus
                Wikipedia übernommen; das Bild wird automatisch im Stil des Kompendiums bearbeitet.
              </p>
              <Input label="Name des Tiers *" value={form.common_name} required
                placeholder="z. B. Eisvogel"
                onChange={(v) => setForm({ ...form, common_name: v })} />
            </>
          )}
          {editing && (
            <>
          <div className="grid gap-4 sm:grid-cols-2">
            <Input label="Deutscher Name *" value={form.common_name} required
              onChange={(v) => setForm({ ...form, common_name: v })} />
            <Input label="Wissenschaftlicher Name" value={form.scientific_name}
              onChange={(v) => setForm({ ...form, scientific_name: v })} />
            <label className="block">
              <span className="label-caps mb-1.5 block">Tiergruppe</span>
              <select
                value={form.group}
                onChange={(e) => setForm({ ...form, group: e.target.value })}
                className="w-full rounded-sm border border-rule bg-paper px-3 py-2 text-[14px] focus:outline-none"
              >
                {meta?.groups.map((g) => (
                  <option key={g.value} value={g.value}>{g.label}</option>
                ))}
              </select>
            </label>
            <Input label="Familie" value={form.family}
              onChange={(v) => setForm({ ...form, family: v })} />
            <Input label="Ordnung" value={form.order_name}
              onChange={(v) => setForm({ ...form, order_name: v })} />
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
          <Chips label="Region" options={meta?.regions ?? []} selected={form.regions}
            onToggle={(v) => toggleList("regions", v)} />

          <Input label="Tags (Komma-getrennt)" value={form.tags.join(", ")}
            onChange={(v) => setForm({ ...form, tags: v.split(",").map((t) => t.trim()).filter(Boolean) })} />
            </>
          )}

          {message && (
            <p className={`text-[13px] ${message.kind === "ok" ? "text-moss-2" : "text-rust"}`}>
              {message.text}
            </p>
          )}

          <button
            type="submit"
            disabled={isImportingWikipedia}
            className="rounded-sm bg-moss px-6 py-2.5 text-[15px] text-paper hover:bg-moss-2"
          >
            {isImportingWikipedia ? "Wikipedia wird abgefragt …" : editing ? "Änderungen speichern" : "Von Wikipedia anlegen"}
          </button>
        </form>
      </section>

      {/* Liste */}
      <section>
        <SectionTitle right={<span className="text-[13px] text-ink-3">{formatNumber(total)} Arten insgesamt</span>}>
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
                {["Art", "Gruppe", "Familie", "Schwierigkeit", "Fotos", ""].map((h) => (
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
                  <td className="py-2 pr-4 text-ink-2">{s.group}</td>
                  <td className="py-2 pr-4 text-ink-2">{s.family}</td>
                  <td className="py-2 pr-4 text-ochre">{"★".repeat(s.difficulty)}</td>
                  <td className="py-2 pr-4 text-ink-2">{s.photo_count}</td>
                  <td className="py-2 text-right whitespace-nowrap">
                    <button onClick={() => edit(s.slug)} className="text-ink-3 hover:text-ink">
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
    </div>
  );
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
