export type LightNeed = 'low' | 'medium' | 'bright_indirect' | 'direct';

// --- Resolved care values ---------------------------------------------------
// The claim graph settles these per species (ADR 0001); each mirrors a backend
// enum by name. They are column values, not copy: a screen never shows one
// raw, it goes through `care/facts.ts` for the caretaker's wording.

/** How the medium is managed — the species-level fact authorities publish.
 *  A day count is an estimate over pot and light and sits beside this. */
export type WaterRegime = 'keep_moist' | 'keep_barely_moist' | 'dry_surface_between' | 'dry_thoroughly_between';
/** A category, not a percentage: sources disagree by up to 40 points on a
 *  number, and nobody can act on the difference. */
export type HumidityNeed = 'low' | 'average' | 'high';
export type SoilBase =
  | 'standard_potting' | 'chunky_aroid' | 'cactus_succulent' | 'ericaceous'
  | 'orchid_bark' | 'african_violet' | 'semi_hydro' | 'garden_bed';
export type SoilDrainage = 'fast' | 'moderate' | 'moisture_retentive';
export type FertilizeStrength = 'full' | 'half' | 'quarter';
/** The outdoor duration scale, kept apart from indoor light intensity — there
 *  is no honest mapping from hours of sun to a room's light level. */
export type OutdoorSunExposure = 'full_sun' | 'part_sun' | 'part_shade' | 'full_shade';
/** How well-backed a species' care values are: at least one value cited to
 *  the species itself, every value borrowed from its genus, or nothing. A
 *  property of the data, deliberately not the review workflow's status. */
export type CareDataStatus = 'sourced' | 'inferred' | 'none';
/** Per field: cited to this species, or borrowed from its genus (ADR 0002,
 *  which wants the borrowed ones labelled wherever they show). */
export type CareProvenance = 'sourced' | 'genus_inferred';

/** Who said so, as much as a client may see: the authority's name, the page,
 *  and which fields that page settled. Never the supporting passage
 *  (ADR 0003). `inferred` marks a page whose every field came in at genus
 *  scope. */
export interface CareSource {
  authority: string;
  url: string;
  fields: string[];
  inferred: boolean;
}
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
  /** The tranche's accepted name when it differs from `scientific_name` —
   *  how a row held under an older name is linked to its evidence. Never a
   *  rename; `scientific_name` stays what users and toxicity key on. */
  scientific_name_accepted?: string | null;
  /** The legacy care columns. Null on a row minted from the claim tranche
   *  (ADR 0005), and absent from the list endpoint when null — so every
   *  reader goes through `care/facts.ts`, which shows a legacy value only
   *  where no resolved counterpart exists. */
  light_need?: LightNeed | null;
  humidity_pct_min?: number | null;
  humidity_pct_max?: number | null;
  temp_f_min?: number | null;
  temp_f_max?: number | null;
  soil_type?: string | null;
  /** Null means "no record", never "safe" (ADR 0002). Truthiness is the only
   *  test a screen should apply: a chip for true, nothing otherwise. */
  toxic_to_pets?: boolean | null;
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
  /** Derived by the recompute (ADR 0001): how well-backed the values below
   *  are, and per field whether it was cited to this species or borrowed
   *  from its genus. Absent on rows the recompute has not reached. */
  care_data_status?: CareDataStatus | null;
  care_provenance?: Record<string, CareProvenance> | null;
  /** The pages the resolved values came from. Detail endpoint only — the
   *  list omits it, so "absent" is not "uncited". */
  care_sources?: CareSource[];
  /** The resolved care columns, exactly as the claims settled them. Each is
   *  absent or null until a claim resolves it; nothing here is ever a
   *  default. */
  light_fc_min?: number | null;
  light_fc_good?: number | null;
  direct_sun_hours_max?: number | null;
  outdoor_sun_exposure?: OutdoorSunExposure[] | null;
  water_regime?: WaterRegime | null;
  water_check_depth_cm?: number | null;
  /** Estimates, and the tranche carries a half-day — so a float. */
  water_growing_days_est?: number | null;
  water_dormant_days_est?: number | null;
  humidity_need?: HumidityNeed | null;
  day_f_min?: number | null;
  day_f_max?: number | null;
  night_f_min?: number | null;
  night_f_max?: number | null;
  chill_damage_f?: number | null;
  soil_base?: SoilBase | null;
  soil_drainage?: SoilDrainage | null;
  soil_ph_min?: number | null;
  soil_ph_max?: number | null;
  /** Month numbers, 1–12, in no promised order. */
  fertilize_active_months?: number[] | null;
  fertilize_interval_days?: number | null;
  fertilize_strength?: FertilizeStrength | null;
  hardiness_zones?: number[] | null;
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
