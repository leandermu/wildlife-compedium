export type Status = "locked" | "unlocked" | "mastered";

export interface Profile {
  id: number;
  name: string;
  avatar: string;
  is_default: boolean;
  photo_count: number;
  observation_count: number;
  collected_species: number;
  created_at: string;
}

export interface SpeciesListItem {
  id: number;
  slug: string;
  common_name: string;
  scientific_name: string;
  group: string;
  family: string;
  difficulty: number;
  regions: string[];
  habitats: string[];
  size: string;
  reference_image_url: string | null;
  reference_thumb_url: string | null;
  status: Status;
  photo_count: number;
  observation_count: number;
  best_photo_url: string | null;
  best_photo_thumb_url: string | null;
  display_photo_date: string | null;
  display_photo_location: string;
}

export interface Photo {
  id: number;
  species_id: number;
  observation_id: number | null;
  url: string | null;
  thumb_url: string | null;
  original_filename: string;
  date: string | null;
  location_name: string;
  caption: string;
  is_best_photo: boolean;
  photo_metadata: Record<string, unknown>;
  created_at: string;
}

export interface Observation {
  id: number;
  species_id: number;
  date: string | null;
  location_name: string;
  latitude: number | null;
  longitude: number | null;
  notes: string;
  has_photo: boolean;
  created_at: string;
}

export interface SpeciesDetail extends SpeciesListItem {
  order_name: string;
  description: string;
  wingspan: string;
  weight: string;
  countries: string[];
  tags: string[];
  rarity: string;
  reference_credit: string | null;
  reference_source: string | null;
  distribution_map_url: string | null;
  active: boolean;
  photos: Photo[];
  observations: Observation[];
}

export interface Page<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  pages: number;
}

export interface FacetValue {
  value: string;
  label: string;
  count: number;
  collected: number;
}

export interface Facets {
  groups: FacetValue[];
  habitats: FacetValue[];
  regions: FacetValue[];
  families: FacetValue[];
  difficulties: FacetValue[];
  statuses: FacetValue[];
  tags: FacetValue[];
}

export interface ProgressBucket {
  key: string;
  label: string;
  collected: number;
  total: number;
}

export interface Dashboard {
  total_species: number;
  collected: number;
  mastered: number;
  photo_count: number;
  observation_count: number;
  by_group: ProgressBucket[];
  by_region: ProgressBucket[];
  by_difficulty: ProgressBucket[];
  recent: {
    species_id: number;
    slug: string;
    common_name: string;
    scientific_name: string;
    photo_url: string | null;
    thumb_url: string | null;
    date: string | null;
    location_name: string;
  }[];
  challenges: { label: string; remaining: number; filter: Record<string, string> }[];
  achievements_unlocked: number;
  achievements_total: number;
}

export interface Achievement {
  id: string;
  name: string;
  description: string;
  icon: string;
  kind: "achievement" | "quest";
  category: string;
  progress: number;
  target: number;
  unlocked: boolean;
  unlocked_at: string | null;
  tiers: { threshold: number; label: string; unlocked: boolean }[];
  species: { slug: string; common_name: string; collected: boolean }[];
}

export interface MetaEntry {
  value: string;
  label: string;
  icon?: string;
  singular?: string;
  key?: string;
}

export interface Meta {
  groups: MetaEntry[];
  habitats: MetaEntry[];
  regions: MetaEntry[];
  difficulties: MetaEntry[];
  statuses: MetaEntry[];
}
