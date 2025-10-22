import React from 'react';
import { View, TouchableOpacity, Text, StyleSheet } from 'react-native';

export default function QuickActionsBar({ onLogMeal, onLogWeight, onViewGroceryList, onChatWithCoach }: any) {
  return (
    <View style={styles.container}>
      <Action icon="🍽️" label="Log Meal" onPress={onLogMeal} />
      <Action icon="⚖️" label="Log Weight" onPress={onLogWeight} />
      <Action icon="🛒" label="Grocery" onPress={onViewGroceryList} />
      <Action icon="💬" label="Coach" onPress={onChatWithCoach} />
    </View>
  );
}

function Action({ icon, label, onPress }: { icon: string; label: string; onPress: () => void }) {
  return (
    <TouchableOpacity style={styles.action} onPress={onPress}>
      <Text style={styles.icon}>{icon}</Text>
      <Text style={styles.label}>{label}</Text>
    </TouchableOpacity>
  );
}

const styles = StyleSheet.create({
  container: { flexDirection: 'row', backgroundColor: '#fff', margin: 16, padding: 8, borderRadius: 12, shadowColor: '#000', shadowOffset: { width: 0, height: 2 }, shadowOpacity: 0.1, shadowRadius: 4, elevation: 3 },
  action: { flex: 1, alignItems: 'center', padding: 12 },
  icon: { fontSize: 28, marginBottom: 4 },
  label: { fontSize: 12, color: '#666', fontWeight: '600' },
});
