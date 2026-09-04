import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { api, type SpeciesQueryParams } from "../api";
import type { Facets, SpeciesListItem } from "../types";
import { SpeciesCard, SpeciesCardSkeleton } from "../components/SpeciesCard";
import { Empty, Pill } from "../components/ui";
import { formatNumber } from "../lib/format";

const PAGE_SIZE = 48;

const MULTI_KEYS = [
  "group", "class_name", "order", "habitat", "region", "family", "tag",
  "difficulty", "status", "seen", "encounter", "activity",
] as const;
type MultiKey = (typeof MULTI_KEYS)[number];

const SORTS = [
  { value: "default", label: "Systematisch" },
  { value: "name", label: "Name A–Z" },
  { value: "difficulty", label: "Leicht zuerst" },
  { value: "difficulty_desc", label: "Schwer zuerst" },
  { value: "collected_first", label: "Zuerst gesammelt" },
  { value: "collected_last", label: "Zuletzt gesammelt" },
  { value: "recent", label: "Zuletzt eingetragen" },
];

export function SpeciesList() {
  const [searchParams, setSearchParams] = useSearchParams();
  const [items, setItems] = useState<SpeciesListItem[]>([]);
  const [total, setTotal] = useState(0);
  const [pages, setPages] = useState(1);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);
  const [loadingMore, setLoadingMore] = useState(false);
  const [facets, setFacets] = useState<Facets | null>(null);
  const [queryInput, setQueryInput] = useState(searchParams.get("q") ?? "");
  const [mobileFiltersOpen, setMobileFiltersOpen] = useState(false);
  const [isShared, setIsShared] = useState(false);
  const requestId = useRef(0);

  useEffect(() => {
    api.profiles().then((profiles) => {
      const activeId = localStorage.getItem("wc-profile-id");
      setIsShared(Boolean(
        profiles.find((profile) => String(profile.id) === activeId)?.is_shared,
      ));
    }).catch(() => setIsShared(false));
  }, []);

  const filters = useMemo<SpeciesQueryParams>(() => {
    const out: SpeciesQueryParams = {};
    const q = searchParams.get("q");
    if (q) out.q = q;
    for (const key of MULTI_KEYS) {
      const values = searchParams.getAll(key);
      if (values.length) out[key] = values;
    }
    out.sort = searchParams.get("sort") ?? "default";
    return out;
  }, [searchParams]);

  // Suchfeld folgt der URL (z. B. bei Suche aus der Kopfzeile)
  useEffect(() => setQueryInput(searchParams.get("q") ?? ""), [searchParams]);

  // Taxonomische Filter bilden eine Hierarchie. Untergeordnete Werte dürfen
  // nicht unsichtbar aktiv bleiben, wenn ihre übergeordnete Auswahl fehlt.
  useEffect(() => {
    const next = new URLSearchParams(searchParams);
    let changed = false;
    if (!next.has("class_name") && (next.has("order") || next.has("family"))) {
      next.delete("order");
      next.delete("family");
      changed = true;
    } else if (!next.has("order") && next.has("family")) {
      next.delete("family");
      changed = true;
    }
    if (changed) setSearchParams(next, { replace: true });
  }, [searchParams, setSearchParams]);

  // Debounce der Sucheingabe
  useEffect(() => {
    const current = searchParams.get("q") ?? "";
    if (queryInput === current) return;
    const timer = setTimeout(() => {
      const next = new URLSearchParams(searchParams);
      if (queryInput.trim()) next.set("q", queryInput.trim());
      else next.delete("q");
      setSearchParams(next, { replace: true });
    }, 250);
    return () => clearTimeout(timer);
  }, [queryInput, searchParams, setSearchParams]);

  useEffect(() => {
    const id = ++requestId.current;
    setLoading(true);
    setPage(1);
    api
      .species({ ...filters, page: 1, page_size: PAGE_SIZE })
      .then((res) => {
        if (id !== requestId.current) return;
        setItems(res.items);
        setTotal(res.total);
        setPages(res.pages);
      })
      .finally(() => id === requestId.current && setLoading(false));
    api.facets(filters).then((f) => id === requestId.current && setFacets(f));
  }, [filters]);

  const loadMore = useCallback(() => {
    const next = page + 1;
    setLoadingMore(true);
    api
      .species({ ...filters, page: next, page_size: PAGE_SIZE })
      .then((res) => {
        setItems((prev) => [...prev, ...res.items]);
        setPage(next);
      })
      .finally(() => setLoadingMore(false));
  }, [filters, page]);

  const toggle = (key: MultiKey, value: string) => {
    const next = new URLSearchParams(searchParams);
    if (key === "class_name") {
      next.delete("order");
      next.delete("family");
    } else if (key === "order") {
      next.delete("family");
    }
    const values = next.getAll(key);
    next.delete(key);
    const remaining = values.includes(value)
      ? values.filter((v) => v !== value)
      : [...values, value];
    remaining.forEach((v) => next.append(key, v));
    setSearchParams(next);
  };

  const activeCount = MULTI_KEYS.reduce((n, k) => n + searchParams.getAll(k).length, 0);

  const collected = items.filter((i) => i.status !== "locked").length;
  const hasClassFilter = searchParams.has("class_name");
  const hasOrderFilter = searchParams.has("order");

  const facetLabels = useMemo(() => {
    const labels = new Map<string, string>();
    if (!facets) return labels;
    for (const [key, values] of Object.entries(facets)) {
      for (const value of values) labels.set(`${key}:${value.value}`, value.label);
    }
    return labels;
  }, [facets]);

  const facetProperty: Record<MultiKey, keyof Facets> = {
    group: "groups", habitat: "habitats", region: "regions", family: "families",
    tag: "tags", difficulty: "difficulties", status: "statuses", seen: "seen",
    encounter: "encounters", class_name: "classes", order: "orders", activity: "activities",
  };

  return (
    <div className="grid gap-8 lg:grid-cols-[16rem_1fr]">
      <div className="no-print space-y-3 lg:hidden">
        <div className="flex items-center gap-3">
          <button
            type="button"
            onClick={() => setMobileFiltersOpen((open) => !open)}
            className="inline-flex items-center gap-2 rounded-full border border-rule-2 bg-paper px-4 py-2 text-sm text-ink-2"
            aria-expanded={mobileFiltersOpen}
          >
            <span aria-hidden>☰</span> Filter {activeCount > 0 && `(${activeCount})`}
          </button>
        </div>
        {activeCount > 0 && (
          <div className="flex flex-wrap gap-1.5">
            {MULTI_KEYS.flatMap((key) => searchParams.getAll(key).map((value) => (
              <button
                key={`${key}-${value}`}
                type="button"
                onClick={() => toggle(key, value)}
                className="rounded-full border border-sage bg-sage/10 px-3 py-1 text-xs text-ink-2"
              >
                {facetLabels.get(`${facetProperty[key]}:${value}`) ?? value} ×
              </button>
            )))}
          </div>
        )}
      </div>
      {/* Filterspalte */}
      <aside className={`no-print space-y-7 ${mobileFiltersOpen ? "block" : "hidden"} lg:sticky lg:top-24 lg:block lg:max-h-[calc(100vh-8rem)] lg:self-start lg:overflow-y-auto lg:pr-2`}>
        <div>
          <label className="label-caps mb-2 block">Suche</label>
          <input
            value={queryInput}
            onChange={(e) => setQueryInput(e.target.value)}
            placeholder="Name, Familie, Art …"
            className="w-full rounded-sm border border-rule bg-paper px-3 py-2 text-[14px] focus:border-rule-2 focus:outline-none"
          />
          <p className="mt-1.5 text-[12px] text-ink-3">
            Umlaute egal: „maus" findet „Mäusebussard".
          </p>
        </div>

        {facets && (
          <>
            <StatusFacetGroup
              statuses={facets.statuses}
              seen={facets.seen}
              searchParams={searchParams}
              toggle={toggle}
            />
            <FacetGroup title="Begegnungsart" k="encounter" facets={facets.encounters} searchParams={searchParams} toggle={toggle} />
            <FacetGroup title="Schwierigkeit" k="difficulty" facets={facets.difficulties} searchParams={searchParams} toggle={toggle} />
            <FacetGroup title="Klasse" k="class_name" facets={facets.classes} searchParams={searchParams} toggle={toggle} />
            {hasClassFilter && (
              <FacetGroup title="Ordnung" k="order" facets={facets.orders} searchParams={searchParams} toggle={toggle} />
            )}
            {hasOrderFilter && (
              <FacetGroup title="Familie" k="family" facets={facets.families.slice(0, 18)} searchParams={searchParams} toggle={toggle} />
            )}
            <FacetGroup title="Region" k="region" facets={facets.regions} searchParams={searchParams} toggle={toggle} />
            <FacetGroup title="Lebensraum" k="habitat" facets={facets.habitats} searchParams={searchParams} toggle={toggle} />
            <FacetGroup title="Aktivität" k="activity" facets={facets.activities} searchParams={searchParams} toggle={toggle} />
            {facets.tags.length > 0 && (
              <FacetGroup title="Merkmale" k="tag" facets={facets.tags.slice(0, 16)} searchParams={searchParams} toggle={toggle} />
            )}
          </>
        )}
      </aside>

      {/* Ergebnisse */}
      <section>
        <div className="mb-5 flex flex-wrap items-baseline justify-between gap-4 border-b border-rule pb-4">
          <div>
            <h1 className="font-serif text-3xl">
              {searchParams.get("q") ? `„${searchParams.get("q")}"` : "Alle Arten"}
            </h1>
            <p className="mt-1 text-sm text-ink-3">
              {formatNumber(total)} {total === 1 ? "Art" : "Arten"}
              {items.length > 0 && ` · ${collected} davon auf dieser Seite gesammelt`}
            </p>
          </div>
          <label className="no-print flex items-center gap-2 text-[13px] text-ink-3">
            Sortierung
            <select
              value={filters.sort}
              onChange={(e) => {
                const next = new URLSearchParams(searchParams);
                next.set("sort", e.target.value);
                setSearchParams(next);
              }}
              className="rounded-sm border border-rule bg-paper px-2 py-1 text-ink-2 focus:outline-none"
            >
              {SORTS.map((s) => (
                <option key={s.value} value={s.value}>
                  {s.label}
                </option>
              ))}
            </select>
          </label>
        </div>

        {loading ? (
          <div className="grid grid-cols-2 gap-5 sm:grid-cols-3 xl:grid-cols-4">
            {Array.from({ length: 8 }, (_, i) => (
              <SpeciesCardSkeleton key={i} />
            ))}
          </div>
        ) : items.length === 0 ? (
          <Empty
            title="Keine Art gefunden"
            hint="Andere Schreibweise probieren, Filter einzeln entfernen oder oben „Alle Arten“ öffnen."
          />
        ) : (
          <>
            <div className="grid grid-cols-2 gap-5 sm:grid-cols-3 xl:grid-cols-4">
              {items.map((s) => (
                <SpeciesCard
                  key={s.id}
                  species={s}
                  listSearch={searchParams.toString()}
                  showPhotographers={isShared}
                />
              ))}
            </div>
            {page < pages && (
              <div className="mt-10 text-center">
                <button
                  onClick={loadMore}
                  disabled={loadingMore}
                  className="rounded-full border border-rule-2 bg-paper px-6 py-2.5 text-sm text-ink-2 transition-colors hover:bg-paper-2 disabled:opacity-50"
                >
                  {loadingMore
                    ? "Lädt …"
                    : `Weitere ${Math.min(PAGE_SIZE, total - items.length)} Arten laden`}
                </button>
                <p className="mt-2 text-[12px] text-ink-3">
                  {items.length} von {formatNumber(total)}
                </p>
              </div>
            )}
          </>
        )}
      </section>
    </div>
  );
}

