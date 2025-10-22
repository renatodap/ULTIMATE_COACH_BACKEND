/**
 * Workout Screen
 *
 * Drop-in: ULTIMATE_COACH_FRONTEND/src/screens/WorkoutScreen.tsx
 *
 * Displays workout details with exercise tracking.
 */

import React, { useState } from 'react';
import { View, Text, ScrollView, StyleSheet, TouchableOpacity } from 'react-native';
import { WorkoutSession } from '../types/program';
import ExerciseCard from '../components/ExerciseCard';

interface Props {
  route: { params: { workout: WorkoutSession } };
  navigation: any;
}

export default function WorkoutScreen({ route, navigation }: Props) {
  const { workout } = route.params;
  const [completedExercises, setCompletedExercises] = useState<Set<string>>(new Set());

  const handleExerciseComplete = (exerciseId: string) => {
    setCompletedExercises(prev => new Set(prev).add(exerciseId));
  };

  const allCompleted = completedExercises.size === workout.exercises.length;

  return (
    <ScrollView style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.title}>{workout.day_name}</Text>
        <Text style={styles.subtitle}>
          {workout.muscle_groups.join(', ')} • {workout.estimated_duration_minutes} min
        </Text>
        <Text style={styles.progress}>
          {completedExercises.size}/{workout.exercises.length} exercises completed
        </Text>
      </View>

      {workout.exercises.map((exercise) => (
        <ExerciseCard
          key={exercise.exercise_id}
          exercise={exercise}
          completed={completedExercises.has(exercise.exercise_id)}
          onComplete={() => handleExerciseComplete(exercise.exercise_id)}
        />
      ))}

      {allCompleted && (
        <TouchableOpacity style={styles.finishButton} onPress={() => navigation.goBack()}>
          <Text style={styles.finishButtonText}>✅ Workout Complete!</Text>
        </TouchableOpacity>
      )}

      <View style={{ height: 40 }} />
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#f5f5f5' },
  header: { padding: 20, backgroundColor: '#fff', borderBottomWidth: 1, borderBottomColor: '#e0e0e0' },
  title: { fontSize: 24, fontWeight: 'bold', color: '#333' },
  subtitle: { fontSize: 14, color: '#666', marginTop: 4 },
  progress: { fontSize: 16, color: '#1976d2', marginTop: 8, fontWeight: '600' },
  finishButton: { backgroundColor: '#4caf50', padding: 16, margin: 16, borderRadius: 12, alignItems: 'center' },
  finishButtonText: { color: '#fff', fontSize: 18, fontWeight: 'bold' },
});
