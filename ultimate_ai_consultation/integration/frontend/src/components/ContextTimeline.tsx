/**
 * ContextTimeline Component
 *
 * Displays a visual timeline of user's life context events
 * (stress, travel, injury, informal activities, etc.)
 */

import React from 'react';
import { View, Text, StyleSheet, ScrollView, TouchableOpacity } from 'react-native';
import {
  ContextLog,
  getContextIcon,
  getContextColor,
  getSeverityLabel,
  formatSentiment,
  ContextType
} from '../types/context';

interface Props {
  contextLogs: ContextLog[];
  showFilters?: boolean;
  onFilterChange?: (filter: ContextType | null) => void;
}

export function ContextTimeline({ contextLogs, showFilters = false, onFilterChange }: Props) {
  const [activeFilter, setActiveFilter] = React.useState<ContextType | null>(null);

  const filteredLogs = activeFilter
    ? contextLogs.filter(log => log.context_type === activeFilter)
    : contextLogs;

  const handleFilterPress = (filter: ContextType) => {
    const newFilter = activeFilter === filter ? null : filter;
    setActiveFilter(newFilter);
    onFilterChange?.(newFilter);
  };

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

  // Get unique context types for filters
  const contextTypes = Array.from(new Set(contextLogs.map(log => log.context_type)));

  return (
    <View style={styles.container}>
      <Text style={styles.title}>Life Context Timeline</Text>

      {showFilters && contextTypes.length > 0 && (
        <ScrollView
          horizontal
          showsHorizontalScrollIndicator={false}
          style={styles.filtersContainer}
          contentContainerStyle={styles.filtersContent}
        >
          {contextTypes.map(type => (
            <TouchableOpacity
              key={type}
              style={[
                styles.filterChip,
                activeFilter === type && styles.filterChipActive,
                { borderColor: getContextColor(type) }
              ]}
              onPress={() => handleFilterPress(type)}
            >
              <Text style={styles.filterIcon}>{getContextIcon(type)}</Text>
              <Text style={[
                styles.filterText,
                activeFilter === type && styles.filterTextActive
              ]}>
                {type.replace('_', ' ')}
              </Text>
            </TouchableOpacity>
          ))}
        </ScrollView>
      )}

      {filteredLogs.length === 0 ? (
        <View style={styles.emptyState}>
          <Text style={styles.emptyIcon}>✨</Text>
          <Text style={styles.emptyText}>
            {activeFilter
              ? `No ${activeFilter.replace('_', ' ')} events in this period`
              : 'No context events logged yet'}
          </Text>
        </View>
      ) : (
        <ScrollView style={styles.timeline}>
          {filteredLogs.map((log, index) => (
            <View key={log.id} style={styles.timelineItem}>
              {/* Connector line */}
              {index < filteredLogs.length - 1 && (
                <View style={[styles.connector, { backgroundColor: getContextColor(log.context_type) }]} />
              )}

              <View style={styles.itemContent}>
                {/* Icon bubble */}
                <View style={[styles.iconBubble, { backgroundColor: getContextColor(log.context_type) }]}>
                  <Text style={styles.icon}>{getContextIcon(log.context_type)}</Text>
                </View>

                {/* Content card */}
                <View style={styles.card}>
                  {/* Header */}
                  <View style={styles.cardHeader}>
                    <Text style={styles.contextType}>
                      {log.context_type.toUpperCase().replace('_', ' ')}
                      {log.severity && (
                        <Text style={styles.severity}> • {getSeverityLabel(log.severity)}</Text>
                      )}
                    </Text>
                    <Text style={styles.date}>{formatDate(log.created_at)}</Text>
                  </View>

                  {/* Description */}
                  <Text style={styles.description}>{log.description}</Text>

                  {/* Tags */}
                  <View style={styles.tags}>
                    {log.affects_training && (
                      <View style={[styles.tag, styles.tagTraining]}>
                        <Text style={styles.tagText}>Affects Training</Text>
                      </View>
                    )}
                    {log.affects_nutrition && (
                      <View style={[styles.tag, styles.tagNutrition]}>
                        <Text style={styles.tagText}>Affects Nutrition</Text>
                      </View>
                    )}
                    {log.sentiment_score !== undefined && log.sentiment_score !== null && (
                      <View style={[styles.tag, styles.tagSentiment]}>
                        <Text style={styles.tagText}>{formatSentiment(log.sentiment_score)}</Text>
                      </View>
                    )}
                  </View>

                  {/* Suggested adaptation */}
                  {log.suggested_adaptation && (
                    <View style={styles.adaptation}>
                      <Text style={styles.adaptationLabel}>💡 Suggestion:</Text>
                      <Text style={styles.adaptationText}>{log.suggested_adaptation}</Text>
                    </View>
                  )}

                  {/* Extraction info (if AI-extracted) */}
                  {log.extraction_confidence && log.extraction_confidence < 1.0 && (
                    <Text style={styles.extractionInfo}>
                      Auto-detected ({Math.round(log.extraction_confidence * 100)}% confidence)
                    </Text>
                  )}
                </View>
              </View>
            </View>
          ))}
        </ScrollView>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    padding: 16,
    backgroundColor: '#f8f9fa',
    borderRadius: 12,
    marginVertical: 8,
  },
  title: {
    fontSize: 20,
    fontWeight: '700',
    marginBottom: 16,
    color: '#2d3436',
  },
  filtersContainer: {
    marginBottom: 16,
  },
  filtersContent: {
    paddingRight: 16,
  },
  filterChip: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 20,
    borderWidth: 1,
    backgroundColor: 'white',
    marginRight: 8,
  },
  filterChipActive: {
    backgroundColor: '#e8f4fd',
  },
  filterIcon: {
    fontSize: 16,
    marginRight: 6,
  },
  filterText: {
    fontSize: 13,
    color: '#636e72',
    textTransform: 'capitalize',
  },
  filterTextActive: {
    color: '#0984e3',
    fontWeight: '600',
  },
  emptyState: {
    alignItems: 'center',
    paddingVertical: 40,
  },
  emptyIcon: {
    fontSize: 48,
    marginBottom: 12,
  },
  emptyText: {
    fontSize: 15,
    color: '#636e72',
    textAlign: 'center',
  },
  timeline: {
    maxHeight: 600,
  },
  timelineItem: {
    position: 'relative',
    marginBottom: 16,
  },
  connector: {
    position: 'absolute',
    left: 19,
    top: 40,
    width: 2,
    height: '100%',
    opacity: 0.3,
  },
  itemContent: {
    flexDirection: 'row',
    alignItems: 'flex-start',
  },
  iconBubble: {
    width: 40,
    height: 40,
    borderRadius: 20,
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: 12,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  icon: {
    fontSize: 20,
  },
  card: {
    flex: 1,
    backgroundColor: 'white',
    borderRadius: 12,
    padding: 12,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.1,
    shadowRadius: 3,
    elevation: 2,
  },
  cardHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8,
  },
  contextType: {
    fontSize: 14,
    fontWeight: '700',
    color: '#2d3436',
  },
  severity: {
    fontSize: 13,
    fontWeight: '500',
    color: '#636e72',
  },
  date: {
    fontSize: 12,
    color: '#b2bec3',
  },
  description: {
    fontSize: 14,
    color: '#2d3436',
    lineHeight: 20,
    marginBottom: 8,
  },
  tags: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    marginBottom: 8,
  },
  tag: {
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 4,
    marginRight: 6,
    marginBottom: 4,
  },
  tagTraining: {
    backgroundColor: '#ffeaa7',
  },
  tagNutrition: {
    backgroundColor: '#dfe6e9',
  },
  tagSentiment: {
    backgroundColor: '#e8f4fd',
  },
  tagText: {
    fontSize: 11,
    fontWeight: '600',
    color: '#2d3436',
  },
  adaptation: {
    backgroundColor: '#f1f3f5',
    padding: 10,
    borderRadius: 8,
    marginTop: 4,
  },
  adaptationLabel: {
    fontSize: 12,
    fontWeight: '600',
    color: '#495057',
    marginBottom: 4,
  },
  adaptationText: {
    fontSize: 13,
    color: '#495057',
    lineHeight: 18,
  },
  extractionInfo: {
    fontSize: 11,
    color: '#b2bec3',
    marginTop: 6,
    fontStyle: 'italic',
  },
});
