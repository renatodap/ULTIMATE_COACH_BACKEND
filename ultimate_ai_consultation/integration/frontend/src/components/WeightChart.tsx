import React from 'react';
import { View, Text, StyleSheet, Dimensions } from 'react-native';
import { LineChart } from 'react-native-chart-kit';

export default function WeightChart({ data, targetRate }: { data: Array<{ date: string; weight_kg: number }>; targetRate: number }) {
  if (data.length === 0) {
    return <View style={styles.empty}><Text>No weight data yet</Text></View>;
  }

  const weights = data.map(d => d.weight_kg);
  const labels = data.map(d => new Date(d.date).toLocaleDateString('en', { month: 'short', day: 'numeric' }));

  return (
    <View style={styles.container}>
      <Text style={styles.title}>Weight Trend</Text>
      <LineChart
        data={{
          labels: labels.length > 7 ? labels.filter((_, i) => i % 2 === 0) : labels,
          datasets: [{ data: weights, color: () => '#1976d2', strokeWidth: 2 }],
        }}
        width={Dimensions.get('window').width - 32}
        height={220}
        chartConfig={{
          backgroundColor: '#fff',
          backgroundGradientFrom: '#fff',
          backgroundGradientTo: '#fff',
          decimalPlaces: 1,
          color: (opacity = 1) => `rgba(25, 118, 210, ${opacity})`,
          labelColor: (opacity = 1) => `rgba(0, 0, 0, ${opacity})`,
          style: { borderRadius: 16 },
          propsForDots: { r: '4', strokeWidth: '2', stroke: '#1976d2' },
        }}
        bezier
        style={styles.chart}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  container: { backgroundColor: '#fff', margin: 16, padding: 16, borderRadius: 12 },
  title: { fontSize: 18, fontWeight: 'bold', marginBottom: 12 },
  chart: { borderRadius: 12 },
  empty: { backgroundColor: '#fff', margin: 16, padding: 32, borderRadius: 12, alignItems: 'center' },
});
