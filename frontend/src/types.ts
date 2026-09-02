export type Status = "locked" | "unlocked";

export interface Profile {
  id: number;
  name: string;
  avatar: string;
  gender: "male" | "female";
  is_default: boolean;
  exclude_captive_from_progress: boolean;
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
  class_name: string;
  family: string;
  difficulty: number;
  regions: string[];
  habitats: string[];
  activity: "diurnal" | "nocturnal";
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
  created_at: string | null;
  updated_at: string | null;
}

export interface Photo {
  id: number;
  species_id: number;
  observation_id: number | null;
  url: string | null;
  thumb_url: string | null;
  original_filename: string;
  date: string | null;
  time: string | null;
  location_name: string;
  caption: string;
  encounter_type: "wild" | "captive";
  is_best_photo: boolean;
  photo_metadata: Record<string, unknown>;
  created_at: string;
}

export interface Observation {
  id: number;
  species_id: number;
  date: string | null;
  time: string | null;
  location_name: string;
  latitude: number | null;
  longitude: number | null;
  notes: string;
  encounter_type: "wild" | "captive";
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
  classes: FacetValue[];
  orders: FacetValue[];
  habitats: FacetValue[];
  regions: FacetValue[];
  families: FacetValue[];
  difficulties: FacetValue[];
  statuses: FacetValue[];
  seen: FacetValue[];
  encounters: FacetValue[];
  activities: FacetValue[];
  tags: FacetValue[];
}

export interface ProgressBucket {
  key: string;
  label: string;
  collected: number;
  total: number;
}

export interface Activity {
  kind: "photographed" | "seen" | "added";
  profile_id: number;
  profile_name: string;
  profile_avatar: string;
  species_id: number;
  species_slug: string;
  species_name: string;
  occurred_at: string;
}

export interface Dashboard {
  total_species: number;
  collected: number;
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
  activity: Activity[];
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
  activities: MetaEntry[];
  tags: MetaEntry[];
  difficulties: MetaEntry[];
  statuses: MetaEntry[];
}
