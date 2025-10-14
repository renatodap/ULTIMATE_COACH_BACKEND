/**
 * React Hooks for Program Data Management
 *
 * Drop-in file for: ULTIMATE_COACH_FRONTEND/src/hooks/useProgramData.ts
 *
 * Provides easy data fetching and state management for program features.
 */

import { useState, useEffect, useCallback } from 'react';
import {
  ActivePlanResponse,
  TodayPlanResponse,
  ProgressResponse,
  GroceryListResponse,
  PlanHistoryResponse,
} from '../types/program';
import ProgramAPI from '../services/programApi';

// =============================================================================
// Hook: useActivePlan
// =============================================================================

export function useActivePlan(userId: string) {
  const [data, setData] = useState<ActivePlanResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchData = useCallback(async () => {
    if (!userId) return;

    setLoading(true);
    setError(null);

    try {
      const response = await ProgramAPI.getActivePlan(userId);
      setData(response);
    } catch (err: any) {
      setError(err.response?.data?.message || 'Failed to load active plan');
    } finally {
      setLoading(false);
    }
  }, [userId]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  return { data, loading, error, refetch: fetchData };
}

// =============================================================================
// Hook: useTodayPlan
// =============================================================================

export function useTodayPlan(userId: string) {
  const [data, setData] = useState<TodayPlanResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchData = useCallback(async () => {
    if (!userId) return;

    setLoading(true);
    setError(null);

    try {
      const response = await ProgramAPI.getTodayPlan(userId);
      setData(response);
    } catch (err: any) {
      setError(err.response?.data?.message || 'Failed to load today\'s plan');
    } finally {
      setLoading(false);
    }
  }, [userId]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  return { data, loading, error, refetch: fetchData };
}

// =============================================================================
// Hook: useProgress
// =============================================================================

export function useProgress(userId: string, days: number = 14) {
  const [data, setData] = useState<ProgressResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchData = useCallback(async () => {
    if (!userId) return;

    setLoading(true);
    setError(null);

    try {
      const response = await ProgramAPI.getProgress(userId, days);
      setData(response);
    } catch (err: any) {
      setError(err.response?.data?.message || 'Failed to load progress');
    } finally {
      setLoading(false);
    }
  }, [userId, days]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  return { data, loading, error, refetch: fetchData };
}

// =============================================================================
// Hook: useGroceryList
// =============================================================================

export function useGroceryList(userId: string) {
  const [data, setData] = useState<GroceryListResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchData = useCallback(async () => {
    if (!userId) return;

    setLoading(true);
    setError(null);

    try {
      const response = await ProgramAPI.getGroceryList(userId);
      setData(response);
    } catch (err: any) {
      setError(err.response?.data?.message || 'Failed to load grocery list');
    } finally {
      setLoading(false);
    }
  }, [userId]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  return { data, loading, error, refetch: fetchData };
}

// =============================================================================
// Hook: usePlanHistory
// =============================================================================

export function usePlanHistory(userId: string) {
  const [data, setData] = useState<PlanHistoryResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchData = useCallback(async () => {
    if (!userId) return;

    setLoading(true);
    setError(null);

    try {
      const response = await ProgramAPI.getPlanHistory(userId);
      setData(response);
    } catch (err: any) {
      setError(err.response?.data?.message || 'Failed to load plan history');
    } finally {
      setLoading(false);
    }
  }, [userId]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  return { data, loading, error, refetch: fetchData };
}

// =============================================================================
// Hook: useReassessment
// =============================================================================

export function useReassessment(userId: string) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);

  const trigger = useCallback(
    async (force: boolean = false) => {
      if (!userId) return;

      setLoading(true);
      setError(null);
      setSuccess(false);

      try {
        await ProgramAPI.triggerReassessment({ user_id: userId, force });
        setSuccess(true);
      } catch (err: any) {
        setError(err.response?.data?.message || 'Failed to trigger reassessment');
      } finally {
        setLoading(false);
      }
    },
    [userId]
  );

  return { trigger, loading, error, success };
}

// =============================================================================
// Hook: useHasActivePlan
// =============================================================================

export function useHasActivePlan(userId: string) {
  const [hasActivePlan, setHasActivePlan] = useState<boolean | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!userId) return;

    const checkActivePlan = async () => {
      setLoading(true);
      const result = await ProgramAPI.hasActivePlan(userId);
      setHasActivePlan(result);
      setLoading(false);
    };

    checkActivePlan();
  }, [userId]);

  return { hasActivePlan, loading };
}
