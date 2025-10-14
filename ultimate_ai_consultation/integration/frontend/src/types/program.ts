/**
 * TypeScript Types for Adaptive Program System
 *
 * Drop-in file for: ULTIMATE_COACH_FRONTEND/src/types/program.ts
 *
 * These types match the Pydantic models from backend exactly.
 */

// =============================================================================
// Enums
// =============================================================================

export enum PlanStatus {
  ACTIVE = "active",
  SUPERSEDED = "superseded",
  ARCHIVED = "archived",
}

export enum AdjustmentReason {
  BI_WEEKLY_REASSESSMENT = "bi_weekly_reassessment",
  PROGRESS_TOO_SLOW = "progress_too_slow",
  PROGRESS_TOO_FAST = "progress_too_fast",
  LOW_ADHERENCE = "low_adherence",
  EXCESSIVE_FATIGUE = "excessive_fatigue",
  INJURY_PREVENTION = "injury_prevention",
  MANUAL_TRIGGER = "manual_trigger",
}

export enum SplitType {
  FULL_BODY = "full_body",
  UPPER_LOWER = "upper_lower",
  PUSH_PULL_LEGS = "push_pull_legs",
  BODY_PART_SPLIT = "body_part_split",
}

export enum DayOfWeek {
  MONDAY = "monday",
  TUESDAY = "tuesday",
  WEDNESDAY = "wednesday",
  THURSDAY = "thursday",
  FRIDAY = "friday",
  SATURDAY = "saturday",
  SUNDAY = "sunday",
}

export type TrendDirection = "exceeding" | "on_track" | "slow" | "stalled" | "insufficient_data";

// =============================================================================
// Core Types
// =============================================================================

export interface MacroTargets {
  calories: number;
  protein_g: number;
  carbs_g: number;
  fat_g: number;
  protein_kcal?: number;
  carbs_kcal?: number;
  fat_kcal?: number;
}

export interface ExerciseSet {
  set_number: number;
  reps: number;
  weight_kg?: number;
  rpe?: number;
  rest_seconds: number;
}

export interface Exercise {
  exercise_id: string;
  exercise_name: string;
  muscle_group: string;
  sets: ExerciseSet[];
  total_sets: number;
  notes?: string;
  video_url?: string;
  form_cues: string[];
}

export interface WorkoutSession {
  workout_id: string;
  day_name: string;
  muscle_groups: string[];
  exercises: Exercise[];
  estimated_duration_minutes: number;
  total_sets: number;
  notes?: string;
}

export interface MealItem {
  food_id: string;
  food_name: string;
  quantity: number;
  unit: string;
  calories: number;
  protein_g: number;
  carbs_g: number;
  fat_g: number;
}

export interface Meal {
  meal_id: string;
  meal_name: string;
  meal_number: number;
  foods: MealItem[];
  total_calories: number;
  total_protein_g: number;
  total_carbs_g: number;
  total_fat_g: number;
  prep_time_minutes?: number;
  recipe_url?: string;
}

export interface DayMealPlan {
  day_number: number;
  meals: Meal[];
  daily_totals: MacroTargets;
}

export interface GroceryItem {
  food_name: string;
  quantity: number;
  unit: string;
  category: string;
  estimated_cost_usd?: number;
  notes?: string;
}

// =============================================================================
// API Response Types
// =============================================================================

export interface ProgramSummary {
  plan_id: string;
  user_id: string;
  version: number;
  status: PlanStatus;
  split_type: SplitType;
  workouts_per_week: number;
  estimated_workout_duration: number;
  cycle_length_weeks: number;
  macro_targets: MacroTargets;
  created_at: string;
  valid_from: string;
  valid_until?: string;
  warnings: string[];
  red_flags: string[];
  welcome_message: string;
}

export interface ActivePlanResponse {
  plan_id: string;
  user_id: string;
  version: number;
  status: PlanStatus;
  split_type: SplitType;
  workouts_per_week: number;
  cycle_length_weeks: number;
  current_week: number;
  current_day: number;
  macro_targets: MacroTargets;
  workouts: WorkoutSession[];
  meal_plans: DayMealPlan[];
  valid_from: string;
  valid_until?: string;
  created_at: string;
  grocery_list: GroceryItem[];
  warnings: string[];
  notes?: string;
}

