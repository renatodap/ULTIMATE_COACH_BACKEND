import React from 'react';
import { View, Text, StyleSheet } from 'react-native';

export default function ProgressBar({ label, value, target }: { label: string; value: number; target: number }) {
  const percentage = Math.min((value / target) * 100, 100);
  const color = value >= target ? '#4caf50' : value >= target * 0.7 ? '#ff9800' : '#f44336';

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.label}>{label}</Text>
        <Text style={styles.value}>{(value * 100).toFixed(0)}%</Text>
      </View>
      <View style={styles.barBackground}>
        <View style={[styles.barFill, { width: `${percentage}%`, backgroundColor: color }]} />
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { marginBottom: 16 },
  header: { flexDirection: 'row', justifyContent: 'space-between', marginBottom: 8 },
  label: { fontSize: 14, color: '#666' },
  value: { fontSize: 14, fontWeight: 'bold', color: '#333' },
  barBackground: { height: 8, backgroundColor: '#e0e0e0', borderRadius: 4, overflow: 'hidden' },
  barFill: { height: '100%', borderRadius: 4 },
});
