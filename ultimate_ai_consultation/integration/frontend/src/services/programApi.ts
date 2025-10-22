/**
 * Program API Client
 *
 * Provides methods to interact with program, activity, and template endpoints.
 * Uses new activity-based architecture (ActivityTemplate, Activity, ExerciseSet).
 */

import axios from 'axios';
import {
  ActivityTemplate,
  Activity,
  ExerciseSet,
  Exercise,
  CreateActivityRequest,
  CreateExerciseSetRequest,
  ActivityTemplateListResponse,
  PersonalRecord,
  ExerciseHistory,
  WeeklyVolume,
  AdherenceMetrics,
  ActivityWithTemplate
} from '../types/activity';

// Create axios instance
const api = axios.create({
  baseURL: process.env.REACT_APP_API_BASE_URL || 'http://localhost:8000/api/v1',
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json'
  }
});

// Auth interceptor
api.interceptors.request.use(async (config) => {
  // For web
  if (typeof window !== 'undefined' && window.localStorage) {
    const token = localStorage.getItem('auth_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
  }

  // For React Native (user needs to uncomment and install AsyncStorage)
  // import AsyncStorage from '@react-native-async-storage/async-storage';
  // const token = await AsyncStorage.getItem('auth_token');
  // if (token) {
  //   config.headers.Authorization = `Bearer ${token}`;
  // }

  return config;
});

/**
 * Program API methods
 */
export const ProgramAPI = {
  // ============================================
  // Activity Templates
  // ============================================

  /**
   * Get user's active activity templates
   */
  async getActiveTemplates(userId: string): Promise<ActivityTemplateListResponse> {
    const response = await api.get(`/programs/templates/${userId}`);
    return response.data;
  },

  /**
   * Get today's recommended template
   */
  async getTodaysTemplate(userId: string): Promise<ActivityTemplate | null> {
    const response = await api.get(`/programs/templates/${userId}/today`);
    return response.data.template || null;
  },

  /**
   * Get single template by ID
   */
  async getTemplate(templateId: string): Promise<ActivityTemplate> {
    const response = await api.get(`/programs/templates/single/${templateId}`);
    return response.data;
  },

  /**
   * Create new activity template
   */
  async createTemplate(data: {
    user_id: string;
    template_name: string;
    activity_type: string;
    description?: string;
    default_exercises: Array<{
      exercise_id: string;
      exercise_name: string;
      target_sets: number;
      target_reps: number;
      target_weight_kg?: number;
      notes?: string;
    }>;
    auto_match_enabled?: boolean;
    expected_duration_minutes?: number;
  }): Promise<{ success: boolean; template_id: string; message: string }> {
    const response = await api.post('/programs/templates', data);
    return response.data;
  },

  /**
   * Update activity template
   */
  async updateTemplate(
    templateId: string,
    data: Partial<ActivityTemplate>
  ): Promise<{ success: boolean; message: string }> {
    const response = await api.put(`/programs/templates/${templateId}`, data);
    return response.data;
  },

  /**
   * Delete activity template
   */
  async deleteTemplate(templateId: string, userId: string): Promise<{ success: boolean; message: string }> {
    const response = await api.delete(`/programs/templates/${templateId}`, {
      params: { user_id: userId }
    });
    return response.data;
  },

  /**
   * Create template from completed activity
   */
  async createTemplateFromActivity(
    activityId: string,
    templateName: string
  ): Promise<{ success: boolean; template_id: string; message: string }> {
    const response = await api.post('/programs/templates/from-activity', {
      activity_id: activityId,
      template_name: templateName
    });
    return response.data;
  },

  // ============================================
  // Activities
  // ============================================

  /**
   * Get user's activities with optional filters
   */
  async getActivities(params: {
    user_id: string;
    days_back?: number;
    category?: string;
    include_exercise_sets?: boolean;
    include_template?: boolean;
  }): Promise<{ activities: Activity[]; total: number }> {
    const response = await api.get(`/programs/activities/${params.user_id}`, {
      params: {
        days_back: params.days_back,
        category: params.category,
        include_exercise_sets: params.include_exercise_sets,
        include_template: params.include_template
      }
    });
    return response.data;
  },

  /**
   * Get single activity by ID
   */
  async getActivity(activityId: string, includeExerciseSets: boolean = true): Promise<ActivityWithTemplate> {
    const response = await api.get(`/programs/activities/single/${activityId}`, {
      params: { include_exercise_sets: includeExerciseSets }
    });
    return response.data;
  },

  /**
   * Create new activity
   */
  async createActivity(data: CreateActivityRequest): Promise<{ success: boolean; activity_id: string; message: string }> {
    const response = await api.post('/programs/activities', data);
    return response.data;
  },

  /**
   * Update activity
   */
  async updateActivity(
    activityId: string,
    data: Partial<Activity>
  ): Promise<{ success: boolean; message: string }> {
    const response = await api.put(`/programs/activities/${activityId}`, data);
    return response.data;
  },

  /**
   * Delete activity
   */
  async deleteActivity(activityId: string, userId: string): Promise<{ success: boolean; message: string }> {
    const response = await api.delete(`/programs/activities/${activityId}`, {
      params: { user_id: userId }
    });
    return response.data;
  },

  /**
   * Match activity to template
   */
  async matchActivityToTemplate(
    activityId: string,
    templateId: string
  ): Promise<{ success: boolean; match_score: number; message: string }> {
    const response = await api.post('/programs/activities/match-template', {
      activity_id: activityId,
      template_id: templateId
    });
    return response.data;
  },

  // ============================================
  // Exercise Sets
  // ============================================

  /**
   * Create exercise set
   */
  async createExerciseSet(data: CreateExerciseSetRequest): Promise<{ success: boolean; set_id: string; message: string }> {
    const response = await api.post('/programs/exercise-sets', data);
    return response.data;
  },

  /**
   * Create multiple exercise sets (batch)
   */
  async createExerciseSets(
    sets: CreateExerciseSetRequest[]
  ): Promise<{ success: boolean; set_ids: string[]; message: string }> {
    const response = await api.post('/programs/exercise-sets/batch', { sets });
    return response.data;
  },

  /**
   * Update exercise set
   */
  async updateExerciseSet(
    setId: string,
    data: Partial<ExerciseSet>
  ): Promise<{ success: boolean; message: string }> {
    const response = await api.put(`/programs/exercise-sets/${setId}`, data);
    return response.data;
  },

  /**
   * Delete exercise set
   */
  async deleteExerciseSet(setId: string, userId: string): Promise<{ success: boolean; message: string }> {
    const response = await api.delete(`/programs/exercise-sets/${setId}`, {
      params: { user_id: userId }
    });
    return response.data;
  },

  /**
   * Get exercise sets for an activity
   */
  async getExerciseSetsForActivity(activityId: string): Promise<{ exercise_sets: ExerciseSet[] }> {
    const response = await api.get(`/programs/exercise-sets/activity/${activityId}`);
    return response.data;
  },

  // ============================================
  // Exercises
  // ============================================

  /**
   * Search exercises by name
   */
  async searchExercises(query: string, limit: number = 20): Promise<{ exercises: Exercise[] }> {
    const response = await api.get('/programs/exercises/search', {
      params: { q: query, limit }
    });
    return response.data;
  },

  /**
   * Get exercise by ID
   */
  async getExercise(exerciseId: string): Promise<Exercise> {
    const response = await api.get(`/programs/exercises/${exerciseId}`);
    return response.data;
  },

  /**
   * Get popular exercises for user
   */
  async getPopularExercises(userId: string, limit: number = 10): Promise<{ exercises: Exercise[] }> {
    const response = await api.get(`/programs/exercises/popular/${userId}`, {
      params: { limit }
    });
    return response.data;
  },

  // ============================================
  // Analytics & Progress
  // ============================================

  /**
   * Get adherence metrics for period
   */
  async getAdherence(userId: string, daysBack: number = 14): Promise<AdherenceMetrics> {
    const response = await api.get(`/programs/adherence/${userId}`, {
      params: { days_back: daysBack }
    });
    return response.data;
  },

  /**
   * Get exercise history for specific exercise
   */
  async getExerciseHistory(
    userId: string,
    exerciseId: string,
    limit: number = 50
  ): Promise<{ history: ExerciseHistory[] }> {
    const response = await api.get(`/programs/history/${userId}/${exerciseId}`, {
      params: { limit }
    });
    return response.data;
  },

  /**
   * Get personal records for exercise
   */
  async getPersonalRecords(userId: string, exerciseId: string): Promise<PersonalRecord> {
    const response = await api.get(`/programs/personal-records/${userId}/${exerciseId}`);
    return response.data;
  },

  /**
   * Get weekly volume stats
   */
  async getWeeklyVolume(userId: string, weeksBack: number = 12): Promise<{ weeks: WeeklyVolume[] }> {
    const response = await api.get(`/programs/volume/${userId}`, {
      params: { weeks_back: weeksBack }
    });
    return response.data;
  },

  /**
   * Get program generation status
   */
  async getProgramStatus(userId: string): Promise<{
    has_program: boolean;
    program_created_at?: string;
    last_adjustment_at?: string;
    next_reassessment?: string;
    persona_type?: string;
  }> {
    const response = await api.get(`/programs/status/${userId}`);
    return response.data;
  },

  /**
   * Trigger program generation
   */
  async generateProgram(userId: string, consultationData?: any): Promise<{
    success: boolean;
    program_id: string;
    templates_created: number;
    message: string;
  }> {
    const response = await api.post(`/programs/generate/${userId}`, {
      consultation_data: consultationData
    });
    return response.data;
  },

  /**
   * Trigger manual reassessment
   */
  async triggerReassessment(userId: string): Promise<{
    success: boolean;
    adjustment_made: boolean;
    reason: string;
    message: string;
  }> {
    const response = await api.post(`/programs/reassess/${userId}`);
    return response.data;
  }
};

export default ProgramAPI;
