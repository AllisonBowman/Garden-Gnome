// The property, site profile, zone, imagery, seasonal plan and vitals
// contract (build spec section 4), typed exactly as the server sends it.
//
// Names and literals are the spec's own. A key the spec marks `?` may be
// null (and is typed `| null`, optional, so a server that leaves it out reads
// the same). Dates are ISO `YYYY-MM-DD` strings; instants are ISO 8601 UTC
// strings. No imports, so anything can use it.

// ── Property ─────────────────────────────────────────────────────────────────

export type LotContent =
  | 'trees_that_drop_leaves' | 'evergreens' | 'shrubs' | 'lawn'
  | 'garden_beds' | 'potted_plants' | 'vegetables' | 'mostly_paved';

export const LOT_CONTENTS: readonly LotContent[] = [
  'trees_that_drop_leaves', 'evergreens', 'shrubs', 'lawn',
  'garden_beds', 'potted_plants', 'vegetables', 'mostly_paved',
];

export type PinSource = 'owner_pin' | 'device_location';

export type FrostBias = 'earlier' | 'later';

export type ProfileStepStatus = 'pending' | 'building' | 'ready' | 'partial' | 'failed';

export interface ProfileStatus {
  fast: ProfileStepStatus;
  background: ProfileStepStatus;
}

export interface Property {
  id: number;
  uuid: string;
  name: string;
  pin_lat: number;
  pin_lng: number;
  pin_source: PinSource;
  city?: string | null;
  region?: string | null;
  country?: string | null;
  timezone?: string | null;
  lot_contents: LotContent[];
  frost_bias?: FrostBias | null;
  whole_lot_zone_id: number;
  profile_status: ProfileStatus;
  created_at: string;
}

export interface PropertyCreate {
  name?: string;
  pin_lat: number;
  pin_lng: number;
  pin_source: PinSource;
  lot_contents?: LotContent[];
}

export interface PropertyPatch {
  name?: string;
  pin_lat?: number;
  pin_lng?: number;
  lot_contents?: LotContent[];
  /** null clears the owner's nudge. */
  frost_bias?: FrostBias | null;
}

// ── Explained values ─────────────────────────────────────────────────────────

/** Degrees. The server stores it as a GeoJSON polygon. */
export interface Box {
  west: number;
  south: number;
  east: number;
  north: number;
}

export interface Source {
  name: string;
  detail?: string | null;
  version?: string | null;
  url?: string | null;
}

export type Confidence =
  | 'you_told_us' | 'you_measured' | 'good_estimate' | 'area_estimate'
  | 'rough_estimate' | 'not_known_yet' | 'neighbourhood_context';

export type ConfidenceLabel =
  | 'You told us' | 'You measured' | 'Good estimate' | 'Area estimate'
  | 'Rough estimate' | 'Not known yet' | 'Neighbourhood context';

/** Each confidence and the label the server pairs it with. */
export const CONFIDENCE_LABELS: Record<Confidence, ConfidenceLabel> = {
  you_told_us: 'You told us',
  you_measured: 'You measured',
  good_estimate: 'Good estimate',
  area_estimate: 'Area estimate',
  rough_estimate: 'Rough estimate',
  not_known_yet: 'Not known yet',
  neighbourhood_context: 'Neighbourhood context',
};

export type Provenance = 'owner' | 'public_map' | 'modelled' | 'default';

/** Every site value and every seasonal event and task carries this shape. */
export interface Explained {
  display: string;
  confidence: Confidence;
  confidence_label: ConfidenceLabel;
  reason: string;
  sources: Source[];
  provenance: Provenance;
}

export type SiteField =
  | 'sun' | 'soil_drainage' | 'water_collects' | 'soil_texture' | 'soil_ph'
  | 'disturbed_soil' | 'slope' | 'facing' | 'flooding' | 'land_cover'
  | 'hardiness_zone' | 'frost_dates';

export type OverrideKind = 'choice' | 'number' | 'none';

export type OverrideMethod = 'tap' | 'measured';

export interface OverrideChoice {
  value: string;
  label: string;
}

export interface SiteValue extends Explained {
  field: SiteField;
  title: string;
  /** JSON value behind `display`; its shape depends on the field. */
  value?: unknown;
  zone_id?: number | null;
  can_override: boolean;
  override_choices: OverrideChoice[];
  override_kind: OverrideKind;
  /** The public-data reading, present only when an owner correction is
   *  showing. */
  public?: { display: string; confidence_label: ConfidenceLabel } | null;
}

export interface SiteProfileZone {
  zone_id: number;
  name: string;
  is_whole_lot: boolean;
  values: SiteValue[];
}

export interface SiteProfile {
  property_id: number;
  status: ProfileStatus;
  updated_at?: string | null;
  values: SiteValue[];
  zones: SiteProfileZone[];
  notes: string[];
}

export interface OverridePut {
  zone_id?: number;
  field: SiteField;
  value: unknown;
  method: OverrideMethod;
}

export interface RefreshAccepted {
  status: string;
}

// ── Zones ────────────────────────────────────────────────────────────────────

export type VegetationType = 'tree' | 'shrub' | 'grass' | 'garden_bed' | 'bare_hardscape';

export type LeafHabit = 'drops_leaves' | 'evergreen' | 'mixed';

