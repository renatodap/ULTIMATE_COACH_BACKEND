/**
 * Context API Client
 *
 * Provides methods to interact with context endpoints.
 */

import axios from 'axios';
import {
  ContextTimelineResponse,
  ContextSummaryResponse,
  ContextLog,
  LogContextRequest,
  ContextType,
  SeverityLevel
} from '../types/context';
import { InformalActivitiesResponse } from '../types/activity';

// Create axios instance
const api = axios.create({
  baseURL: process.env.REACT_APP_API_BASE_URL || 'http://localhost:8000/api/v1',
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json'
  }
});

// Auth interceptor (same as programApi.ts)
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
 * Context API methods
 */
export const ContextAPI = {
  /**
   * Get user's context timeline
   */
  async getTimeline(userId: string, daysBack: number = 14): Promise<ContextTimelineResponse> {
    const response = await api.get(`/context/timeline/${userId}`, {
      params: { days_back: daysBack }
    });
    return response.data;
  },

  /**
   * Get informal activities extracted from chat
   */
  async getInformalActivities(userId: string, daysBack: number = 14): Promise<InformalActivitiesResponse> {
    const response = await api.get(`/context/informal-activities/${userId}`, {
      params: { days_back: daysBack }
    });
    return response.data;
  },

  /**
   * Get context summary
   */
  async getSummary(userId: string, daysBack: number = 14): Promise<ContextSummaryResponse> {
    const response = await api.get(`/context/summary/${userId}`, {
      params: { days_back: daysBack }
    });
    return response.data;
  },

  /**
   * Get context that affects training
   */
  async getTrainingAffectingContext(userId: string, daysBack: number = 14): Promise<{ context_logs: ContextLog[], total: number }> {
    const response = await api.get(`/context/affects-training/${userId}`, {
      params: { days_back: daysBack }
    });
    return response.data;
  },

  /**
   * Manually log a context event
   */
  async logContext(data: {
    user_id: string;
    context_type: ContextType;
    description: string;
    severity?: SeverityLevel;
    affects_training?: boolean;
    affects_nutrition?: boolean;
  }): Promise<{ success: boolean; context_id: string; message: string }> {
    const response = await api.post('/context/log', data);
    return response.data;
  },

  /**
   * Delete a context log entry
   */
  async deleteContext(contextId: string, userId: string): Promise<{ success: boolean; message: string }> {
    const response = await api.delete(`/context/${contextId}`, {
      params: { user_id: userId }
    });
    return response.data;
  }
};

export default ContextAPI;
