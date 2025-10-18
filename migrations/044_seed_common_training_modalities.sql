-- Migration: Seed common training modalities for onboarding
-- Date: 2025-10-17
-- Purpose: Populate training_modalities table with curated list of popular training types

-- Clear existing data if any (for clean re-runs)
DELETE FROM user_training_modalities;
DELETE FROM training_modalities;

-- Insert common training modalities in display order
INSERT INTO public.training_modalities (name, description, typical_frequency_per_week, equipment_required, icon, display_order) VALUES
-- Strength Training
('Powerlifting', 'Focus on squat, bench press, and deadlift with heavy weights', 3, ARRAY['barbell', 'rack', 'bench'], '🏋️', 1),
('Bodybuilding', 'Hypertrophy training with focus on muscle size and aesthetics', 4, ARRAY['dumbbells', 'cables', 'machines'], '💪', 2),
('Olympic Weightlifting', 'Snatch and clean & jerk with emphasis on explosive power', 3, ARRAY['barbell', 'platform', 'bumper plates'], '🏋️‍♀️', 3),
('Calisthenics', 'Bodyweight training emphasizing strength and control', 4, ARRAY['pull-up bar', 'parallettes', 'rings'], '🤸', 4),

-- Functional & Mixed
('CrossFit', 'High-intensity functional fitness combining multiple modalities', 5, ARRAY['barbell', 'kettlebell', 'box', 'rope'], '🔥', 5),
('Functional Fitness', 'Practical movement patterns for everyday strength', 3, ARRAY['kettlebell', 'medicine ball', 'TRX'], '⚡', 6),

-- Endurance
('Running', 'Distance running, sprinting, or interval training', 4, ARRAY['running shoes'], '🏃', 7),
('Cycling', 'Road cycling, mountain biking, or indoor spinning', 4, ARRAY['bike', 'helmet'], '🚴', 8),
('Swimming', 'Pool or open water swimming for endurance and technique', 3, ARRAY['swimsuit', 'goggles'], '🏊', 9),
('Rowing', 'Indoor or outdoor rowing for full-body cardio', 3, ARRAY['rowing machine', 'boat'], '🚣', 10),

-- Sports
('Team Sports', 'Basketball, soccer, football, volleyball, etc.', 3, ARRAY['ball', 'court/field'], '⚽', 11),
('Racket Sports', 'Tennis, badminton, squash, pickleball', 3, ARRAY['racket', 'ball', 'court'], '🎾', 12),
('Martial Arts', 'Boxing, MMA, Muay Thai, Brazilian Jiu-Jitsu, etc.', 3, ARRAY['gloves', 'wraps', 'gi'], '🥊', 13),

-- Flexibility & Recovery
('Yoga', 'Flexibility, balance, and mindfulness practice', 3, ARRAY['mat'], '🧘', 14),
('Pilates', 'Core strength and flexibility with controlled movements', 3, ARRAY['mat', 'reformer'], '🤸‍♀️', 15),
('Mobility Work', 'Dynamic stretching and joint mobility exercises', 5, ARRAY['foam roller', 'bands'], '🔄', 16),

-- Other (catch-all for custom entries)
('Other', 'Custom training modality not listed above', NULL, ARRAY[]::text[], '💡', 99);

-- Add comment to table
COMMENT ON TABLE public.training_modalities IS 'Master list of training modalities for user selection during onboarding. Display order determines UI presentation.';
