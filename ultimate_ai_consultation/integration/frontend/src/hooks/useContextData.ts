/**
 * React hooks for context data
 *
 * Custom hooks for fetching and managing context-related data.
 */

import { useState, useEffect } from 'react';
import { ContextAPI } from '../services/contextApi';
import {
  ContextTimelineResponse,
  ContextSummaryResponse,
  ContextLog
} from '../types/context';
import { InformalActivitiesResponse } from '../types/activity';

/**
 * Hook to fetch context timeline
 */
export function useContextTimeline(userId: string, daysBack: number = 14) {
  const [data, setData] = useState<ContextTimelineResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<Error | null>(null);

  useEffect(() => {
    let mounted = true;

    const fetchTimeline = async () => {
      try {
        setLoading(true);
        const response = await ContextAPI.getTimeline(userId, daysBack);
        if (mounted) {
          setData(response);
          setError(null);
        }
      } catch (err) {
        if (mounted) {
          setError(err as Error);
        }
      } finally {
        if (mounted) {
          setLoading(false);
        }
      }
    };

    fetchTimeline();

    return () => {
      mounted = false;
    };
  }, [userId, daysBack]);

  return { data, loading, error };
}

/**
 * Hook to fetch informal activities
 */
export function useInformalActivities(userId: string, daysBack: number = 14) {
  const [data, setData] = useState<InformalActivitiesResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<Error | null>(null);

  useEffect(() => {
    let mounted = true;

    const fetchActivities = async () => {
      try {
        setLoading(true);
        const response = await ContextAPI.getInformalActivities(userId, daysBack);
        if (mounted) {
          setData(response);
          setError(null);
        }
      } catch (err) {
        if (mounted) {
          setError(err as Error);
        }
      } finally {
        if (mounted) {
          setLoading(false);
        }
      }
    };

    fetchActivities();

    return () => {
      mounted = false;
    };
  }, [userId, daysBack]);

  return { data, loading, error };
}

/**
 * Hook to fetch context summary
 */
export function useContextSummary(userId: string, daysBack: number = 14) {
  const [data, setData] = useState<ContextSummaryResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<Error | null>(null);

  useEffect(() => {
    let mounted = true;

    const fetchSummary = async () => {
      try {
        setLoading(true);
        const response = await ContextAPI.getSummary(userId, daysBack);
        if (mounted) {
          setData(response);
          setError(null);
        }
      } catch (err) {
        if (mounted) {
          setError(err as Error);
        }
      } finally {
        if (mounted) {
          setLoading(false);
        }
      }
    };

    fetchSummary();

    return () => {
      mounted = false;
    };
  }, [userId, daysBack]);

  return { data, loading, error };
}

/**
 * Hook to fetch training-affecting context
 */
export function useTrainingAffectingContext(userId: string, daysBack: number = 14) {
  const [data, setData] = useState<ContextLog[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<Error | null>(null);

  useEffect(() => {
    let mounted = true;

    const fetchContext = async () => {
      try {
        setLoading(true);
        const response = await ContextAPI.getTrainingAffectingContext(userId, daysBack);
        if (mounted) {
          setData(response.context_logs);
          setError(null);
        }
      } catch (err) {
        if (mounted) {
          setError(err as Error);
        }
      } finally {
        if (mounted) {
          setLoading(false);
        }
      }
    };

    fetchContext();

    return () => {
      mounted = false;
    };
  }, [userId, daysBack]);

  return { data, loading, error };
}
