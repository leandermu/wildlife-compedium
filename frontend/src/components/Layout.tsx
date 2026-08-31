import { NavLink, Outlet, useNavigate } from "react-router-dom";
import { useEffect, useRef, useState } from "react";

const NAV = [
  { to: "/", label: "Kompendium", end: true },
  { to: "/arten", label: "Alle Arten" },
  { to: "/auszeichnungen", label: "Auszeichnungen" },
  { to: "/verwaltung", label: "Verwaltung" },
];

export function Layout() {
  const navigate = useNavigate();
  const [query, setQuery] = useState("");
  const searchRef = useRef<HTMLInputElement>(null);

  // "/" fokussiert die Suche, wie in einem Nachschlagewerk
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      const target = e.target as HTMLElement | null;
      const typing = target && /input|textarea|select/i.test(target.tagName);
      if (e.key === "/" && !typing) {
        e.preventDefault();
        searchRef.current?.focus();
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, []);

  return (
    <div className="flex min-h-screen flex-col">
      <header className="no-print sticky top-0 z-30 border-b border-rule bg-paper/92 backdrop-blur-sm">
        <div className="mx-auto flex max-w-[1400px] flex-wrap items-center gap-x-8 gap-y-3 px-6 py-4">
          <NavLink to="/" className="group flex items-baseline gap-3">
            <span className="font-serif text-[1.6rem] leading-none tracking-tight text-ink">
              Wildlife&nbsp;Compendium
            </span>
            <span className="label-caps hidden sm:inline">Persönliche Sammlung</span>
          </NavLink>

          <nav className="order-3 flex flex-1 flex-wrap items-center gap-6 sm:order-2">
            {NAV.map((item) => (
              <NavLink
                key={item.to}
                to={item.to}
                end={item.end}
                className={({ isActive }) =>
                  `relative py-1 text-[14px] transition-colors ${
                    isActive ? "text-ink" : "text-ink-3 hover:text-ink-2"
                  } after:absolute after:-bottom-0.5 after:left-0 after:h-px after:bg-ochre after:transition-all ${
                    isActive ? "after:w-full" : "after:w-0 hover:after:w-full"
                  }`
                }
              >
                {item.label}
              </NavLink>
            ))}
          </nav>

          <form
            className="order-2 ml-auto sm:order-3"
            onSubmit={(e) => {
              e.preventDefault();
              navigate(`/arten?q=${encodeURIComponent(query.trim())}`);
            }}
          >
            <label className="relative block">
              <span className="sr-only">Arten durchsuchen</span>
              <svg
                viewBox="0 0 16 16"
                className="pointer-events-none absolute left-3 top-1/2 h-3.5 w-3.5 -translate-y-1/2 text-ink-3"
                fill="none"
                stroke="currentColor"
                strokeWidth="1.6"
                aria-hidden
              >
                <circle cx="7" cy="7" r="4.5" />
                <path d="M10.5 10.5 14 14" />
              </svg>
              <input
                ref={searchRef}
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="Art suchen …"
                className="w-52 rounded-full border border-rule bg-paper-2/70 py-1.5 pl-9 pr-3 text-[14px] text-ink placeholder:text-ink-3 focus:w-64 focus:border-rule-2 focus:bg-paper focus:outline-none"
              />
            </label>
          </form>
        </div>
      </header>

      <main className="mx-auto w-full max-w-[1400px] flex-1 px-6 py-8">
        <Outlet />
      </main>

      <footer className="no-print mt-12 border-t border-rule bg-paper-2/40">
        <div className="mx-auto max-w-[1400px] px-6 py-6 text-center">
          <p className="font-serif italic text-ink-3">
            „Ein Tier ist erst durch das eigene Foto wirklich gesammelt."
          </p>
        </div>
      </footer>
    </div>
  );
}
