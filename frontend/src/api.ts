import type {
  Achievement, Dashboard, Facets, Meta, Observation, Page, Photo,
  Profile, SpeciesDetail, SpeciesListItem,
} from "./types";

const BASE = import.meta.env.VITE_API_BASE ?? "";

export class ApiError extends Error {
  constructor(message: string, readonly status: number) {
    super(message);
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const headers = new Headers(init?.headers);
  const profileId = localStorage.getItem("wc-profile-id");
  if (profileId) headers.set("X-Profile-ID", profileId);
  const res = await fetch(`${BASE}${path}`, { ...init, headers });
  if (!res.ok) {
    let detail = res.statusText;
    try {
      const body = await res.json();
      detail = typeof body.detail === "string" ? body.detail : JSON.stringify(body.detail);
    } catch {
      /* keep statusText */
    }
    throw new ApiError(detail, res.status);
  }
  if (res.status === 204) return undefined as T;
  return res.json() as Promise<T>;
}

const json = (body: unknown): RequestInit => ({
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify(body),
});

export interface SpeciesQueryParams {
  q?: string;
  group?: string[];
  habitat?: string[];
  region?: string[];
  family?: string[];
  tag?: string[];
  difficulty?: string[];
  status?: string[];
  sort?: string;
  page?: number;
  page_size?: number;
}

export function toSearchParams(params: SpeciesQueryParams): URLSearchParams {
  const sp = new URLSearchParams();
  for (const [key, value] of Object.entries(params)) {
    if (value === undefined || value === null || value === "") continue;
    if (Array.isArray(value)) value.forEach((v) => sp.append(key, String(v)));
    else sp.set(key, String(value));
  }
  return sp;
}

export const api = {
  profiles: () => request<Profile[]>("/api/profiles"),
  createProfile: (name: string) =>
    request<Profile>("/api/profiles", json({ name })),
  updateProfile: (id: number, body: { name?: string; avatar?: string }) =>
    request<Profile>(`/api/profiles/${id}`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    }),
  deleteProfile: (id: number) =>
    request<void>(`/api/profiles/${id}`, { method: "DELETE" }),

  backupUrl: () => `${BASE}/api/backup/save`,
  restoreBackup: (file: File) => {
    const fd = new FormData();
    fd.append("file", file);
    return request<{
      message: string;
      profiles: number;
      species: number;
      observations: number;
      photos: number;
    }>("/api/backup/load", { method: "POST", body: fd });
  },

  meta: () => request<Meta>("/api/meta"),
  dashboard: () => request<Dashboard>("/api/dashboard"),

  species: (params: SpeciesQueryParams) =>
    request<Page<SpeciesListItem>>(`/api/species?${toSearchParams(params)}`),
  facets: (params: SpeciesQueryParams) =>
    request<Facets>(`/api/species/facets?${toSearchParams(params)}`),
  speciesDetail: (key: string) => request<SpeciesDetail>(`/api/species/${key}`),
  createSpecies: (body: Record<string, unknown>) =>
    request<SpeciesDetail>("/api/species", json(body)),
  createSpeciesFromWikipedia: (commonName: string) =>
    request<SpeciesDetail>("/api/species/from-wikipedia", json({ common_name: commonName })),
  updateSpecies: (key: string, body: Record<string, unknown>) =>
    request<SpeciesDetail>(`/api/species/${key}`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    }),
  deleteSpecies: (key: string) =>
    request<void>(`/api/species/${key}`, { method: "DELETE" }),
  uploadPhoto: (fd: FormData) =>
    request<Photo>("/api/photos", { method: "POST", body: fd }),
  updatePhoto: (id: number, body: Record<string, unknown>) =>
    request<Photo>(`/api/photos/${id}`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    }),
  deletePhoto: (id: number) => request<void>(`/api/photos/${id}`, { method: "DELETE" }),

  createObservation: (body: Record<string, unknown>) =>
    request<Observation>("/api/observations", json(body)),
  deleteObservation: (id: number) =>
    request<void>(`/api/observations/${id}`, { method: "DELETE" }),

  achievements: () => request<Achievement[]>("/api/achievements"),

};
