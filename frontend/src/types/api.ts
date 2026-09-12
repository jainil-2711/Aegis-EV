
export type AuthRole = "grid_operator" | "network_operator" | "ev_driver";

export interface AuthUser {
  id: string;
  email: string;
  display_name: string;
  role: AuthRole;
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface LoginResponse {
  access_token: string;
  token_type: string;
  expires_in: number;
  user: AuthUser;
}
export type DriverPreference = "cheapest" | "greenest" | "balanced" | "immediate";
export type Flexibility = "high" | "medium" | "low" | "non_flexible";
export type SessionStatus = "pending" | "scheduled" | "charging" | "completed" | "cancelled";
export type OperatorObjective = "cheapest" | "greenest" | "balanced";
export type OptimizationStatus = "pending" | "candidate" | "applied" | "superseded" | "rejected";
export type Scenario = "normal" | "high_demand" | "high_renewable" | "low_renewable";
export type GridCondition = "normal" | "high_demand" | "high_renewable" | "low_renewable";
export type SignalOperator = "lte" | "gte";
export type RenewableAvailability = "low" | "medium" | "high";
export type ChargerStatus = "available" | "occupied" | "offline" | "maintenance";
export type ConnectorType = "type2" | "ccs" | "chademo" | "other";

export interface ErrorResponse {
  error: { code: string; message: string };
}

export interface EVLoad {
  current_ev_load_kw: number;
  scheduled_ev_load_kw: number;
  peak_ev_load_kw: number;
}

export interface BeforeAfter {
  before: number;
  after: number;
}

export interface PricingTier {
  condition: GridCondition;
  price_per_kwh: number;
}

export interface PricingRule {
  base_rate: number;
  currency: string;
  tiers: PricingTier[];
}

export interface StationSummary {
  id: string;
  name: string;
  capacity_kw: number;
  charger_count: number;
}

export interface ChargerSummary {
  id: string;
  station_id: string;
  max_power_kw: number;
  connector_type: ConnectorType;
  status: ChargerStatus;
}

export interface StationsResponse {
  stations: StationSummary[];
}

export interface ChargersResponse {
  chargers: ChargerSummary[];
}


export interface GridStatusResponse {
  grid_demand_kw: number;
  grid_capacity_kw: number;
  renewable_generation_kw: number;
  ev_load: EVLoad;
  headroom_kw: number;
}

export interface EnergySlot {
  timestamp: string;
  base_load_kw: number;
  renewable_kw: number;
  grid_capacity_kw: number;
  electricity_price: number;
  carbon_intensity: number;
}

export interface GridForecastResponse {
  slots: EnergySlot[];
}

export interface GridSignal {
  id: string;
  start_time: string;
  end_time: string;
  condition: GridCondition;
  recommended_ev_load_kw: number;
  signal_operator: SignalOperator;
  renewable_availability: RenewableAvailability;
  created_at: string;
}

export interface GridSignalsResponse {
  signals: GridSignal[];
}

export interface GridSignalCreate {
  start_time: string;
  end_time: string;
  condition: GridCondition;
  recommended_ev_load_kw: number;
  signal_operator: SignalOperator;
  renewable_availability: RenewableAvailability;
}

export interface NetworkStatusResponse {
  active_evs: number;
  active_chargers: number;
  ev_load: EVLoad;
  renewable_availability_pct: number;
  grid_demand_kw: number;
  grid_capacity_kw: number;
  renewable_generation_kw: number;
}

export interface NetworkImpactResponse {
  peak_load_kw: BeforeAfter;
  cost: BeforeAfter;
  renewable_share_pct: BeforeAfter;
  co2_kg: BeforeAfter;
  pricing_rule: PricingRule;
  active_optimization_run_id: string;
}

export interface DriverSessionResponse {
  ev_id: string;
  battery_capacity_kwh: number;
  current_soc: number;
  target_soc: number;
  arrival_time: string;
  departure_time: string;
  max_charge_kw: number;
  efficiency: number;
  preference: DriverPreference;
  charger_id: string;
  flexibility: Flexibility;
}

export interface DriverPreferencesUpdate {
  preference: DriverPreference;
  target_soc?: number;
  departure_time?: string;
}

export interface DriverRecommendationResponse {
  optimization_run_id: string;
  window_start: string;
  window_end: string;
  estimated_cost: number;
  price_per_kwh: number;
  renewable_share_pct: number;
  co2_impact_kg: number;
  green_score?: number | null;
  why: string;
}

export interface ScheduleAcceptRequest {
  optimization_run_id: string;
}

export interface ScheduleAcceptResponse {
  ev_id: string;
  accepted: boolean;
  status: SessionStatus;
}

export interface ScheduleOverrideRequest {
  requested_power_kw?: number;
  requested_start_time?: string;
  reason?: string;
}

export interface ScheduleOverrideResponse {
  ev_id: string;
  overridden: boolean;
  status: SessionStatus;
  feasible: boolean;
  explanation?: string | null;
  alternatives?: string[] | null;
}

export interface DriverSessionStatusResponse {
  status: SessionStatus;
  current_soc: number;
  charging_power_kw: number;
  renewable_share_pct: number;
  grid_share_pct: number;
  cost_so_far: number;
  co2_kg_so_far: number;
  green_score?: number | null;
  simulated: boolean;
  updated_at: string;
}

export interface OptimizationRunRequest {
  mode: OperatorObjective;
  scenario?: Scenario;
}

export interface ChargingScheduleEntry {
  ev_id: string;
  timestamp: string;
  charging_power_kw: number;
  energy_kwh: number;
  renewable_energy_kwh: number;
  grid_energy_kwh: number;
  cost: number;
  co2_kg: number;
}

export interface OptimizationMetrics {
  peak_kw: number;
  cost: number;
  renewable_share_pct: number;
  co2_kg: number;
}

export interface OptimizationRunResponse {
  id: string;
  status: OptimizationStatus;
  mode: OperatorObjective;
  created_at: string;
  baseline: OptimizationMetrics;
  candidate: OptimizationMetrics;
  schedule: ChargingScheduleEntry[];
}

export interface OptimizationApplyRequest {
  optimization_run_id: string;
}

export interface OptimizationApplyResponse {
  id: string;
  status: OptimizationStatus;
  applied_at: string;
  superseded_run_id?: string | null;
}


export interface OptimizationScheduleResponse {
  optimization_run_id: string;
  status: OptimizationStatus;
  entries: ChargingScheduleEntry[];
}
