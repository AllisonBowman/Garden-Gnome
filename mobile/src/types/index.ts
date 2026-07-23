export type LightNeed = 'low' | 'medium' | 'bright_indirect' | 'direct';
export type CareType = 'water' | 'fertilize' | 'mist' | 'prune' | 'repot' | 'rotate' | 'clean' | 'other';
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
  care_notes: string;
  care_schedules?: CareSchedule[];
  traits?: SpeciesTrait[];
}

export interface CareLog {
  id: number;
  plant_id: number;
  action: CareType;
  notes: string;
  logged_at: string;
}

export type MaturityStage = 'seedling' | 'juvenile' | 'mature' | 'flowering';

export interface Plant {
  id: number;
  plant_uuid: string;
  nickname: string;
  species_id: number;
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