export type BoundarySource = 'default' | 'owner';

export interface Zone {
  id: number;
  /** The same number as `id`: a zone is a growing area. */
  growing_area_id: number;
  property_id: number;
  name: string;
  /** Null only for the whole-lot zone, which is a mix (the server sends null). */
  vegetation_type: VegetationType | null;
  is_whole_lot: boolean;
  box?: Box | null;
  boundary_source: BoundarySource;
  leaf_habit?: LeafHabit | null;
  plant_count: number;
  values: SiteValue[];
}

export interface ZoneCreate {
  name?: string;
  vegetation_type: VegetationType;
  box: Box;
  leaf_habit?: LeafHabit;
  /** False when the owner did not draw the box (the approximate whole lot
   *  was used), so the server counts it as the default footprint. */
  drawn?: boolean;
}

export interface ZonePatch {
  name?: string;
  vegetation_type?: VegetationType;
  box?: Box;
  leaf_habit?: LeafHabit;
}

// ── Imagery ──────────────────────────────────────────────────────────────────

export interface Imagery {
  tile_key: string;
  /** Path on our server: GET /imagery/tiles/{tile_key}.jpg */
  image_path: string;
  width: number;
  height: number;
  bounds: Box;
  source: Source;
  captured?: string | null;
  pin?: { lat: number; lng: number } | null;
  default_footprint?: Box | null;
}

// ── Forecast and seasonal plan ───────────────────────────────────────────────

export type FrostRisk = 'none' | 'frost' | 'freeze' | 'hard_freeze';

export interface ForecastDay {
  date: string;
  high_f?: number | null;
  low_f?: number | null;
  precipitation_chance?: number | null;
  summary: string;
  frost_risk: FrostRisk;
}

export interface Forecast {
  provider: string;
  provider_name: string;
  fetched_at: string;
  days: ForecastDay[];
}

export type TaskState = 'open' | 'done' | 'not_needed';

export type AppliesToKind = 'lot' | 'zones' | 'plants';

export interface SeasonTask {
  task_key: string;
  text: string;
  low_impact_note?: string | null;
  reason: string;
  sources: Source[];
  applies_to: { kind: AppliesToKind; ids: number[] };
  state: TaskState;
}

export type SeasonEventType =
  | 'first_frost' | 'first_freeze' | 'hard_freeze' | 'fall_hardening'
  | 'leaf_drop' | 'dormancy' | 'last_frost' | 'spring_emergence'
  | 'tender_plants_out' | 'spring_cleanup';

export type SeasonEventStatus =
  | 'happened' | 'happening' | 'forecast' | 'expected' | 'typically_around'
  | 'done' | 'not_needed';

export type OwnerAction =
  | 'mark_happened' | 'mark_not_yet' | 'mark_done' | 'mark_not_needed' | 'clear';

export interface SeasonWindow {
  start?: string | null;
  end?: string | null;
  text: string;
}

export interface SeasonEvent {
  event_key: string;
  type: SeasonEventType;
  title: string;
  status: SeasonEventStatus;
  window: SeasonWindow;
  explained: Explained;
  tasks: SeasonTask[];
  owner_actions: OwnerAction[];
  sort_date?: string | null;
}

/** `Vitals.season_ahead` sends events without their tasks. */
export type SeasonEventSummary = Omit<SeasonEvent, 'tasks'> & { tasks?: SeasonTask[] };

export type SeasonEventState = 'done' | 'not_needed' | 'happened' | 'not_yet' | 'clear';

export interface SeasonEventPut {
  state: SeasonEventState;
  observed_on?: string;
}

export interface SeasonAlert {
  alert_key: string;
  event_key: string;
  title: string;
  body: string;
  fire_at: string;
  built_from_forecast_at: string;
}

export interface SeasonalPlan {
  property_id: number;
  generated_at: string;
  season_label: string;
  forecast?: Forecast | null;
  events: SeasonEvent[];
  alerts: SeasonAlert[];
  notes: string[];
}

// ── Vitals (Home) ────────────────────────────────────────────────────────────

export type VitalTone = 'ok' | 'watch' | 'act';

export type VitalCardKey =
  | 'weather_now' | 'frost' | 'rain' | 'heat' | 'sun' | 'soil' | 'drainage' | 'season';

export interface VitalCard {
  key: VitalCardKey;
  title: string;
  value_text: string;
  detail: string;
  tone: VitalTone;
  explained?: Explained | null;
  /** A screen name from the build spec's section 6 table. */
  link?: string | null;
}

export interface VitalsWeekItem {
  event_key?: string | null;
  task: SeasonTask;
}

export type VitalSpaceKind = 'zone' | 'space';

export interface VitalSpace {
  growing_area_id: number;
  name: string;
  kind: VitalSpaceKind;
  vegetation_type?: VegetationType | null;
  indoor: boolean;
  plant_count: number;
}

export interface Vitals {
  generated_at: string;
  headline: string;
  property?: Property | null;
  forecast?: Forecast | null;
  cards: VitalCard[];
  this_week: VitalsWeekItem[];
  season_ahead: SeasonEventSummary[];
  spaces: VitalSpace[];
  notes: string[];
  /** The server can add a property (its land routes are on). */
  can_add_land?: boolean;
}
