import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { ExerciseSet } from '../types/program';

export default function SetRow({ set }: { set: ExerciseSet }) {
  return (
    <View style={styles.row}>
      <Text style={styles.setNumber}>Set {set.set_number}</Text>
      <Text style={styles.detail}>{set.reps} reps</Text>
      {set.weight_kg && <Text style={styles.detail}>{set.weight_kg} kg</Text>}
      {set.rpe && <Text style={styles.detail}>RPE {set.rpe}</Text>}
      <Text style={styles.rest}>{set.rest_seconds}s rest</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  row: { flexDirection: 'row', justifyContent: 'space-between', paddingVertical: 8, borderBottomWidth: 1, borderBottomColor: '#f0f0f0' },
  setNumber: { fontSize: 14, fontWeight: '600', color: '#333', flex: 1 },
  detail: { fontSize: 14, color: '#666', marginHorizontal: 8 },
  rest: { fontSize: 12, color: '#999' },
});
