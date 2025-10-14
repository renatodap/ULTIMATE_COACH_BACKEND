import React from 'react';
import { TouchableOpacity, Text, StyleSheet, View } from 'react-native';
import { ProgressResponse } from '../types/program';

export default function ProgressCard({ progress, onPress }: { progress: ProgressResponse; onPress: () => void }) {
  const m = progress.metrics;
  return (
    <TouchableOpacity style={styles.card} onPress={onPress}>
      <Text style={styles.title}>7-Day Progress</Text>
      <View style={styles.row}>
        <Metric label="Weight Change" value={`${(m.weight_change_kg || 0).toFixed(1)} kg`} />
        <Metric label="Meal Adherence" value={`${(m.meal_logging_adherence * 100).toFixed(0)}%`} />
      </View>
      <View style={[styles.trendBadge, styles[`trend_${progress.trend_direction}`]]}>
        <Text style={styles.trendText}>{progress.trend_direction.toUpperCase()}</Text>
      </View>
    </TouchableOpacity>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return <View style={styles.metric}><Text style={styles.metricValue}>{value}</Text><Text style={styles.metricLabel}>{label}</Text></View>;
}

const styles = StyleSheet.create({
  card: { backgroundColor: '#fff', margin: 16, padding: 16, borderRadius: 12, shadowColor: '#000', shadowOffset: { width: 0, height: 2 }, shadowOpacity: 0.1, shadowRadius: 4, elevation: 3 },
  title: { fontSize: 18, fontWeight: 'bold', marginBottom: 12 },
  row: { flexDirection: 'row', justifyContent: 'space-around', marginBottom: 12 },
  metric: { alignItems: 'center' },
  metricValue: { fontSize: 20, fontWeight: 'bold', color: '#333' },
  metricLabel: { fontSize: 12, color: '#666', marginTop: 4 },
  trendBadge: { paddingVertical: 8, paddingHorizontal: 16, borderRadius: 8, alignSelf: 'center' },
  trendText: { fontSize: 12, fontWeight: 'bold' },
  trend_on_track: { backgroundColor: '#e8f5e9' },
  trend_exceeding: { backgroundColor: '#fff3e0' },
  trend_slow: { backgroundColor: '#fff9c4' },
});
