/**
 * InformalActivityCard Component
 *
 * Displays AI-extracted activities from chat messages
 * (e.g., "played tennis today", "went for a long walk")
 */

import React from 'react';
import { View, Text, StyleSheet, TouchableOpacity } from 'react-native';
import {
  Activity,
  formatDuration,
  getCategoryIcon,
  getRPELabel,
  getRPEColor
} from '../types/activity';

interface Props {
  activity: Activity;
  showDetails?: boolean;
  onPress?: () => void;
}

export function InformalActivityCard({ activity, showDetails = false, onPress }: Props) {
  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));

    if (diffDays === 0) return 'Today';
    if (diffDays === 1) return 'Yesterday';
    if (diffDays < 7) return `${diffDays} days ago`;
    return date.toLocaleDateString();
  };

  const getSourceLabel = (source: Activity['source']): string => {
    const labels = {
      coach_chat: 'From Coach Chat',
      ai_text: 'AI Extracted (Text)',
      ai_voice: 'AI Extracted (Voice)',
      manual: 'Manual Entry',
      garmin: 'Garmin',
      strava: 'Strava'
    };
    return labels[source] || 'Unknown';
  };

  const getSourceIcon = (source: Activity['source']): string => {
    const icons = {
      coach_chat: '💬',
      ai_text: '🤖',
      ai_voice: '🎤',
      manual: '✍️',
      garmin: '⌚',
      strava: '🏃'
    };
    return icons[source] || '📝';
  };

  const containerStyle = onPress ? styles.containerTouchable : styles.container;

  const CardContent = (
    <View style={containerStyle}>
      {/* Header */}
      <View style={styles.header}>
        <View style={styles.headerLeft}>
          <Text style={styles.categoryIcon}>{getCategoryIcon(activity.category)}</Text>
          <View>
            <Text style={styles.activityName}>{activity.activity_name}</Text>
            <Text style={styles.date}>{formatDate(activity.start_time)}</Text>
          </View>
        </View>
        <View style={styles.headerRight}>
          <Text style={styles.sourceIcon}>{getSourceIcon(activity.source)}</Text>
        </View>
      </View>

      {/* Metrics */}
      <View style={styles.metrics}>
        <View style={styles.metricItem}>
          <Text style={styles.metricLabel}>Duration</Text>
          <Text style={styles.metricValue}>{formatDuration(activity.duration_minutes)}</Text>
        </View>

        {activity.distance_meters && (
          <View style={styles.metricItem}>
            <Text style={styles.metricLabel}>Distance</Text>
            <Text style={styles.metricValue}>
              {(activity.distance_meters / 1000).toFixed(2)} km
            </Text>
          </View>
        )}

        {activity.calories_burned && (
          <View style={styles.metricItem}>
            <Text style={styles.metricLabel}>Calories</Text>
            <Text style={styles.metricValue}>{activity.calories_burned} kcal</Text>
          </View>
        )}

        {activity.perceived_exertion && (
          <View style={styles.metricItem}>
            <Text style={styles.metricLabel}>RPE</Text>
            <View
              style={[
                styles.rpebadge,
                { backgroundColor: getRPEColor(activity.perceived_exertion) }
              ]}
            >
              <Text style={styles.rpeBadgeText}>{activity.perceived_exertion}</Text>
            </View>
          </View>
        )}
      </View>

      {/* Notes (original message) */}
      {activity.notes && showDetails && (
        <View style={styles.notesContainer}>
          <Text style={styles.notesLabel}>Original Message:</Text>
          <Text style={styles.notes}>"{activity.notes}"</Text>
        </View>
      )}

      {/* Tags */}
      <View style={styles.tags}>
        <View style={styles.tag}>
          <Text style={styles.tagText}>{getSourceLabel(activity.source)}</Text>
        </View>

        {activity.template_id && activity.template_match_score && (
          <View style={[styles.tag, styles.tagMatched]}>
            <Text style={styles.tagText}>
              Matched ({Math.round(activity.template_match_score * 100)}%)
            </Text>
          </View>
        )}

        {activity.ai_confidence !== undefined && activity.ai_confidence < 1.0 && (
          <View style={[styles.tag, styles.tagConfidence]}>
            <Text style={styles.tagText}>
              {Math.round(activity.ai_confidence * 100)}% confidence
            </Text>
          </View>
        )}
      </View>

      {/* Template match info */}
      {activity.template_id && showDetails && (
        <View style={styles.templateMatch}>
          <Text style={styles.templateMatchLabel}>✓ Matched to workout template</Text>
          {activity.template_match_score && (
            <Text style={styles.templateMatchScore}>
              Match score: {Math.round(activity.template_match_score * 100)}%
            </Text>
          )}
        </View>
      )}

      {/* Low confidence warning */}
      {activity.ai_confidence !== undefined && activity.ai_confidence < 0.7 && (
        <View style={styles.warningBanner}>
          <Text style={styles.warningText}>
            ⚠️ Low confidence extraction. Please verify details.
          </Text>
        </View>
      )}
    </View>
  );

  if (onPress) {
    return (
      <TouchableOpacity onPress={onPress} activeOpacity={0.7}>
        {CardContent}
      </TouchableOpacity>
    );
  }

  return CardContent;
}

