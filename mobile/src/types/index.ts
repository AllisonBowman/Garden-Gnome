export type LightNeed = 'low' | 'medium' | 'bright_indirect' | 'direct';
export type ReviewStatus = 'approved' | 'needs_review' | 'verified';
export type CareType = 'water' | 'fertilize' | 'mist' | 'prune' | 'repot' | 'rotate' | 'clean' | 'other';
/** What a care to-do ended in. The reminder verb is *check*, so "looked and it
 *  didn't need doing" is a first-class result. Only water and repot take
 *  outcomes; the server refuses mismatched pairs. */
export type CareOutcome = 'watered' | 'checked_not_needed' | 'repotted' | 'top_dressed' | 'checked_fine';
export type EnvironmentType = 'home' | 'nursery' | 'community_garden' | 'conservation' | 'research';

export interface CareSchedule {
  id: number;
  species_id: number;
  care_type: CareType;
  interval_days_min: number;
  interval_days_max: number;
  notes: string;
}

export interface SpeciesTrait {
  id: number;
  species_id: number;
  trait: string;
  value: string;
  unit: string;
}

export interface Species {
  id: number;
  common_name: string;
  scientific_name: string;
  light_need: LightNeed;
  humidity_pct_min: number;
  humidity_pct_max: number;
  temp_f_min: number;
  temp_f_max: number;
  soil_type: string;
  toxic_to_pets: boolean;
  /** Plain-language toxicity sentence derived server-side — names which parts
   *  are toxic, to which animals, and how serious. Prefer this over the bare
   *  flag wherever there is room to show it: "Tomato: toxic" is contradictory
   *  to anyone who eats tomatoes, and a lily and a pothos are not the same
   *  risk. Empty on older API versions, so always fall back to the flag. */
  toxicity_description?: string;
  /** False when the humidity percentages were derived from a watering
   *  category (imported rows) rather than a source. Hide the stat and don't
   *  sort on it. Absent on older API versions — treat as sourced. */
  humidity_sourced?: boolean;
  care_notes: string;
  /** How trustworthy this row's care data is, when a caller happens to know.
   *  Deliberately NOT sent by `GET /species/`: review status, notes and source
   *  are operator state, and a test guards the list schema against leaking
   *  them. Matching uses it as a tiebreak only when it is present — see
   *  `identify-photo`'s `unreviewed_ids`, which is how the server flags
   *  provisional rows without putting the review trail on every species. */
  review_status?: ReviewStatus;
  care_schedules?: CareSchedule[];
  traits?: SpeciesTrait[];
}

export interface CareLog {
  id: number;
  plant_id: number;
  action: CareType;
  /** Null on rows that predate outcomes — the action was simply done. */
  outcome?: CareOutcome | null;
  notes: string;
  logged_at: string;
}

export type MaturityStage = 'seedling' | 'juvenile' | 'mature' | 'flowering';

export interface Plant {
  id: number;
  plant_uuid: string;
  nickname: string;
  species_id: number;
  /** How many physical plants this row stands for. 1 is an individual — a
   *  named houseplant; more is a planting, "twelve tomatoes along the south
   *  fence", which a gardener counts rather than names. Older API versions
   *  omit it, so treat a missing value as 1. */
  quantity?: number;
  /** Set when this row was split off another planting; carries the original's
   *  plant_uuid so the census can tell a rearrangement from new plants. */
  split_from_uuid?: string | null;
  environment_id?: number;
  location: string;
  maturity_stage: MaturityStage;
  acquired_on?: string;
  intake_notes: string;
  species?: Species;
}

export type Shelter = 'sheltered' | 'partial' | 'exposed';
export type TempExposure = 'indoor' | 'outdoor';
export type SunExposure = 'full_sun' | 'partial_sun' | 'shade';

export interface Environment {
  id: number;
  uuid: string;
  name: string;
  type: EnvironmentType;
  city: string;
  region: string;
  country: string;
  lat?: number;
  lng?: number;
  shelter: Shelter;
  temp_exposure: TempExposure;
  sun_exposure: SunExposure;
  created_at: string;
  plant_count: number;
}

export interface WeatherCurrent {
  temp_f: number | null;
  humidity_pct: number | null;
  uv_index: number | null;
  condition: string | null;
}

export interface WeatherDay {
  date: string;
  high_f: number | null;
  low_f: number | null;
  precip_chance_pct: number | null;
  uv_max: number | null;
  sunrise: string | null;
  sunset: string | null;
  daylight_hours: number | null;
  condition: string | null;
}

export interface WeatherAttribution {
  text: string;
  url: string;
}

export interface Weather {
  current: WeatherCurrent;
  daily: WeatherDay[];
  attribution: WeatherAttribution;
}

export interface StewardshipRecord {
  id: number;
  plant_id: number;
  environment_id: number;
  installation_uuid: string;
  started_at: string;
  ended_at?: string;
  transfer_notes: string;
}

export interface CensusSummary {
  total_plants: number;
  total_environments: number;
  environments_by_type: Record<string, number>;
  plants_by_environment_type: Record<string, number>;
  species_distribution: Array<{ species_id: number; common_name: string; count: number }>;
}
