/**
 * TypeScript types for activities and templates
 *
 * Matches backend database schema:
 * - activity_templates table
 * - activities table
 * - exercise_sets table
 * - exercises table
 */

export interface ExerciseTemplate {
  exercise_id: string;
  exercise_name: string;
  target_sets: number;
  target_reps: number;
  target_weight_kg?: number;
  notes?: string;
}

export interface ActivityTemplate {
  id: string;
  user_id: string;
  template_name: string;
  activity_type: string;
  description?: string;
  icon?: string;

  // Expected ranges for auto-matching
  expected_distance_m?: number;
  distance_tolerance_percent?: number;
  expected_duration_minutes?: number;
  duration_tolerance_percent?: number;

  // Pre-filled data
  default_exercises: ExerciseTemplate[];
  default_metrics?: Record<string, any>;
  default_notes?: string;

  // Auto-matching
  auto_match_enabled: boolean;
  min_match_score: number;
  require_gps_match: boolean;

  // Time-based matching
  typical_start_time?: string;
  time_window_hours?: number;
  preferred_days?: number[]; // 1=Monday, 7=Sunday

  // Goals
  target_zone?: string;
  goal_notes?: string;

  // Usage stats
  use_count: number;
  last_used_at?: string;

  // Status
  is_active: boolean;
  created_from_activity_id?: string;
  created_at: string;
  updated_at: string;
}

export interface ExerciseSet {
  id: string;
  activity_id: string;
  exercise_id: string;
  user_id: string;

  // Set details
  set_number: number; // 1, 2, 3, etc.
  reps?: number;
  weight_kg?: number;

  // Time/distance based
  duration_seconds?: number;
  distance_meters?: number;

  // Intensity tracking
  rpe?: number; // Rate of Perceived Exertion (1-10)
  tempo?: string; // e.g., "3-1-2-0"
  rest_seconds?: number;

  // Performance
  completed: boolean;
  failure: boolean; // Taken to failure?
  notes?: string;

  created_at: string;
  updated_at: string;
}

export interface Activity {
  id: string;
  user_id: string;

  // Basic info
  category: string; // cardio_steady_state, strength_training, etc.
  activity_name: string;
  start_time: string;
  end_time?: string;
  duration_minutes: number;

  // Performance metrics
  distance_meters?: number;
  calories_burned?: number;
  average_heart_rate?: number;
  max_heart_rate?: number;

  // Subjective
  perceived_exertion?: number;
  notes?: string;

  // Template linkage
  template_id?: string;
  template_match_score?: number;
  template_applied_at?: string;

  // Strength-specific (legacy JSONB field)
  exercises?: any[];

  // Flexible metrics
  metrics?: Record<string, any>;

  // Source tracking
  source: 'manual' | 'ai_text' | 'ai_voice' | 'garmin' | 'strava' | 'coach_chat';
  ai_confidence?: number;
  ai_cost_usd?: number;

  // Wearable integration
  wearable_activity_id?: string;
  wearable_url?: string;
  device_name?: string;

  // Soft delete
  deleted_at?: string;

  created_at: string;
  updated_at: string;

  // Populated if requested
  exercise_sets?: ExerciseSet[];
}

export interface ActivityWithTemplate extends Activity {
  template?: ActivityTemplate;
}

export interface Exercise {
  id: string;
  name: string;
  description?: string;
  category: string;
  primary_muscle_groups: string[];
  secondary_muscle_groups: string[];
  equipment_needed: string[];
  difficulty_level?: string;
  primary_modalities: string[];
  usage_count: number;
  is_public: boolean;
  verified: boolean;
  created_at: string;
}

export interface PersonalRecord {
  max_weight_kg?: number;
  max_weight_reps?: number;
  max_weight_date?: string;
  max_estimated_1rm?: number;
  max_1rm_date?: string;
  max_set_volume?: number;
  max_volume_date?: string;
}

export interface ExerciseHistory {
  activity_id: string;
  activity_name: string;
  start_time: string;
  set_number: number;
  reps?: number;
  weight_kg?: number;
  rpe?: number;
  estimated_1rm?: number;
  set_volume?: number;
}

export interface WeeklyVolume {
  week_start: string;
  total_activities: number;
  total_sets: number;
  total_volume: number;
  avg_rpe: number;
}

export interface AdherenceMetrics {
  planned_count: number;
  completed_count: number;
  adherence_pct: number;
  completed_with_template: number;
  completed_without_template: number;
  informal_activities: number;
}

// Request/Response types

export interface CreateActivityRequest {
  category: string;
  activity_name: string;
  start_time: string;
  duration_minutes: number;
  template_id?: string;
  calories_burned?: number;
  perceived_exertion?: number;
  notes?: string;
}

export interface CreateExerciseSetRequest {
  activity_id: string;
  exercise_id: string;
  set_number: number;
  reps?: number;
  weight_kg?: number;
  rpe?: number;
  completed: boolean;
  notes?: string;
}

export interface ActivityTemplateListResponse {
  templates: ActivityTemplate[];
  total: number;
}

export interface InformalActivitiesResponse {
  activities: Activity[];
  total: number;
  period_days: number;
}

// Helper functions

export function calculateEstimated1RM(weight: number, reps: number): number {
  // Epley formula: 1RM = weight × (1 + reps / 30)
  if (reps > 10) return weight; // Formula less accurate above 10 reps
  return Math.round(weight * (1 + reps / 30) * 100) / 100;
}

export function calculateSetVolume(weight: number, reps: number): number {
  return Math.round(weight * reps * 100) / 100;
}

export function formatDuration(minutes: number): string {
  if (minutes < 60) return `${minutes}min`;
  const hours = Math.floor(minutes / 60);
  const mins = minutes % 60;
  return `${hours}h ${mins}min`;
}

export function getCategoryIcon(category: string): string {
  const icons: Record<string, string> = {
    cardio_steady_state: '🏃',
    cardio_interval: '🔥',
    strength_training: '💪',
    sports: '⚽',
    flexibility: '🧘',
    other: '🎯'
  };
  return icons[category] || '🏋️';
}

export function getRPELabel(rpe?: number): string {
  if (!rpe) return '';
  if (rpe <= 3) return 'Very Easy';
  if (rpe <= 5) return 'Moderate';
  if (rpe <= 7) return 'Challenging';
  if (rpe <= 9) return 'Very Hard';
  return 'Maximum Effort';
}

export function getRPEColor(rpe?: number): string {
  if (!rpe) return '#dfe6e9';
  if (rpe <= 3) return '#00b894';
  if (rpe <= 5) return '#55efc4';
  if (rpe <= 7) return '#ffeaa7';
  if (rpe <= 9) return '#fdcb6e';
  return '#ff7675';
}
