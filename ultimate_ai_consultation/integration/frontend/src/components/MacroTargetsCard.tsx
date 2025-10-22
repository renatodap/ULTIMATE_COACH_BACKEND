import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { MacroTargets } from '../types/program';

export default function MacroTargetsCard({ macros }: { macros: MacroTargets }) {
  return (
    <View style={styles.card}>
      <Text style={styles.title}>Today's Targets</Text>
      <View style={styles.macros}>
        <Macro label="Calories" value={macros.calories} unit="kcal" color="#ff9800" />
        <Macro label="Protein" value={macros.protein_g} unit="g" color="#e91e63" />
        <Macro label="Carbs" value={macros.carbs_g} unit="g" color="#2196f3" />
        <Macro label="Fat" value={macros.fat_g} unit="g" color="#4caf50" />
      </View>
    </View>
  );
}

function Macro({ label, value, unit, color }: { label: string; value: number; unit: string; color: string }) {
  return (
    <View style={styles.macro}>
      <View style={[styles.macroIndicator, { backgroundColor: color }]} />
      <Text style={styles.macroValue}>{value}</Text>
      <Text style={styles.macroUnit}>{unit}</Text>
      <Text style={styles.macroLabel}>{label}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  card: { backgroundColor: '#fff', margin: 16, padding: 16, borderRadius: 12, shadowColor: '#000', shadowOffset: { width: 0, height: 2 }, shadowOpacity: 0.1, shadowRadius: 4, elevation: 3 },
  title: { fontSize: 18, fontWeight: 'bold', marginBottom: 12 },
  macros: { flexDirection: 'row', justifyContent: 'space-between' },
  macro: { alignItems: 'center', flex: 1 },
  macroIndicator: { width: 40, height: 4, borderRadius: 2, marginBottom: 8 },
  macroValue: { fontSize: 24, fontWeight: 'bold', color: '#333' },
  macroUnit: { fontSize: 12, color: '#999', marginBottom: 4 },
  macroLabel: { fontSize: 12, color: '#666' },
});
