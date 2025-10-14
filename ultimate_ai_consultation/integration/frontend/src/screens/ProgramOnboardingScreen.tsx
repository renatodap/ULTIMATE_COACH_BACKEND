/**
 * Program Onboarding Screen
 *
 * Drop-in: ULTIMATE_COACH_FRONTEND/src/screens/ProgramOnboardingScreen.tsx
 *
 * Shown after consultation is complete, triggers program generation.
 */

import React, { useState } from 'react';
import { View, Text, ScrollView, StyleSheet, TouchableOpacity, ActivityIndicator } from 'react-native';
import ProgramAPI from '../services/programApi';

interface Props {
  userId: string;
  consultationData: Record<string, any>;
  navigation: any;
}

export default function ProgramOnboardingScreen({ userId, consultationData, navigation }: Props) {
  const [generating, setGenerating] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleGenerateProgram = async () => {
    setGenerating(true);
    setError(null);

    try {
      const result = await ProgramAPI.generateProgram({
        user_id: userId,
        consultation_data: consultationData,
      });

      // Success! Navigate to dashboard
      navigation.replace('ProgramDashboard');
    } catch (err: any) {
      setError(err.response?.data?.message || 'Failed to generate program');
    } finally {
      setGenerating(false);
    }
  };

  return (
    <ScrollView style={styles.container}>
      <View style={styles.content}>
        <Text style={styles.emoji}>🎯</Text>
        <Text style={styles.title}>Your Custom Program is Ready!</Text>
        <Text style={styles.description}>
          Based on your consultation, we've designed a complete fitness and nutrition program tailored specifically to your goals.
        </Text>

        <View style={styles.features}>
          <View style={{ marginBottom: 16 }}><Feature icon="💪" title="Training Plan" text={`${consultationData.workouts_per_week || 5}x/week workouts`} /></View>
          <View style={{ marginBottom: 16 }}><Feature icon="🍽️" title="Meal Plan" text="14-day personalized nutrition" /></View>
          <View style={{ marginBottom: 16 }}><Feature icon="📊" title="Progress Tracking" text="Automatic adjustments every 2 weeks" /></View>
          <Feature icon="🛒" title="Grocery List" text="Shopping list included" />
        </View>

        {error && <Text style={styles.error}>{error}</Text>}

        <TouchableOpacity
          style={[styles.button, generating && styles.buttonDisabled]}
          onPress={handleGenerateProgram}
          disabled={generating}
        >
          {generating ? (
            <ActivityIndicator color="#fff" />
          ) : (
            <Text style={styles.buttonText}>Generate My Program</Text>
          )}
        </TouchableOpacity>

        <Text style={styles.disclaimer}>
          This program is based on evidence-based protocols and your individual data.
          You can modify it anytime by chatting with your coach.
        </Text>
      </View>
    </ScrollView>
  );
}

function Feature({ icon, title, text }: { icon: string; title: string; text: string }) {
  return (
    <View style={styles.feature}>
      <Text style={styles.featureIcon}>{icon}</Text>
      <View style={styles.featureText}>
        <Text style={styles.featureTitle}>{title}</Text>
        <Text style={styles.featureDescription}>{text}</Text>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#fff' },
  content: { padding: 24, alignItems: 'center' },
  emoji: { fontSize: 64, marginBottom: 16 },
  title: { fontSize: 28, fontWeight: 'bold', textAlign: 'center', marginBottom: 12 },
  description: { fontSize: 16, color: '#666', textAlign: 'center', lineHeight: 24, marginBottom: 32 },
  features: { width: '100%', marginBottom: 32 },
  feature: { flexDirection: 'row', alignItems: 'center', backgroundColor: '#f5f5f5', padding: 16, borderRadius: 12 },
  featureIcon: { fontSize: 32, marginRight: 16 },
  featureText: { flex: 1 },
  featureTitle: { fontSize: 16, fontWeight: 'bold', marginBottom: 4 },
  featureDescription: { fontSize: 14, color: '#666' },
  button: { backgroundColor: '#1976d2', paddingVertical: 16, paddingHorizontal: 32, borderRadius: 12, width: '100%', alignItems: 'center', marginBottom: 16 },
  buttonDisabled: { opacity: 0.6 },
  buttonText: { color: '#fff', fontSize: 18, fontWeight: 'bold' },
  disclaimer: { fontSize: 12, color: '#999', textAlign: 'center', lineHeight: 18 },
  error: { color: '#d32f2f', fontSize: 14, textAlign: 'center', marginBottom: 16 },
});
