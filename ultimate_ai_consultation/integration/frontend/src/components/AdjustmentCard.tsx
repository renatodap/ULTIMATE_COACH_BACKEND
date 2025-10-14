import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { AdjustmentRecord } from '../types/program';

export default function AdjustmentCard({ adjustment }: { adjustment: AdjustmentRecord }) {
  const calChange = adjustment.calories_after - adjustment.calories_before;
  const volChange = adjustment.volume_after - adjustment.volume_before;

  return (
    <View style={styles.card}>
      <Text style={styles.date}>{new Date(adjustment.created_at).toLocaleDateString()}</Text>
      <Text style={styles.reason}>{adjustment.adjustment_reason.replace(/_/g, ' ')}</Text>
      <View style={styles.changes}>
        <Change label="Calories" value={calChange} unit="kcal" />
        <Change label="Volume" value={volChange} unit="sets/wk" />
      </View>
      <Text style={styles.rationale}>{adjustment.rationale}</Text>
    </View>
  );
}

function Change({ label, value, unit }: { label: string; value: number; unit: string }) {
  const color = value > 0 ? '#4caf50' : value < 0 ? '#f44336' : '#666';
  return (
    <View style={[styles.change, { marginRight: 16 }]}>
      <Text style={styles.changeLabel}>{label}</Text>
      <Text style={[styles.changeValue, { color }]}>{value > 0 ? '+' : ''}{value} {unit}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  card: { backgroundColor: '#f9f9f9', padding: 12, borderRadius: 8, marginBottom: 12 },
  date: { fontSize: 12, color: '#999', marginBottom: 4 },
  reason: { fontSize: 14, fontWeight: 'bold', color: '#333', marginBottom: 8 },
  changes: { flexDirection: 'row', marginBottom: 8 },
  change: { flex: 1 },
  changeLabel: { fontSize: 12, color: '#666', marginBottom: 2 },
  changeValue: { fontSize: 16, fontWeight: 'bold' },
  rationale: { fontSize: 13, color: '#666', lineHeight: 18 },
});
