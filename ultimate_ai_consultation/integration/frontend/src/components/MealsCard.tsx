import React from 'react';
import { TouchableOpacity, Text, StyleSheet, View } from 'react-native';
import { Meal } from '../types/program';

export default function MealsCard({ meals, onPress }: { meals: Meal[]; onPress: () => void }) {
  return (
    <TouchableOpacity style={styles.card} onPress={onPress}>
      <Text style={styles.title}>Today's Meals ({meals.length})</Text>
      {meals.slice(0, 3).map(meal => (
        <View key={meal.meal_id} style={styles.meal}>
          <Text style={styles.mealName}>{meal.meal_name}</Text>
          <Text style={styles.mealCalories}>{meal.total_calories} kcal</Text>
        </View>
      ))}
      <Text style={styles.viewButton}>View Full Meal Plan →</Text>
    </TouchableOpacity>
  );
}

const styles = StyleSheet.create({
  card: { backgroundColor: '#fff', margin: 16, padding: 16, borderRadius: 12, shadowColor: '#000', shadowOffset: { width: 0, height: 2 }, shadowOpacity: 0.1, shadowRadius: 4, elevation: 3 },
  title: { fontSize: 18, fontWeight: 'bold', marginBottom: 12 },
  meal: { flexDirection: 'row', justifyContent: 'space-between', paddingVertical: 8, borderBottomWidth: 1, borderBottomColor: '#f0f0f0' },
  mealName: { fontSize: 16, color: '#333' },
  mealCalories: { fontSize: 16, color: '#666', fontWeight: '600' },
  viewButton: { fontSize: 14, color: '#1976d2', fontWeight: '600', marginTop: 12, textAlign: 'right' },
});
