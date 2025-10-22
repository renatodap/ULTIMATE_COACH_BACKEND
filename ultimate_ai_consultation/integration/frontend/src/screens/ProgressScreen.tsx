/**
 * Progress Screen
 *
 * Drop-in: ULTIMATE_COACH_FRONTEND/src/screens/ProgressScreen.tsx
 */

import React, { useState } from 'react';
import { View, Text, ScrollView, StyleSheet, TouchableOpacity } from 'react-native';
import { useProgress, usePlanHistory } from '../hooks/useProgramData';
import WeightChart from '../components/WeightChart';
import ProgressBar from '../components/ProgressBar';
import AdjustmentCard from '../components/AdjustmentCard';

interface Props {
  userId: string;
}

export default function ProgressScreen({ userId }: Props) {
  const [days, setDays] = useState(14);
  const { data: progress, loading } = useProgress(userId, days);
  const { data: history } = usePlanHistory(userId);

  if (loading || !progress) {
    return <View style={styles.container}><Text>Loading...</Text></View>;
  }

  const metrics = progress.metrics;

  return (
    <ScrollView style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.title}>Your Progress</Text>
        <View style={styles.periodSelector}>
          {[7, 14, 30].map(d => (
            <TouchableOpacity key={d} onPress={() => setDays(d)} style={[styles.periodButton, days === d && styles.periodButtonActive, { marginLeft: 8 }]}>
              <Text style={[styles.periodButtonText, days === d && styles.periodButtonTextActive]}>{d}d</Text>
            </TouchableOpacity>
          ))}
        </View>
      </View>

      {/* Weight Chart */}
      <WeightChart data={progress.weight_history} targetRate={metrics.target_rate_per_week || 0} />

      {/* Metrics Grid */}
      <View style={styles.metricsGrid}>
        <View style={[styles.metricCard, { marginRight: 8 }]}>
          <Text style={styles.metricLabel}>Weight Change</Text>
          <Text style={styles.metricValue}>{metrics.weight_change_kg?.toFixed(1) || 'N/A'} kg</Text>
        </View>
        <View style={[styles.metricCard, { marginLeft: 8 }]}>
          <Text style={styles.metricLabel}>Weekly Rate</Text>
          <Text style={styles.metricValue}>{metrics.weight_change_rate_per_week?.toFixed(2) || 'N/A'} kg/wk</Text>
        </View>
      </View>

      {/* Adherence */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Adherence</Text>
        <ProgressBar label="Meal Logging" value={metrics.meal_logging_adherence} target={0.85} />
        <ProgressBar label="Training" value={metrics.training_adherence} target={0.85} />
      </View>

      {/* Recent Adjustments */}
      {history && history.adjustments.length > 0 && (
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Recent Adjustments</Text>
          {history.adjustments.slice(0, 3).map(adj => (
            <AdjustmentCard key={adj.adjustment_id} adjustment={adj} />
          ))}
        </View>
      )}

      <View style={{ height: 40 }} />
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#f5f5f5' },
  header: { padding: 20, backgroundColor: '#fff', flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' },
  title: { fontSize: 24, fontWeight: 'bold' },
  periodSelector: { flexDirection: 'row' },
  periodButton: { paddingHorizontal: 16, paddingVertical: 8, borderRadius: 8, backgroundColor: '#e0e0e0' },
  periodButtonActive: { backgroundColor: '#1976d2' },
  periodButtonText: { fontSize: 14, color: '#666', fontWeight: '600' },
  periodButtonTextActive: { color: '#fff' },
  metricsGrid: { flexDirection: 'row', padding: 16 },
  metricCard: { flex: 1, backgroundColor: '#fff', padding: 16, borderRadius: 12, alignItems: 'center' },
  metricLabel: { fontSize: 12, color: '#666', marginBottom: 4 },
  metricValue: { fontSize: 20, fontWeight: 'bold', color: '#333' },
  section: { margin: 16, padding: 16, backgroundColor: '#fff', borderRadius: 12 },
  sectionTitle: { fontSize: 18, fontWeight: 'bold', marginBottom: 12 },
});
