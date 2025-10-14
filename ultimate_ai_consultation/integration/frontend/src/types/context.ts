/**
 * TypeScript types for context tracking
 *
 * Matches backend Pydantic models in app/models/context.py
 */

export type ContextType =
  | 'stress'
  | 'energy'
  | 'sleep'
  | 'travel'
  | 'injury'
  | 'illness'
  | 'motivation'
  | 'life_event'
  | 'informal_activity';

export type SeverityLevel = 'low' | 'moderate' | 'high';

export interface ContextLog {
  id: string;
  user_id: string;
  context_type: ContextType;
  severity?: SeverityLevel;
  sentiment_score?: number; // -1.0 to 1.0
  description: string;
  original_message?: string;
  affects_training: boolean;
  affects_nutrition: boolean;
  suggested_adaptation?: string;
  extracted_from_message_id?: string;
  extraction_confidence?: number;
  extraction_model?: string;
  activity_created_id?: string;
  created_at: string; // ISO date string
}

export interface ContextSummary {
  context_type: ContextType;
  count: number;
  avg_severity?: number;
  avg_sentiment?: number;
}

export interface ContextTimelineResponse {
  context_logs: ContextLog[];
  period_summary: Record<ContextType, ContextSummary>;
  total_events: number;
  period_days: number;
}

export interface ContextSummaryResponse {
  total_events: number;
  stress_events: number;
  high_stress_events: number;
  travel_events: number;
  injury_events: number;
  informal_activities: number;
  events_affecting_training: number;
  significant_context: boolean;
  period_days: number;
}

export interface InformalActivityExtraction {
  activity_id?: string;
  activity_type: string;
  duration_minutes: number;
  confidence: number;
}

export interface LifeContextExtraction {
  context_id?: string;
  context_type: ContextType;
  severity?: SeverityLevel;
  sentiment_score?: number;
  confidence: number;
}

export interface MessageContextResult {
  informal_activity?: InformalActivityExtraction;
  life_context?: LifeContextExtraction;
  sentiment_score: number;
}

export interface LogContextRequest {
  user_id: string;
  context_type: ContextType;
  description: string;
  severity?: SeverityLevel;
  affects_training?: boolean;
  affects_nutrition?: boolean;
}

// Helper functions

export function getContextIcon(contextType: ContextType): string {
  const icons: Record<ContextType, string> = {
    stress: '😰',
    energy: '⚡',
    sleep: '😴',
    travel: '✈️',
    injury: '🤕',
    illness: '🤒',
    motivation: '💪',
    life_event: '🎉',
    informal_activity: '🏃'
  };
  return icons[contextType] || '📝';
}

export function getContextColor(contextType: ContextType): string {
  const colors: Record<ContextType, string> = {
    stress: '#ff6b6b',
    energy: '#ffd93d',
    sleep: '#6c5ce7',
    travel: '#74b9ff',
    injury: '#ff7675',
    illness: '#fd79a8',
    motivation: '#00b894',
    life_event: '#a29bfe',
    informal_activity: '#55efc4'
  };
  return colors[contextType] || '#dfe6e9';
}

export function getSeverityLabel(severity?: SeverityLevel): string {
  if (!severity) return '';
  const labels = {
    low: 'Low',
    moderate: 'Moderate',
    high: 'High'
  };
  return labels[severity];
}

export function formatSentiment(score?: number): string {
  if (score === undefined || score === null) return 'Neutral';
  if (score >= 0.5) return 'Very Positive';
  if (score >= 0.2) return 'Positive';
  if (score >= -0.2) return 'Neutral';
  if (score >= -0.5) return 'Negative';
  return 'Very Negative';
}
