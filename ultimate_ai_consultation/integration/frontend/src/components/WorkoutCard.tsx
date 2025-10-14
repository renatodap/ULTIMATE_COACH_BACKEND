import React from 'react';
import { TouchableOpacity, Text, StyleSheet, View } from 'react-native';
import { WorkoutSession } from '../types/program';

export default function WorkoutCard({ workout, onPress }: { workout: WorkoutSession; onPress: () => void }) {
  return (
    <TouchableOpacity style={styles.card} onPress={onPress}>
      <Text style={styles.title}>{workout.day_name}</Text>
      <Text style={styles.subtitle}>{workout.muscle_groups.join(', ')}</Text>
      <View style={styles.stats}>
        <Stat label="Exercises" value={workout.exercises.length.toString()} />
        <Stat label="Sets" value={workout.total_sets.toString()} />
        <Stat label="Duration" value={`${workout.estimated_duration_minutes} min`} />
      </View>
      <Text style={styles.viewButton}>View Workout →</Text>
    </TouchableOpacity>
  );
}

function Stat({ label, value }: { label: string; value: string }) {
  return <View style={styles.stat}><Text style={styles.statValue}>{value}</Text><Text style={styles.statLabel}>{label}</Text></View>;
}

const styles = StyleSheet.create({
  card: { backgroundColor: '#1976d2', margin: 16, padding: 20, borderRadius: 12, shadowColor: '#000', shadowOffset: { width: 0, height: 2 }, shadowOpacity: 0.15, shadowRadius: 6, elevation: 4 },
  title: { fontSize: 20, fontWeight: 'bold', color: '#fff', marginBottom: 4 },
  subtitle: { fontSize: 14, color: '#bbdefb', marginBottom: 16 },
  stats: { flexDirection: 'row', justifyContent: 'space-between', marginBottom: 16 },
  stat: { alignItems: 'center' },
  statValue: { fontSize: 20, fontWeight: 'bold', color: '#fff' },
  statLabel: { fontSize: 12, color: '#bbdefb', marginTop: 4 },
  viewButton: { fontSize: 16, color: '#fff', fontWeight: '600', textAlign: 'right' },
});