const styles = StyleSheet.create({
  container: {
    backgroundColor: 'white',
    borderRadius: 12,
    padding: 16,
    marginVertical: 8,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
    borderLeftWidth: 4,
    borderLeftColor: '#00b894',
  },
  containerTouchable: {
    backgroundColor: 'white',
    borderRadius: 12,
    padding: 16,
    marginVertical: 8,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
    borderLeftWidth: 4,
    borderLeftColor: '#00b894',
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    marginBottom: 12,
  },
  headerLeft: {
    flexDirection: 'row',
    alignItems: 'center',
    flex: 1,
  },
  headerRight: {
    marginLeft: 8,
  },
  categoryIcon: {
    fontSize: 32,
    marginRight: 12,
  },
  activityName: {
    fontSize: 16,
    fontWeight: '700',
    color: '#2d3436',
    marginBottom: 2,
  },
  date: {
    fontSize: 13,
    color: '#b2bec3',
  },
  sourceIcon: {
    fontSize: 20,
  },
  metrics: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    marginBottom: 12,
  },
  metricItem: {
    marginRight: 20,
    marginBottom: 8,
  },
  metricLabel: {
    fontSize: 11,
    color: '#636e72',
    textTransform: 'uppercase',
    fontWeight: '600',
    marginBottom: 2,
  },
  metricValue: {
    fontSize: 15,
    color: '#2d3436',
    fontWeight: '600',
  },
  rpebadge: {
    paddingHorizontal: 8,
    paddingVertical: 2,
    borderRadius: 4,
    marginTop: 2,
  },
  rpeBadgeText: {
    fontSize: 14,
    fontWeight: '700',
    color: '#2d3436',
  },
  notesContainer: {
    backgroundColor: '#f8f9fa',
    padding: 10,
    borderRadius: 8,
    marginBottom: 12,
  },
  notesLabel: {
    fontSize: 11,
    fontWeight: '600',
    color: '#636e72',
    marginBottom: 4,
    textTransform: 'uppercase',
  },
  notes: {
    fontSize: 13,
    color: '#2d3436',
    fontStyle: 'italic',
    lineHeight: 18,
  },
  tags: {
    flexDirection: 'row',
    flexWrap: 'wrap',
  },
  tag: {
    backgroundColor: '#e8f4fd',
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 4,
    marginRight: 6,
    marginBottom: 6,
  },
  tagMatched: {
    backgroundColor: '#d4edda',
  },
  tagConfidence: {
    backgroundColor: '#fff3cd',
  },
  tagText: {
    fontSize: 11,
    fontWeight: '600',
    color: '#2d3436',
  },
  templateMatch: {
    marginTop: 8,
    paddingTop: 8,
    borderTopWidth: 1,
    borderTopColor: '#dfe6e9',
  },
  templateMatchLabel: {
    fontSize: 12,
    fontWeight: '600',
    color: '#00b894',
    marginBottom: 2,
  },
  templateMatchScore: {
    fontSize: 11,
    color: '#636e72',
  },
  warningBanner: {
    backgroundColor: '#fff3cd',
    padding: 8,
    borderRadius: 6,
    marginTop: 8,
  },
  warningText: {
    fontSize: 12,
    color: '#856404',
    textAlign: 'center',
  },
});
