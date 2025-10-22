import React from 'react';
import { View, Text, TouchableOpacity, StyleSheet } from 'react-native';
import { Exercise } from '../types/program';
import SetRow from './SetRow';

export default function ExerciseCard({ exercise, completed, onComplete }: { exercise: Exercise; completed: boolean; onComplete: () => void }) {
  return (
    <View style={[styles.card, completed && styles.cardCompleted]}>
      <Text style={styles.name}>{exercise.exercise_name}</Text>
      <Text style={styles.muscle}>{exercise.muscle_group}</Text>
      {exercise.sets.map(set => <SetRow key={set.set_number} set={set} />)}
      {!completed && (
        <TouchableOpacity style={styles.button} onPress={onComplete}>
          <Text style={styles.buttonText}>Mark Complete</Text>
        </TouchableOpacity>
      )}
      {completed && <Text style={styles.completedText}>✓ Completed</Text>}
    </View>
  );
}

const styles = StyleSheet.create({
  card: { backgroundColor: '#fff', margin: 16, padding: 16, borderRadius: 12 },
  cardCompleted: { backgroundColor: '#f1f8f4', borderWidth: 2, borderColor: '#4caf50' },
  name: { fontSize: 18, fontWeight: 'bold', marginBottom: 4 },
  muscle: { fontSize: 14, color: '#666', marginBottom: 12 },
  button: { backgroundColor: '#1976d2', padding: 12, borderRadius: 8, marginTop: 12 },
  buttonText: { color: '#fff', textAlign: 'center', fontWeight: '600' },
  completedText: { fontSize: 16, color: '#4caf50', fontWeight: 'bold', textAlign: 'center', marginTop: 12 },
});