function StatusFacetGroup({
  statuses,
  seen,
  searchParams,
  toggle,
}: {
  statuses: Facets["statuses"];
  seen: Facets["seen"];
  searchParams: URLSearchParams;
  toggle: (k: MultiKey, v: string) => void;
}) {
  const activeStatus = searchParams.getAll("status");
  const activeSeen = searchParams.getAll("seen");
  return (
    <div>
      <h3 className="label-caps mb-2.5">Status</h3>
      <div className="flex flex-wrap gap-1.5">
        {statuses.map((facet) => (
          <Pill
            key={`status-${facet.value}`}
            active={activeStatus.includes(facet.value)}
            onClick={() => toggle("status", facet.value)}
            count={facet.count}
          >
            {facet.label}
          </Pill>
        ))}
        {seen.map((facet) => (
          <Pill
            key={`seen-${facet.value}`}
            active={activeSeen.includes(facet.value)}
            onClick={() => toggle("seen", facet.value)}
            count={facet.count}
          >
            {facet.label}
          </Pill>
        ))}
      </div>
    </div>
  );
}

function FacetGroup({
  title,
  k,
  facets,
  searchParams,
  toggle,
}: {
  title: string;
  k: MultiKey;
  facets: { value: string; label: string; count: number; collected: number }[];
  searchParams: URLSearchParams;
  toggle: (k: MultiKey, v: string) => void;
}) {
  if (facets.length === 0) return null;
  const active = searchParams.getAll(k);
  return (
    <div>
      <h3 className="label-caps mb-2.5">{title}</h3>
      <div className="flex flex-wrap gap-1.5">
        {facets.map((f) => (
          <Pill
            key={f.value}
            active={active.includes(f.value)}
            onClick={() => toggle(k, f.value)}
            count={f.count}
          >
            {f.label}
          </Pill>
        ))}
      </div>
    </div>
  );
}
