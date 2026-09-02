import { NavLink, Outlet, useNavigate } from "react-router-dom";
import { useEffect, useRef, useState } from "react";
import { api } from "../api";
import type { Profile } from "../types";

const NAV = [
  { to: "/arten", label: "Alle Arten" },
  { to: "/auszeichnungen", label: "Auszeichnungen" },
  { to: "/verwaltung", label: "Verwaltung" },
];

const PROFILE_AVATARS = ["🐾", "🦊", "🦉", "🦌", "🐦", "🦋", "🐺", "🌿", "📷"];

export function Layout() {
  const navigate = useNavigate();
  const [query, setQuery] = useState("");
  const [profiles, setProfiles] = useState<Profile[]>([]);
  const [profileId, setProfileId] = useState(localStorage.getItem("wc-profile-id") ?? "");
  const [profileMenuOpen, setProfileMenuOpen] = useState(false);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [profileView, setProfileView] = useState<"profiles" | "settings">("profiles");
  const [newProfileName, setNewProfileName] = useState("");
  const [settingsName, setSettingsName] = useState("");
  const [settingsAvatar, setSettingsAvatar] = useState("🐾");
  const [settingsGender, setSettingsGender] = useState<"male" | "female">("male");
  const [settingsExcludeCaptive, setSettingsExcludeCaptive] = useState(false);
  const [profileSaving, setProfileSaving] = useState(false);
  const searchRef = useRef<HTMLInputElement>(null);
  const profileMenuRef = useRef<HTMLDivElement>(null);

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

  useEffect(() => {
    api.profiles().then((items) => {
      setProfiles(items);
      const selected = items.find((profile) => String(profile.id) === profileId);
      if (!selected && items.length) {
        const fallback = items.find((profile) => profile.is_default) ?? items[0];
        localStorage.setItem("wc-profile-id", String(fallback.id));
        setProfileId(String(fallback.id));
        if (profileId) window.location.reload();
      }
    });
  }, [profileId]);

  useEffect(() => {
    if (!profileMenuOpen) return;
    const closeOutside = (event: MouseEvent) => {
      if (!profileMenuRef.current?.contains(event.target as Node)) setProfileMenuOpen(false);
    };
    const closeWithEscape = (event: KeyboardEvent) => {
      if (event.key === "Escape") setProfileMenuOpen(false);
    };
    document.addEventListener("mousedown", closeOutside);
    document.addEventListener("keydown", closeWithEscape);
    return () => {
      document.removeEventListener("mousedown", closeOutside);
      document.removeEventListener("keydown", closeWithEscape);
    };
  }, [profileMenuOpen]);

  const switchProfile = (id: string) => {
    setProfileMenuOpen(false);
    if (id === profileId) return;
    localStorage.setItem("wc-profile-id", id);
    setProfileId(id);
    window.location.reload();
  };

  const addProfile = async (event: React.FormEvent) => {
    event.preventDefault();
    const name = newProfileName.trim();
    if (!name) return;
    setProfileSaving(true);
    try {
      const profile = await api.createProfile(name);
      localStorage.setItem("wc-profile-id", String(profile.id));
      window.location.reload();
    } catch (error) {
      alert(error instanceof Error ? error.message : "Profil konnte nicht angelegt werden.");
      setProfileSaving(false);
    }
  };

  const activeProfile = profiles.find((profile) => String(profile.id) === profileId);
  const canDeleteProfile = Boolean(
    activeProfile &&
    profiles.length > 1 &&
    activeProfile.photo_count === 0 &&
    activeProfile.observation_count === 0,
  );

  const removeProfile = async () => {
    if (!activeProfile || !canDeleteProfile) return;
    if (!confirm(`Das leere Profil „${activeProfile.name}“ wirklich löschen?`)) return;
    try {
      await api.deleteProfile(activeProfile.id);
      const remaining = profiles.filter((profile) => profile.id !== activeProfile.id);
      const fallback = remaining.find((profile) => profile.is_default) ?? remaining[0];
      if (fallback) localStorage.setItem("wc-profile-id", String(fallback.id));
      window.location.reload();
    } catch (error) {
      alert(error instanceof Error ? error.message : "Profil konnte nicht gelöscht werden.");
    }
  };

  const openProfileSettings = () => {
    if (!activeProfile) return;
    setSettingsName(activeProfile.name);
    setSettingsAvatar(activeProfile.avatar || "🐾");
    setSettingsGender(activeProfile.gender || "male");
    setSettingsExcludeCaptive(activeProfile.exclude_captive_from_progress);
    setProfileView("settings");
  };

  const saveProfile = async (event: React.FormEvent) => {
    event.preventDefault();
    if (!activeProfile || !settingsName.trim()) return;
    setProfileSaving(true);
    try {
      const updated = await api.updateProfile(activeProfile.id, {
        name: settingsName.trim(),
        avatar: settingsAvatar,
        gender: settingsGender,
        exclude_captive_from_progress: settingsExcludeCaptive,
      });
      setProfiles((items) => items.map((item) => item.id === updated.id ? updated : item));
      window.location.reload();
    } catch (error) {
      alert(error instanceof Error ? error.message : "Profil konnte nicht gespeichert werden.");
    } finally {
      setProfileSaving(false);
    }
  };

  return (
    <div className="flex min-h-screen flex-col">
      <header className="no-print sticky top-0 z-30 border-b border-rule bg-paper/92 backdrop-blur-sm">
        <div className="mx-auto flex max-w-[1400px] flex-wrap items-center gap-x-3 gap-y-3 px-4 py-3 sm:gap-x-7 sm:px-6 sm:py-4">
          <NavLink to="/" className="group">
            <span className="font-serif text-[1.25rem] leading-none tracking-tight text-ink sm:text-[1.6rem]">
              Wildlife&nbsp;Compedium
            </span>
          </NavLink>

          <nav className="order-3 hidden items-center gap-6 sm:order-2 sm:flex">
            {NAV.map((item) => (
              <NavLink
                key={item.to}
                to={item.to}
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
            className="order-2 ml-auto hidden sm:order-3 sm:block"
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

          <div ref={profileMenuRef} className="relative order-2 ml-auto sm:order-3 sm:ml-0">
            <button
              type="button"
              onClick={() => {
                setMobileMenuOpen(false);
                setProfileView("profiles");
                setProfileMenuOpen((open) => !open);
              }}
              aria-label="Profilmenü öffnen"
              aria-expanded={profileMenuOpen}
              className="flex items-center gap-2 rounded-full border border-rule bg-paper-2/70 py-1 pl-1 pr-2.5 text-left transition hover:border-rule-2 hover:bg-paper"
            >
              <span className="flex h-8 w-8 items-center justify-center rounded-full bg-sage/20 text-lg" aria-hidden>
                {activeProfile?.avatar || "🐾"}
              </span>
              <span className="hidden max-w-28 truncate text-[13px] font-medium text-ink lg:block">
                {activeProfile?.name || "Profil"}
              </span>
              <svg viewBox="0 0 12 12" className={`h-3 w-3 text-ink-3 transition ${profileMenuOpen ? "rotate-180" : ""}`} fill="none" stroke="currentColor" strokeWidth="1.4" aria-hidden>
                <path d="m2.5 4.5 3.5 3 3.5-3" />
              </svg>
            </button>

            {profileMenuOpen && (
              <div className="fixed left-4 right-4 top-[4.5rem] overflow-hidden rounded-2xl border border-rule bg-paper shadow-xl shadow-ink/10 sm:absolute sm:left-auto sm:right-0 sm:top-full sm:mt-3 sm:w-80">
                {profileView === "profiles" ? (
                  <>
                    <div className="border-b border-rule px-4 py-3">
                      <p className="font-serif text-lg text-ink">Profile</p>
                      <p className="mt-0.5 text-xs text-ink-3">Fortschritt und Fotos getrennt sammeln</p>
                    </div>

                    <div className="max-h-64 space-y-1 overflow-y-auto p-2">
                      {profiles.map((profile) => {
                        const selected = String(profile.id) === profileId;
                        return (
                          <button
                            key={profile.id}
                            type="button"
                            onClick={() => switchProfile(String(profile.id))}
                            className={`flex w-full items-center gap-3 rounded-xl px-3 py-2.5 text-left transition ${selected ? "bg-sage/15" : "hover:bg-paper-2"}`}
                          >
                            <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-paper-3 text-lg" aria-hidden>
                              {profile.avatar || "🐾"}
                            </span>
                            <span className="min-w-0 flex-1">
                              <span className="block truncate text-sm font-medium text-ink">{profile.name}</span>
                              <span className="block text-xs text-ink-3">
                                {profile.collected_species} {profile.collected_species === 1 ? "Art" : "Arten"} gesammelt
                              </span>
                            </span>
                            {selected && (
                              <svg viewBox="0 0 16 16" className="h-4 w-4 shrink-0 text-sage" fill="none" stroke="currentColor" strokeWidth="1.8" aria-label="Aktiv">
                                <path d="m3 8 3 3 7-7" />
                              </svg>
                            )}
                          </button>
                        );
                      })}
                    </div>

                    <form onSubmit={addProfile} className="flex gap-2 border-t border-rule px-3 py-3">
                      <input
                        value={newProfileName}
                        onChange={(event) => setNewProfileName(event.target.value)}
                        placeholder="Neues Profil …"
                        maxLength={80}
                        aria-label="Name des neuen Profils"
                        className="min-w-0 flex-1 rounded-lg border border-rule bg-paper-2 px-3 py-2 text-sm text-ink placeholder:text-ink-3 focus:border-rule-2 focus:bg-paper focus:outline-none"
                      />
                      <button
                        type="submit"
                        disabled={!newProfileName.trim() || profileSaving}
                        className="rounded-lg bg-ink px-3 py-2 text-sm text-paper transition hover:bg-ink-2 disabled:cursor-not-allowed disabled:opacity-40"
                      >
                        Anlegen
                      </button>
                    </form>

                    <div className="border-t border-rule bg-paper-2/45 p-2">
                      <button
                        type="button"
                        onClick={openProfileSettings}
                        disabled={!activeProfile}
                        className="flex w-full items-center gap-2 rounded-lg px-3 py-2 text-sm text-ink-2 transition hover:bg-paper-3 disabled:opacity-40"
                      >
                        <svg viewBox="0 0 16 16" className="h-4 w-4" fill="none" stroke="currentColor" strokeWidth="1.3" aria-hidden>
                          <circle cx="8" cy="8" r="2.2" />
                          <path d="M6.6 2.2h2.8l.4 1.5 1.3.8 1.5-.5 1.4 2.4-1.1 1.1v1.4l1.1 1.1-1.4 2.4-1.5-.5-1.3.8-.4 1.5H6.6l-.4-1.5-1.3-.8-1.5.5L2 10l1.1-1.1V7.5L2 6.4 3.4 4l1.5.5 1.3-.8.4-1.5Z" />
                        </svg>
                        Aktives Profil bearbeiten
                      </button>
                    </div>
                  </>
                ) : (
                  <form onSubmit={saveProfile}>
                    <div className="flex items-center gap-3 border-b border-rule px-4 py-3">
                      <button
                        type="button"
                        onClick={() => setProfileView("profiles")}
                        className="flex h-8 w-8 items-center justify-center rounded-full text-ink-3 transition hover:bg-paper-3 hover:text-ink"
                        aria-label="Zurück zur Profilauswahl"
                      >
                        <svg viewBox="0 0 16 16" className="h-4 w-4" fill="none" stroke="currentColor" strokeWidth="1.5" aria-hidden>
                          <path d="m10.5 3-5 5 5 5" />
                        </svg>
                      </button>
                      <div>
                        <p className="font-serif text-lg text-ink">Profileinstellungen</p>
                        <p className="text-xs text-ink-3">{activeProfile?.name}</p>
                      </div>
                    </div>

                    <div className="space-y-5 p-4">
                      <fieldset>
                        <legend className="label-caps mb-2">Profilbild</legend>
                        <div className="grid grid-cols-5 gap-2">
                          {PROFILE_AVATARS.map((avatar) => (
                            <button
                              key={avatar}
                              type="button"
                              onClick={() => setSettingsAvatar(avatar)}
                              aria-label={`Profilbild ${avatar} wählen`}
                              aria-pressed={settingsAvatar === avatar}
                              className={`flex aspect-square items-center justify-center rounded-full border text-xl transition ${settingsAvatar === avatar ? "border-sage bg-sage/20 ring-2 ring-sage/20" : "border-rule bg-paper-2 hover:border-rule-2 hover:bg-paper-3"}`}
                            >
                              {avatar}
                            </button>
                          ))}
                        </div>
                      </fieldset>

                      <label className="block">
                        <span className="label-caps mb-1.5 block">Name</span>
                        <input
                          value={settingsName}
                          onChange={(event) => setSettingsName(event.target.value)}
                          maxLength={80}
                          required
                          className="w-full rounded-lg border border-rule bg-paper-2 px-3 py-2 text-sm text-ink focus:border-rule-2 focus:bg-paper focus:outline-none"
                        />
                      </label>

                      <fieldset>
                        <legend className="label-caps mb-2">Anrede für Auszeichnungen</legend>
                        <div className="grid grid-cols-2 gap-2 rounded-xl bg-paper-2 p-1">
                          {(["male", "female"] as const).map((gender) => (
                            <button
                              key={gender}
                              type="button"
                              onClick={() => setSettingsGender(gender)}
                              aria-pressed={settingsGender === gender}
                              className={`rounded-lg px-3 py-2 text-sm transition ${settingsGender === gender ? "bg-paper text-ink shadow-sm" : "text-ink-3 hover:text-ink-2"}`}
                            >
                              {gender === "male" ? "Männlich" : "Weiblich"}
                            </button>
                          ))}
                        </div>
                        <p className="mt-1.5 text-[11px] text-ink-3">
                          Passt Namen wie Alpenjäger oder Alpenjägerin an.
                        </p>
                      </fieldset>

                      <label className="flex cursor-pointer items-start gap-3 rounded-xl border border-rule bg-paper-2/60 p-3">
                        <input
                          type="checkbox"
                          checked={settingsExcludeCaptive}
                          onChange={(event) => setSettingsExcludeCaptive(event.target.checked)}
                          className="mt-0.5 h-4 w-4 accent-[var(--color-moss)]"
                        />
                        <span>
                          <span className="block text-sm font-medium text-ink">
                            Gefangenschaft nicht werten
                          </span>
                          <span className="mt-1 block text-[11px] leading-4 text-ink-3">
                            Fotos und Begegnungen in Gefangenschaft bleiben sichtbar und filterbar,
                            zählen aber nicht zum Compedium-Fortschritt oder zu Auszeichnungen.
                          </span>
                        </span>
                      </label>

                      <button
                        type="submit"
                        disabled={!settingsName.trim() || profileSaving}
                        className="w-full rounded-lg bg-ink px-4 py-2.5 text-sm text-paper transition hover:bg-ink-2 disabled:cursor-not-allowed disabled:opacity-40"
                      >
                        {profileSaving ? "Wird gespeichert …" : "Änderungen speichern"}
                      </button>
                    </div>

                    <div className="border-t border-rule bg-rust/5 p-4">
                      <button
                        type="button"
                        onClick={removeProfile}
                        disabled={!canDeleteProfile}
                        className="w-full rounded-lg border border-rust/30 px-4 py-2 text-sm text-rust transition hover:border-rust hover:bg-rust/5 disabled:cursor-not-allowed disabled:border-rule disabled:text-ink-3 disabled:opacity-60"
                      >
                        Profil löschen
                      </button>
                      <p className="mt-2 text-center text-[11px] leading-4 text-ink-3">
                        {profiles.length <= 1
                          ? "Das einzige Profil kann nicht gelöscht werden."
                          : canDeleteProfile
                            ? "Nur dieses leere Profil wird entfernt."
                            : "Löschen ist nur ohne Fotos und Begegnungen möglich."}
                      </p>
                    </div>
                  </form>
                )}
              </div>
            )}
          </div>

          <button
            type="button"
            onClick={() => {
              setProfileMenuOpen(false);
              setMobileMenuOpen((open) => !open);
            }}
            className="order-2 flex h-10 w-10 items-center justify-center rounded-full border border-rule bg-paper-2/70 text-ink-2 sm:hidden"
            aria-label={mobileMenuOpen ? "Menü schließen" : "Menü öffnen"}
            aria-expanded={mobileMenuOpen}
          >
            {mobileMenuOpen ? (
              <svg viewBox="0 0 18 18" className="h-5 w-5" fill="none" stroke="currentColor" strokeWidth="1.5" aria-hidden>
                <path d="m4 4 10 10M14 4 4 14" />
              </svg>
            ) : (
              <svg viewBox="0 0 18 18" className="h-5 w-5" fill="none" stroke="currentColor" strokeWidth="1.5" aria-hidden>
                <path d="M3 5h12M3 9h12M3 13h12" />
              </svg>
            )}
          </button>

          {mobileMenuOpen && (
            <div className="order-3 w-full border-t border-rule pt-3 sm:hidden">
              <form
                onSubmit={(event) => {
                  event.preventDefault();
                  setMobileMenuOpen(false);
                  navigate(`/arten?q=${encodeURIComponent(query.trim())}`);
                }}
              >
                <label className="relative block">
                  <span className="sr-only">Arten durchsuchen</span>
                  <svg viewBox="0 0 16 16" className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-ink-3" fill="none" stroke="currentColor" strokeWidth="1.6" aria-hidden>
                    <circle cx="7" cy="7" r="4.5" />
                    <path d="M10.5 10.5 14 14" />
                  </svg>
                  <input
                    value={query}
                    onChange={(event) => setQuery(event.target.value)}
                    placeholder="Art suchen …"
                    className="w-full rounded-full border border-rule bg-paper-2/70 py-2.5 pl-10 pr-4 text-[15px] text-ink placeholder:text-ink-3 focus:border-rule-2 focus:bg-paper focus:outline-none"
                  />
                </label>
              </form>
              <nav className="mt-3 grid grid-cols-3 gap-1">
                {NAV.map((item) => (
                  <NavLink
                    key={item.to}
                    to={item.to}
                    onClick={() => setMobileMenuOpen(false)}
                    className={({ isActive }) =>
                      `rounded-lg px-2 py-2.5 text-center text-[13px] transition ${isActive ? "bg-sage/15 text-ink" : "text-ink-3 hover:bg-paper-2 hover:text-ink-2"}`
                    }
                  >
                    {item.label}
                  </NavLink>
                ))}
              </nav>
            </div>
          )}
        </div>
      </header>

      <main className="mx-auto w-full max-w-[1400px] flex-1 px-4 py-6 sm:px-6 sm:py-8">
        <Outlet />
      </main>

      <footer className="no-print mt-12 border-t border-rule bg-paper-2/40">
        <div className="mx-auto max-w-[1400px] px-6 py-6 text-center">
          <p className="font-serif italic text-ink-3">
            „Ein Tier ist erst durch das eigene Foto wirklich gesammelt."
          </p>
          <p className="mt-2 text-[11px] tracking-wide text-ink-3">v1.4.0</p>
        </div>
      </footer>
    </div>
  );
}
