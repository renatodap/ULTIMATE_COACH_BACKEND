/**
 * Program Dashboard Screen
 *
 * Drop-in file for: ULTIMATE_COACH_FRONTEND/src/screens/ProgramDashboardScreen.tsx
 *
 * Main hub for user's active program. Shows today's plan, quick actions, and progress.
 */

import React from 'react';
import { View, Text, ScrollView, StyleSheet, TouchableOpacity, RefreshControl } from 'react-native';
import { useTodayPlan, useProgress } from '../hooks/useProgramData';
import MacroTargetsCard from '../components/MacroTargetsCard';
import WorkoutCard from '../components/WorkoutCard';
import MealsCard from '../components/MealsCard';
import ProgressCard from '../components/ProgressCard';
import QuickActionsBar from '../components/QuickActionsBar';

interface Props {
  userId: string;
  navigation: any;
}

export default function ProgramDashboardScreen({ userId, navigation }: Props) {
  const { data: todayPlan, loading, error, refetch } = useTodayPlan(userId);
  const { data: progress } = useProgress(userId, 7); // Last 7 days

  const handleRefresh = () => {
    refetch();
  };

  const handleViewWorkout = () => {
    if (todayPlan?.workout) {
      navigation.navigate('Workout', { workout: todayPlan.workout });
    }
  };

  const handleViewMeals = () => {
    if (todayPlan?.meals) {
      navigation.navigate('Meals', { meals: todayPlan.meals });
    }
  };

  const handleViewProgress = () => {
    navigation.navigate('Progress');
  };

  const handleViewGroceryList = () => {
    navigation.navigate('GroceryList');
  };

  if (loading && !todayPlan) {
    return (
      <View style={styles.container}>
        <Text style={styles.loadingText}>Loading today's plan...</Text>
      </View>
    );
  }

  if (error) {
    return (
      <View style={styles.container}>
        <Text style={styles.errorText}>{error}</Text>
        <TouchableOpacity style={styles.retryButton} onPress={handleRefresh}>
          <Text style={styles.retryButtonText}>Retry</Text>
        </TouchableOpacity>
      </View>
    );
  }

  if (!todayPlan) {
    return (
      <View style={styles.container}>
        <Text style={styles.errorText}>No active plan found</Text>
      </View>
    );
  }

  return (
    <ScrollView
      style={styles.container}
      refreshControl={
        <RefreshControl refreshing={loading} onRefresh={handleRefresh} />
      }
    >
      {/* Header */}
      <View style={styles.header}>
        <Text style={styles.title}>Today's Plan</Text>
        <Text style={styles.subtitle}>
          {todayPlan.calendar_day.toUpperCase()} • Day {todayPlan.cycle_day} of {todayPlan.cycle_week * 7}
        </Text>
      </View>

      {/* Reassessment Notice */}
      {todayPlan.days_until_next_reassessment <= 3 && (
        <View style={styles.noticeCard}>
          <Text style={styles.noticeText}>
            📊 Progress check-in in {todayPlan.days_until_next_reassessment} days
          </Text>
        </View>
      )}

      {/* Macro Targets */}
      <MacroTargetsCard macros={todayPlan.macro_targets} />

      {/* Training Section */}
      {todayPlan.is_training_day && todayPlan.workout ? (
        <WorkoutCard
          workout={todayPlan.workout}
          onPress={handleViewWorkout}
        />
      ) : (
        <View style={styles.restDayCard}>
          <Text style={styles.restDayTitle}>🛌 Rest Day</Text>
          <Text style={styles.restDayText}>
            Recovery is essential for progress. Focus on nutrition and sleep.
          </Text>
        </View>
      )}

      {/* Meals Section */}
      <MealsCard
        meals={todayPlan.meals}
        onPress={handleViewMeals}
      />

      {/* Progress Card (last 7 days) */}
      {progress && (
        <ProgressCard
          progress={progress}
          onPress={handleViewProgress}
        />
      )}

      {/* Quick Actions */}
      <QuickActionsBar
        onLogMeal={() => navigation.navigate('LogMeal')}
        onLogWeight={() => navigation.navigate('LogWeight')}
        onViewGroceryList={handleViewGroceryList}
        onChatWithCoach={() => navigation.navigate('Coach')}
      />

      {/* Bottom Padding */}
      <View style={{ height: 32 }} />
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f5f5f5',
  },
  header: {
    padding: 20,
    backgroundColor: '#fff',
    borderBottomWidth: 1,
    borderBottomColor: '#e0e0e0',
  },
  title: {
    fontSize: 28,
    fontWeight: 'bold',
    color: '#333',
  },
  subtitle: {
    fontSize: 14,
    color: '#666',
    marginTop: 4,
  },
  noticeCard: {
    backgroundColor: '#fff3cd',
    padding: 16,
    margin: 16,
    borderRadius: 8,
    borderLeftWidth: 4,
    borderLeftColor: '#ffc107',
  },
  noticeText: {
    fontSize: 14,
    color: '#856404',
  },
  restDayCard: {
    backgroundColor: '#e8f5e9',
    padding: 20,
    margin: 16,
    borderRadius: 12,
    borderWidth: 1,
    borderColor: '#c8e6c9',
  },
  restDayTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#2e7d32',
    marginBottom: 8,
  },
  restDayText: {
    fontSize: 14,
    color: '#1b5e20',
    lineHeight: 20,
  },
  loadingText: {
    fontSize: 16,
    color: '#666',
    textAlign: 'center',
    marginTop: 100,
  },
  errorText: {
    fontSize: 16,
    color: '#d32f2f',
    textAlign: 'center',
    marginTop: 100,
    paddingHorizontal: 20,
  },
  retryButton: {
    backgroundColor: '#1976d2',
    padding: 12,
    borderRadius: 8,
    marginTop: 16,
    marginHorizontal: 60,
  },
  retryButtonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '600',
    textAlign: 'center',
  },
});