export interface TodayPlanResponse {
  plan_id: string;
  user_id: string;
  today_date: string;
  cycle_day: number;
  cycle_week: number;
  calendar_day: DayOfWeek;
  is_training_day: boolean;
  training_day_number?: number;
  workout?: WorkoutSession;
  meals: Meal[];
  macro_targets: MacroTargets;
  days_until_next_reassessment: number;
  last_reassessment_date?: string;
  suggested_actions: string[];
}

export interface ProgressMetrics {
  start_weight_kg?: number;
  current_weight_kg?: number;
  weight_change_kg?: number;
  weight_change_rate_per_week?: number;
  target_rate_per_week?: number;
  meal_logging_adherence: number;
  training_adherence: number;
  avg_calories_consumed?: number;
  avg_protein_consumed_g?: number;
  calorie_adherence?: number;
  total_sets_completed?: number;
  avg_sets_per_workout?: number;
  days_with_meals_logged: number;
  days_with_workouts_logged: number;
  days_with_weight_logged: number;
  total_days_in_period: number;
}

export interface ProgressResponse {
  user_id: string;
  plan_id: string;
  plan_version: number;
  start_date: string;
  end_date: string;
  days_analyzed: number;
  metrics: ProgressMetrics;
  trend_direction: TrendDirection;
  confidence_score: number;
  red_flags: string[];
  recommendations: string[];
  weight_history: Array<{ date: string; weight_kg: number }>;
  calorie_history: Array<{ date: string; calories: number }>;
}

export interface GroceryListResponse {
  plan_id: string;
  user_id: string;
  generated_at: string;
  items_by_category: Record<string, GroceryItem[]>;
  total_items: number;
  estimated_total_cost_usd?: number;
  covers_days: number;
  notes: string[];
}

export interface AdjustmentRecord {
  adjustment_id: string;
  plan_id: string;
  from_version: number;
  to_version: number;
  calories_before: number;
  calories_after: number;
  volume_before: number;
  volume_after: number;
  adjustment_reason: AdjustmentReason;
  rationale: string;
  created_at: string;
  progress_metrics?: ProgressMetrics;
}

export interface PlanVersion {
  plan_id: string;
  version: number;
  user_id: string;
  status: PlanStatus;
  created_at: string;
  valid_from: string;
  valid_until?: string;
  macro_targets: MacroTargets;
  split_type: SplitType;
  workouts_per_week: number;
  changes_from_previous?: string;
}

export interface PlanHistoryResponse {
  user_id: string;
  current_plan_id: string;
  current_version: number;
  versions: PlanVersion[];
  adjustments: AdjustmentRecord[];
  total_versions: number;
  total_adjustments: number;
  plan_start_date: string;
  days_on_plan: number;
}

// =============================================================================
// Request Types
// =============================================================================

export interface GenerateProgramRequest {
  user_id: string;
  consultation_data: Record<string, any>;
  force_regenerate?: boolean;
}

export interface TriggerReassessmentRequest {
  user_id: string;
  force?: boolean;
}

// =============================================================================
// UI State Types
// =============================================================================

export interface ProgramState {
  activePlan?: ActivePlanResponse;
  todayPlan?: TodayPlanResponse;
  progress?: ProgressResponse;
  groceryList?: GroceryListResponse;
  planHistory?: PlanHistoryResponse;
  loading: boolean;
  error?: string;
  lastUpdated?: Date;
}

export interface WorkoutLog {
  workout_id: string;
  completed_at: Date;
  exercises: Array<{
    exercise_id: string;
    sets: Array<{
      set_number: number;
      reps: number;
      weight_kg?: number;
      rpe?: number;
    }>;
  }>;
  notes?: string;
}

export interface MealLog {
  meal_id: string;
  logged_at: Date;
  foods: Array<{
    food_id: string;
    quantity: number;
  }>;
  substitutions?: string[];
  notes?: string;
}

// =============================================================================
// Helper Types
// =============================================================================

export interface DataPoint {
  date: string;
  value: number;
}

export interface ChartData {
  labels: string[];
  datasets: Array<{
    label: string;
    data: number[];
    color: string;
  }>;
}
