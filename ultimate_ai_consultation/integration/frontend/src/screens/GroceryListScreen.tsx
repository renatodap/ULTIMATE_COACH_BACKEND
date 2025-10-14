/**
 * Grocery List Screen
 *
 * Drop-in: ULTIMATE_COACH_FRONTEND/src/screens/GroceryListScreen.tsx
 */

import React, { useState } from 'react';
import { View, Text, ScrollView, StyleSheet, TouchableOpacity } from 'react-native';
import { useGroceryList } from '../hooks/useProgramData';

interface Props {
  userId: string;
}

export default function GroceryListScreen({ userId }: Props) {
  const { data, loading } = useGroceryList(userId);
  const [checkedItems, setCheckedItems] = useState<Set<string>>(new Set());

  const toggleItem = (foodName: string) => {
    setCheckedItems(prev => {
      const next = new Set(prev);
      if (next.has(foodName)) next.delete(foodName);
      else next.add(foodName);
      return next;
    });
  };

  if (loading || !data) {
    return <View style={styles.container}><Text>Loading...</Text></View>;
  }

  const categories = Object.keys(data.items_by_category);

  return (
    <ScrollView style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.title}>Shopping List</Text>
        <Text style={styles.subtitle}>
          {data.total_items} items • {data.covers_days} days
          {data.estimated_total_cost_usd && ` • $${data.estimated_total_cost_usd.toFixed(2)}`}
        </Text>
      </View>

      {categories.map(category => (
        <View key={category} style={styles.category}>
          <Text style={styles.categoryTitle}>{category}</Text>
          {data.items_by_category[category].map(item => (
            <TouchableOpacity
              key={item.food_name}
              style={styles.item}
              onPress={() => toggleItem(item.food_name)}
            >
              <View style={[styles.checkbox, checkedItems.has(item.food_name) && styles.checkboxChecked]}>
                {checkedItems.has(item.food_name) && <Text style={styles.checkmark}>✓</Text>}
              </View>
              <View style={styles.itemDetails}>
                <Text style={[styles.itemName, checkedItems.has(item.food_name) && styles.itemNameChecked]}>
                  {item.food_name}
                </Text>
                <Text style={styles.itemQuantity}>
                  {item.quantity.toFixed(1)} {item.unit}
                  {item.estimated_cost_usd && ` • $${item.estimated_cost_usd.toFixed(2)}`}
                </Text>
              </View>
            </TouchableOpacity>
          ))}
        </View>
      ))}

      <View style={{ height: 40 }} />
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#f5f5f5' },
  header: { padding: 20, backgroundColor: '#fff', borderBottomWidth: 1, borderBottomColor: '#e0e0e0' },
  title: { fontSize: 24, fontWeight: 'bold' },
  subtitle: { fontSize: 14, color: '#666', marginTop: 4 },
  category: { backgroundColor: '#fff', margin: 16, padding: 16, borderRadius: 12 },
  categoryTitle: { fontSize: 18, fontWeight: 'bold', marginBottom: 12, color: '#1976d2' },
  item: { flexDirection: 'row', alignItems: 'center', paddingVertical: 12, borderBottomWidth: 1, borderBottomColor: '#f0f0f0' },
  checkbox: { width: 24, height: 24, borderWidth: 2, borderColor: '#bbb', borderRadius: 4, marginRight: 12, alignItems: 'center', justifyContent: 'center' },
  checkboxChecked: { backgroundColor: '#4caf50', borderColor: '#4caf50' },
  checkmark: { color: '#fff', fontSize: 16, fontWeight: 'bold' },
  itemDetails: { flex: 1 },
  itemName: { fontSize: 16, color: '#333', fontWeight: '500' },
  itemNameChecked: { textDecorationLine: 'line-through', color: '#999' },
  itemQuantity: { fontSize: 14, color: '#666', marginTop: 2 },
});
