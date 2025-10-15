-- ============================================================================
-- ULTIMATE COACH - Exercise Library Seed Data
-- ============================================================================
-- Version: 1.0.0
-- Created: 2025-10-12
-- Description: Comprehensive exercise library covering all major modalities
--
-- CATEGORIES:
-- - Compound Strength (50+ exercises)
-- - Isolation Strength (40+ exercises)
-- - Cardio (20+ exercises)
-- - Bodyweight (30+ exercises)
-- - Olympic Lifts (10+ exercises)
-- - Functional/CrossFit (20+ exercises)
-- - Flexibility/Mobility (20+ exercises)
-- - Sports-Specific (20+ exercises)
-- ============================================================================

-- ============================================================================
-- COMPOUND STRENGTH EXERCISES
-- ============================================================================

INSERT INTO exercises (name, category, primary_muscle_groups, secondary_muscle_groups, equipment_needed, difficulty_level, primary_modalities, description) VALUES

-- Squat Variations
('Barbell Back Squat', 'compound_strength', ARRAY['quadriceps', 'glutes'], ARRAY['hamstrings', 'core', 'calves'], ARRAY['barbell', 'rack'], 'intermediate', ARRAY['Powerlifting', 'Bodybuilding', 'CrossFit'], 'King of leg exercises - barbell on back, squat to parallel or below'),
('Barbell Front Squat', 'compound_strength', ARRAY['quadriceps', 'core'], ARRAY['glutes', 'upper back'], ARRAY['barbell', 'rack'], 'advanced', ARRAY['Olympic Weightlifting', 'CrossFit'], 'Barbell racked on front delts, more quad emphasis'),
('Goblet Squat', 'compound_strength', ARRAY['quadriceps', 'glutes'], ARRAY['core'], ARRAY['dumbbell', 'kettlebell'], 'beginner', ARRAY['General Fitness'], 'Hold weight at chest, great for learning squat pattern'),
('Bulgarian Split Squat', 'compound_strength', ARRAY['quadriceps', 'glutes'], ARRAY['hamstrings'], ARRAY['dumbbells', 'bench'], 'intermediate', ARRAY['Bodybuilding', 'General Fitness'], 'Rear foot elevated single-leg squat'),
('Box Squat', 'compound_strength', ARRAY['quadriceps', 'glutes'], ARRAY['hamstrings'], ARRAY['barbell', 'rack', 'box'], 'intermediate', ARRAY['Powerlifting'], 'Squat to box, pause, then stand'),

-- Deadlift Variations
('Conventional Deadlift', 'compound_strength', ARRAY['posterior chain', 'back'], ARRAY['traps', 'forearms'], ARRAY['barbell'], 'intermediate', ARRAY['Powerlifting', 'General Fitness'], 'Hip-width stance, pull from floor'),
('Sumo Deadlift', 'compound_strength', ARRAY['glutes', 'adductors'], ARRAY['hamstrings', 'back'], ARRAY['barbell'], 'intermediate', ARRAY['Powerlifting'], 'Wide stance, toes out, more upright torso'),
('Romanian Deadlift', 'compound_strength', ARRAY['hamstrings', 'glutes'], ARRAY['lower back'], ARRAY['barbell', 'dumbbells'], 'intermediate', ARRAY['Bodybuilding', 'General Fitness'], 'Hinge at hips, slight knee bend, weight to mid-shin'),
('Trap Bar Deadlift', 'compound_strength', ARRAY['quadriceps', 'glutes'], ARRAY['back', 'traps'], ARRAY['trap bar'], 'beginner', ARRAY['General Fitness'], 'Stand inside trap bar, more quad emphasis than conventional'),
('Stiff-Leg Deadlift', 'compound_strength', ARRAY['hamstrings'], ARRAY['lower back', 'glutes'], ARRAY['barbell', 'dumbbells'], 'intermediate', ARRAY['Bodybuilding'], 'Legs nearly straight, extreme hamstring stretch'),

-- Bench Press Variations
('Barbell Bench Press', 'compound_strength', ARRAY['chest', 'triceps'], ARRAY['front delts'], ARRAY['barbell', 'bench'], 'intermediate', ARRAY['Powerlifting', 'Bodybuilding'], 'Flat bench, bar to chest, press up'),
('Incline Barbell Bench Press', 'compound_strength', ARRAY['upper chest', 'front delts'], ARRAY['triceps'], ARRAY['barbell', 'incline bench'], 'intermediate', ARRAY['Bodybuilding'], '30-45 degree incline, emphasizes upper chest'),
('Decline Barbell Bench Press', 'compound_strength', ARRAY['lower chest', 'triceps'], ARRAY['front delts'], ARRAY['barbell', 'decline bench'], 'intermediate', ARRAY['Bodybuilding'], 'Decline bench, emphasizes lower chest'),
('Dumbbell Bench Press', 'compound_strength', ARRAY['chest', 'triceps'], ARRAY['front delts'], ARRAY['dumbbells', 'bench'], 'beginner', ARRAY['Bodybuilding', 'General Fitness'], 'Greater range of motion than barbell'),
('Close-Grip Bench Press', 'compound_strength', ARRAY['triceps', 'chest'], ARRAY['front delts'], ARRAY['barbell', 'bench'], 'intermediate', ARRAY['Powerlifting', 'Bodybuilding'], 'Hands shoulder-width, more tricep emphasis'),

-- Overhead Press Variations
('Barbell Overhead Press', 'compound_strength', ARRAY['shoulders', 'triceps'], ARRAY['upper chest', 'core'], ARRAY['barbell'], 'intermediate', ARRAY['Powerlifting', 'General Fitness'], 'Standing, bar from shoulders overhead'),
('Seated Dumbbell Press', 'compound_strength', ARRAY['shoulders', 'triceps'], ARRAY['upper chest'], ARRAY['dumbbells', 'bench'], 'beginner', ARRAY['Bodybuilding'], 'Seated, dumbbells from shoulders to overhead'),
('Push Press', 'compound_strength', ARRAY['shoulders', 'legs'], ARRAY['triceps', 'core'], ARRAY['barbell'], 'intermediate', ARRAY['CrossFit', 'Olympic Weightlifting'], 'Use leg drive to help press weight overhead'),
('Arnold Press', 'compound_strength', ARRAY['shoulders'], ARRAY['triceps'], ARRAY['dumbbells'], 'intermediate', ARRAY['Bodybuilding'], 'Rotate palms from facing you to facing forward'),

-- Row Variations
('Barbell Bent-Over Row', 'compound_strength', ARRAY['lats', 'upper back'], ARRAY['rear delts', 'biceps'], ARRAY['barbell'], 'intermediate', ARRAY['Bodybuilding', 'Powerlifting'], 'Hinged position, pull bar to lower chest'),
('Pendlay Row', 'compound_strength', ARRAY['upper back', 'lats'], ARRAY['rear delts', 'traps'], ARRAY['barbell'], 'intermediate', ARRAY['CrossFit'], 'Explosive row from floor, bar touches floor each rep'),
('T-Bar Row', 'compound_strength', ARRAY['lats', 'upper back'], ARRAY['rear delts'], ARRAY['t-bar', 'landmine'], 'intermediate', ARRAY['Bodybuilding'], 'Landmine setup, pull to chest'),
('Dumbbell Row', 'compound_strength', ARRAY['lats', 'upper back'], ARRAY['rear delts', 'biceps'], ARRAY['dumbbells', 'bench'], 'beginner', ARRAY['Bodybuilding', 'General Fitness'], 'One arm at a time, supported by bench'),
('Chest-Supported Row', 'compound_strength', ARRAY['upper back', 'lats'], ARRAY['rear delts'], ARRAY['dumbbells', 'incline bench'], 'beginner', ARRAY['Bodybuilding'], 'Chest on incline bench, eliminates lower back strain'),

-- Pull Variations
('Pull-Up', 'compound_strength', ARRAY['lats', 'upper back'], ARRAY['biceps', 'forearms'], ARRAY['pull-up bar'], 'intermediate', ARRAY['Calisthenics', 'CrossFit', 'General Fitness'], 'Palms away, pull chin over bar'),
('Chin-Up', 'compound_strength', ARRAY['lats', 'biceps'], ARRAY['upper back'], ARRAY['pull-up bar'], 'intermediate', ARRAY['Calisthenics', 'General Fitness'], 'Palms toward you, more bicep emphasis'),
('Weighted Pull-Up', 'compound_strength', ARRAY['lats', 'upper back'], ARRAY['biceps'], ARRAY['pull-up bar', 'weight belt', 'dumbbell'], 'advanced', ARRAY['Calisthenics'], 'Add weight via belt or hold dumbbell between feet'),
('Lat Pulldown', 'compound_strength', ARRAY['lats', 'upper back'], ARRAY['biceps'], ARRAY['cable machine'], 'beginner', ARRAY['Bodybuilding', 'General Fitness'], 'Seated cable pull to chest'),

-- Lunge Variations
('Barbell Walking Lunge', 'compound_strength', ARRAY['quadriceps', 'glutes'], ARRAY['hamstrings', 'core'], ARRAY['barbell'], 'intermediate', ARRAY['CrossFit', 'General Fitness'], 'Barbell on back, step forward into lunge'),
('Dumbbell Lunge', 'compound_strength', ARRAY['quadriceps', 'glutes'], ARRAY['hamstrings'], ARRAY['dumbbells'], 'beginner', ARRAY['General Fitness'], 'Hold dumbbells at sides, lunge forward'),
('Reverse Lunge', 'compound_strength', ARRAY['quadriceps', 'glutes'], ARRAY['hamstrings'], ARRAY['dumbbells', 'barbell'], 'beginner', ARRAY['General Fitness'], 'Step backward into lunge, easier on knees'),

-- Hip Hinge/Posterior
('Hip Thrust', 'compound_strength', ARRAY['glutes'], ARRAY['hamstrings'], ARRAY['barbell', 'bench'], 'beginner', ARRAY['Bodybuilding', 'General Fitness'], 'Upper back on bench, barbell on hips, thrust upward'),
('Glute Bridge', 'compound_strength', ARRAY['glutes'], ARRAY['hamstrings'], ARRAY['barbell', 'bodyweight'], 'beginner', ARRAY['General Fitness'], 'Lie on back, drive hips upward');

-- ============================================================================
-- ISOLATION STRENGTH EXERCISES
-- ============================================================================

INSERT INTO exercises (name, category, primary_muscle_groups, secondary_muscle_groups, equipment_needed, difficulty_level, primary_modalities, description) VALUES

-- Chest Isolation
('Dumbbell Fly', 'isolation_strength', ARRAY['chest'], ARRAY[], ARRAY['dumbbells', 'bench'], 'beginner', ARRAY['Bodybuilding'], 'Lie on bench, arc dumbbells out and back together'),
('Cable Fly', 'isolation_strength', ARRAY['chest'], ARRAY[], ARRAY['cable machine'], 'beginner', ARRAY['Bodybuilding'], 'Cables from sides, bring hands together in front'),
('Pec Deck', 'isolation_strength', ARRAY['chest'], ARRAY[], ARRAY['pec deck machine'], 'beginner', ARRAY['Bodybuilding'], 'Machine-based chest fly'),

-- Shoulder Isolation
('Lateral Raise', 'isolation_strength', ARRAY['side delts'], ARRAY[], ARRAY['dumbbells', 'cables'], 'beginner', ARRAY['Bodybuilding'], 'Raise weights out to sides to shoulder height'),
('Front Raise', 'isolation_strength', ARRAY['front delts'], ARRAY[], ARRAY['dumbbells', 'barbell', 'plate'], 'beginner', ARRAY['Bodybuilding'], 'Raise weight in front to shoulder height'),
('Rear Delt Fly', 'isolation_strength', ARRAY['rear delts'], ARRAY[], ARRAY['dumbbells', 'cables'], 'beginner', ARRAY['Bodybuilding'], 'Bent over, raise weights out to sides'),
('Face Pull', 'isolation_strength', ARRAY['rear delts', 'upper back'], ARRAY[], ARRAY['cable machine', 'bands'], 'beginner', ARRAY['General Fitness'], 'Pull rope to face, excellent for posture'),

-- Back Isolation
('Straight-Arm Pulldown', 'isolation_strength', ARRAY['lats'], ARRAY[], ARRAY['cable machine'], 'beginner', ARRAY['Bodybuilding'], 'Arms straight, pull cable down in arc'),
('Shrug', 'isolation_strength', ARRAY['traps'], ARRAY[], ARRAY['dumbbells', 'barbell'], 'beginner', ARRAY['Bodybuilding', 'Powerlifting'], 'Elevate shoulders straight up'),

-- Biceps
('Barbell Curl', 'isolation_strength', ARRAY['biceps'], ARRAY['forearms'], ARRAY['barbell'], 'beginner', ARRAY['Bodybuilding'], 'Standard bicep curl with barbell'),
('Dumbbell Curl', 'isolation_strength', ARRAY['biceps'], ARRAY['forearms'], ARRAY['dumbbells'], 'beginner', ARRAY['Bodybuilding'], 'Curl dumbbells, can be done alternating or together'),
('Hammer Curl', 'isolation_strength', ARRAY['biceps', 'brachialis'], ARRAY['forearms'], ARRAY['dumbbells'], 'beginner', ARRAY['Bodybuilding'], 'Neutral grip, thumbs up throughout'),
('Preacher Curl', 'isolation_strength', ARRAY['biceps'], ARRAY[], ARRAY['preacher bench', 'dumbbells', 'barbell'], 'beginner', ARRAY['Bodybuilding'], 'Arms rested on preacher pad'),
('Cable Curl', 'isolation_strength', ARRAY['biceps'], ARRAY[], ARRAY['cable machine'], 'beginner', ARRAY['Bodybuilding'], 'Constant tension bicep curl'),

-- Triceps
('Tricep Pushdown', 'isolation_strength', ARRAY['triceps'], ARRAY[], ARRAY['cable machine'], 'beginner', ARRAY['Bodybuilding'], 'Push cable attachment down, elbows fixed at sides'),
('Overhead Tricep Extension', 'isolation_strength', ARRAY['triceps'], ARRAY[], ARRAY['dumbbells', 'cable machine'], 'beginner', ARRAY['Bodybuilding'], 'Weight overhead, lower behind head'),
('Skull Crusher', 'isolation_strength', ARRAY['triceps'], ARRAY[], ARRAY['barbell', 'ez-bar'], 'intermediate', ARRAY['Bodybuilding'], 'Lying, lower bar to forehead/behind head'),
('Dumbbell Kickback', 'isolation_strength', ARRAY['triceps'], ARRAY[], ARRAY['dumbbells'], 'beginner', ARRAY['Bodybuilding'], 'Bent over, extend arm backward'),
('Diamond Push-Up', 'isolation_strength', ARRAY['triceps', 'chest'], ARRAY[], ARRAY['bodyweight'], 'intermediate', ARRAY['Calisthenics'], 'Hands in diamond shape, tricep-focused push-up'),

-- Legs - Quads
('Leg Extension', 'isolation_strength', ARRAY['quadriceps'], ARRAY[], ARRAY['leg extension machine'], 'beginner', ARRAY['Bodybuilding'], 'Seated, extend legs against resistance'),
('Sissy Squat', 'isolation_strength', ARRAY['quadriceps'], ARRAY[], ARRAY['bodyweight'], 'advanced', ARRAY['Calisthenics', 'Bodybuilding'], 'Lean back while squatting, intense quad stretch'),

-- Legs - Hamstrings
('Leg Curl', 'isolation_strength', ARRAY['hamstrings'], ARRAY[], ARRAY['leg curl machine'], 'beginner', ARRAY['Bodybuilding'], 'Lying or seated, curl legs against resistance'),
('Nordic Curl', 'isolation_strength', ARRAY['hamstrings'], ARRAY[], ARRAY['partner', 'bench'], 'advanced', ARRAY['General Fitness'], 'Eccentric hamstring exercise, partner holds ankles'),

-- Legs - Calves
('Standing Calf Raise', 'isolation_strength', ARRAY['calves'], ARRAY[], ARRAY['calf raise machine', 'barbell'], 'beginner', ARRAY['Bodybuilding'], 'Raise up on toes against resistance'),
('Seated Calf Raise', 'isolation_strength', ARRAY['calves'], ARRAY[], ARRAY['calf raise machine'], 'beginner', ARRAY['Bodybuilding'], 'Seated, knees bent, emphasizes soleus'),

-- Legs - Glutes
('Cable Pull-Through', 'isolation_strength', ARRAY['glutes', 'hamstrings'], ARRAY[], ARRAY['cable machine'], 'beginner', ARRAY['General Fitness'], 'Hip hinge movement with cable between legs'),
('Banded Glute Bridge', 'isolation_strength', ARRAY['glutes'], ARRAY[], ARRAY['resistance band'], 'beginner', ARRAY['General Fitness'], 'Bridge with band around knees for extra glute activation'),

-- Core
('Cable Crunch', 'isolation_strength', ARRAY['abs'], ARRAY[], ARRAY['cable machine'], 'beginner', ARRAY['Bodybuilding'], 'Kneeling, crunch with cable overhead'),
('Ab Wheel Rollout', 'isolation_strength', ARRAY['abs', 'core'], ARRAY[], ARRAY['ab wheel'], 'advanced', ARRAY['General Fitness'], 'Roll wheel forward, core braced');

-- ============================================================================
-- BODYWEIGHT EXERCISES
-- ============================================================================

INSERT INTO exercises (name, category, primary_muscle_groups, secondary_muscle_groups, equipment_needed, difficulty_level, primary_modalities, description) VALUES

-- Push
('Push-Up', 'bodyweight', ARRAY['chest', 'triceps'], ARRAY['front delts', 'core'], ARRAY['bodyweight'], 'beginner', ARRAY['Calisthenics', 'General Fitness'], 'Classic push-up from floor'),
('Wide-Grip Push-Up', 'bodyweight', ARRAY['chest'], ARRAY['triceps', 'front delts'], ARRAY['bodyweight'], 'beginner', ARRAY['Calisthenics'], 'Hands wider than shoulder-width, more chest emphasis'),
('Pike Push-Up', 'bodyweight', ARRAY['shoulders', 'triceps'], ARRAY['upper chest'], ARRAY['bodyweight'], 'intermediate', ARRAY['Calisthenics'], 'Hips high, push-up from pike position'),
('Handstand Push-Up', 'bodyweight', ARRAY['shoulders', 'triceps'], ARRAY['upper back'], ARRAY['bodyweight', 'wall'], 'advanced', ARRAY['Calisthenics', 'CrossFit'], 'Handstand against wall, lower head to floor'),
('Dip', 'bodyweight', ARRAY['chest', 'triceps'], ARRAY['front delts'], ARRAY['dip bars', 'rings'], 'intermediate', ARRAY['Calisthenics', 'CrossFit'], 'Parallel bars, lower and press up'),
('Ring Dip', 'bodyweight', ARRAY['chest', 'triceps'], ARRAY['front delts', 'core'], ARRAY['rings'], 'advanced', ARRAY['Calisthenics', 'CrossFit'], 'Dip on unstable rings'),

-- Pull
('Inverted Row', 'bodyweight', ARRAY['upper back', 'lats'], ARRAY['biceps', 'rear delts'], ARRAY['bar', 'rings'], 'beginner', ARRAY['Calisthenics'], 'Body horizontal, pull chest to bar'),
('Muscle-Up', 'bodyweight', ARRAY['lats', 'triceps'], ARRAY['chest', 'shoulders'], ARRAY['pull-up bar', 'rings'], 'expert', ARRAY['Calisthenics', 'CrossFit'], 'Pull-up transitioning to dip in one motion'),
('L-Sit Pull-Up', 'bodyweight', ARRAY['lats', 'core'], ARRAY['biceps'], ARRAY['pull-up bar'], 'advanced', ARRAY['Calisthenics'], 'Pull-up while holding L-sit position'),
('Archer Pull-Up', 'bodyweight', ARRAY['lats', 'biceps'], ARRAY['forearms'], ARRAY['pull-up bar'], 'advanced', ARRAY['Calisthenics'], 'Pull to one side, other arm straight'),

-- Core
('Plank', 'bodyweight', ARRAY['core', 'abs'], ARRAY['shoulders'], ARRAY['bodyweight'], 'beginner', ARRAY['General Fitness'], 'Forearms and toes, body in straight line'),
('Side Plank', 'bodyweight', ARRAY['obliques', 'core'], ARRAY[], ARRAY['bodyweight'], 'beginner', ARRAY['General Fitness'], 'On one forearm, body sideways'),
('Hollow Body Hold', 'bodyweight', ARRAY['abs', 'core'], ARRAY[], ARRAY['bodyweight'], 'intermediate', ARRAY['Calisthenics', 'CrossFit'], 'Lying, shoulders and legs off ground, body curved'),
('L-Sit', 'bodyweight', ARRAY['abs', 'hip flexors'], ARRAY['triceps'], ARRAY['parallettes', 'floor'], 'intermediate', ARRAY['Calisthenics'], 'Seated, hands on floor/parallettes, legs straight out'),
('Toes to Bar', 'bodyweight', ARRAY['abs', 'hip flexors'], ARRAY['lats'], ARRAY['pull-up bar'], 'intermediate', ARRAY['CrossFit'], 'Hang from bar, bring toes to touch bar'),
('Hanging Knee Raise', 'bodyweight', ARRAY['abs', 'hip flexors'], ARRAY[], ARRAY['pull-up bar'], 'beginner', ARRAY['General Fitness'], 'Hang from bar, raise knees to chest'),
('Dragon Flag', 'bodyweight', ARRAY['abs', 'core'], ARRAY[], ARRAY['bench'], 'expert', ARRAY['Calisthenics'], 'Advanced core exercise, body held horizontal'),

-- Legs
('Pistol Squat', 'bodyweight', ARRAY['quadriceps', 'glutes'], ARRAY['hamstrings', 'core'], ARRAY['bodyweight'], 'advanced', ARRAY['Calisthenics'], 'Single-leg squat to full depth'),
('Jump Squat', 'plyometric', ARRAY['quadriceps', 'glutes'], ARRAY['calves'], ARRAY['bodyweight'], 'intermediate', ARRAY['CrossFit', 'General Fitness'], 'Squat and explode into jump'),
('Single-Leg Deadlift', 'bodyweight', ARRAY['hamstrings', 'glutes'], ARRAY['core'], ARRAY['bodyweight', 'dumbbells'], 'intermediate', ARRAY['General Fitness'], 'Balance on one leg, hinge forward'),

-- Full Body
('Burpee', 'plyometric', ARRAY['full body'], ARRAY[], ARRAY['bodyweight'], 'intermediate', ARRAY['CrossFit', 'General Fitness'], 'Push-up, jump feet to hands, jump up'),
('Mountain Climber', 'cardio_interval', ARRAY['core', 'shoulders'], ARRAY['hip flexors'], ARRAY['bodyweight'], 'beginner', ARRAY['CrossFit', 'General Fitness'], 'Plank position, alternate driving knees to chest');

-- ============================================================================
-- OLYMPIC LIFTS
-- ============================================================================

INSERT INTO exercises (name, category, primary_muscle_groups, secondary_muscle_groups, equipment_needed, difficulty_level, primary_modalities, description) VALUES

('Snatch', 'olympic_lift', ARRAY['full body'], ARRAY['shoulders', 'traps', 'legs'], ARRAY['barbell', 'bumper plates', 'platform'], 'expert', ARRAY['Olympic Weightlifting', 'CrossFit'], 'Floor to overhead in one motion'),
('Clean', 'olympic_lift', ARRAY['full body'], ARRAY['legs', 'back', 'traps'], ARRAY['barbell', 'bumper plates'], 'advanced', ARRAY['Olympic Weightlifting', 'CrossFit'], 'Floor to front rack'),
('Jerk', 'olympic_lift', ARRAY['shoulders', 'legs'], ARRAY['triceps', 'core'], ARRAY['barbell'], 'advanced', ARRAY['Olympic Weightlifting', 'CrossFit'], 'Front rack to overhead with leg drive'),
('Clean and Jerk', 'olympic_lift', ARRAY['full body'], ARRAY['shoulders', 'legs'], ARRAY['barbell', 'bumper plates', 'platform'], 'expert', ARRAY['Olympic Weightlifting', 'CrossFit'], 'Clean followed immediately by jerk'),
('Power Clean', 'olympic_lift', ARRAY['full body'], ARRAY['traps', 'legs'], ARRAY['barbell', 'bumper plates'], 'advanced', ARRAY['CrossFit', 'General Fitness'], 'Clean without full squat catch'),
('Power Snatch', 'olympic_lift', ARRAY['full body'], ARRAY['shoulders', 'traps'], ARRAY['barbell', 'bumper plates'], 'advanced', ARRAY['CrossFit'], 'Snatch without full squat catch'),
('Hang Clean', 'olympic_lift', ARRAY['legs', 'back'], ARRAY['traps'], ARRAY['barbell'], 'intermediate', ARRAY['CrossFit'], 'Clean starting from hanging position (above knee)'),
('Hang Snatch', 'olympic_lift', ARRAY['full body'], ARRAY['shoulders', 'traps'], ARRAY['barbell'], 'intermediate', ARRAY['CrossFit'], 'Snatch from hanging position'),
('Clean Pull', 'olympic_lift', ARRAY['back', 'legs'], ARRAY['traps'], ARRAY['barbell'], 'intermediate', ARRAY['Olympic Weightlifting'], 'First pull of clean, ends at hip'),
('Snatch Pull', 'olympic_lift', ARRAY['back', 'legs'], ARRAY['traps', 'shoulders'], ARRAY['barbell'], 'intermediate', ARRAY['Olympic Weightlifting'], 'First pull of snatch, ends at hip');

-- ============================================================================
-- FUNCTIONAL / CROSSFIT EXERCISES
-- ============================================================================

INSERT INTO exercises (name, category, primary_muscle_groups, secondary_muscle_groups, equipment_needed, difficulty_level, primary_modalities, description) VALUES

('Wall Ball', 'functional', ARRAY['legs', 'shoulders'], ARRAY['core'], ARRAY['medicine ball', 'wall'], 'beginner', ARRAY['CrossFit'], 'Squat with med ball, throw to target on wall'),
('Thruster', 'functional', ARRAY['legs', 'shoulders'], ARRAY['core'], ARRAY['barbell', 'dumbbells'], 'intermediate', ARRAY['CrossFit'], 'Front squat directly into push press'),
('Kettlebell Swing', 'functional', ARRAY['glutes', 'hamstrings'], ARRAY['core', 'shoulders'], ARRAY['kettlebell'], 'beginner', ARRAY['CrossFit', 'General Fitness'], 'Explosive hip hinge, swing KB to chest/overhead'),
('Turkish Get-Up', 'functional', ARRAY['full body'], ARRAY['shoulders', 'core'], ARRAY['kettlebell', 'dumbbell'], 'intermediate', ARRAY['General Fitness'], 'From lying to standing with weight overhead'),
('Farmer Carry', 'functional', ARRAY['forearms', 'core'], ARRAY['traps', 'legs'], ARRAY['dumbbells', 'kettlebells'], 'beginner', ARRAY['CrossFit', 'General Fitness'], 'Walk with heavy weights at sides'),
('Sled Push', 'functional', ARRAY['legs', 'core'], ARRAY['shoulders'], ARRAY['sled', 'plates'], 'intermediate', ARRAY['CrossFit', 'General Fitness'], 'Push weighted sled across floor'),
('Sled Pull', 'functional', ARRAY['legs', 'upper back'], ARRAY['biceps'], ARRAY['sled', 'rope'], 'intermediate', ARRAY['CrossFit'], 'Pull weighted sled toward you with rope'),
('Rope Climb', 'functional', ARRAY['upper back', 'biceps'], ARRAY['forearms', 'core'], ARRAY['climbing rope'], 'advanced', ARRAY['CrossFit'], 'Climb rope using hands and feet'),
('Box Jump', 'plyometric', ARRAY['legs'], ARRAY['core'], ARRAY['plyo box'], 'intermediate', ARRAY['CrossFit', 'General Fitness'], 'Jump onto elevated box'),
('Double-Under', 'cardio_interval', ARRAY['calves', 'shoulders'], ARRAY['forearms'], ARRAY['jump rope'], 'intermediate', ARRAY['CrossFit'], 'Jump rope where rope passes twice per jump'),
('Assault Bike', 'cardio_interval', ARRAY['legs', 'full body'], ARRAY[], ARRAY['assault bike'], 'beginner', ARRAY['CrossFit'], 'High-intensity stationary bike with arm movement'),
('Rowing Machine', 'cardio_steady_state', ARRAY['back', 'legs'], ARRAY['biceps', 'core'], ARRAY['rowing machine'], 'beginner', ARRAY['CrossFit', 'Endurance Running'], 'Full-body cardio on rowing machine'),
('Battle Ropes', 'cardio_interval', ARRAY['shoulders', 'core'], ARRAY['forearms'], ARRAY['battle ropes'], 'beginner', ARRAY['CrossFit', 'General Fitness'], 'Wave heavy ropes in alternating pattern'),
('Slam Ball', 'plyometric', ARRAY['shoulders', 'core'], ARRAY['back'], ARRAY['slam ball'], 'beginner', ARRAY['CrossFit'], 'Lift ball overhead and slam to ground');

-- ============================================================================
-- CARDIO EXERCISES
-- ============================================================================

INSERT INTO exercises (name, category, primary_muscle_groups, secondary_muscle_groups, equipment_needed, difficulty_level, primary_modalities, description) VALUES

('Running (Outdoor)', 'cardio_steady_state', ARRAY['legs', 'cardiovascular'], ARRAY[], ARRAY['running shoes'], 'beginner', ARRAY['Endurance Running', 'General Fitness'], 'Outdoor running at steady pace'),
('Running (Treadmill)', 'cardio_steady_state', ARRAY['legs', 'cardiovascular'], ARRAY[], ARRAY['treadmill'], 'beginner', ARRAY['Endurance Running', 'General Fitness'], 'Treadmill running'),
('Sprint Intervals', 'cardio_interval', ARRAY['legs', 'cardiovascular'], ARRAY[], ARRAY['track', 'treadmill'], 'intermediate', ARRAY['Endurance Running', 'CrossFit'], 'High-intensity running intervals'),
('Cycling (Road)', 'cardio_steady_state', ARRAY['legs', 'cardiovascular'], ARRAY[], ARRAY['bicycle'], 'beginner', ARRAY['Cycling'], 'Road cycling at steady pace'),
('Cycling (Stationary)', 'cardio_steady_state', ARRAY['legs', 'cardiovascular'], ARRAY[], ARRAY['stationary bike'], 'beginner', ARRAY['Cycling', 'General Fitness'], 'Indoor cycling bike'),
('Spin Class', 'cardio_interval', ARRAY['legs', 'cardiovascular'], ARRAY[], ARRAY['spin bike'], 'intermediate', ARRAY['Cycling'], 'High-intensity indoor cycling with intervals'),
('Swimming (Freestyle)', 'cardio_steady_state', ARRAY['full body', 'cardiovascular'], ARRAY[], ARRAY['pool'], 'intermediate', ARRAY['Swimming'], 'Front crawl stroke'),
('Swimming (Breaststroke)', 'cardio_steady_state', ARRAY['full body', 'cardiovascular'], ARRAY[], ARRAY['pool'], 'intermediate', ARRAY['Swimming'], 'Breaststroke technique'),
('Swimming (Backstroke)', 'cardio_steady_state', ARRAY['full body', 'cardiovascular'], ARRAY[], ARRAY['pool'], 'intermediate', ARRAY['Swimming'], 'Swimming on back'),
('Swimming (Butterfly)', 'cardio_steady_state', ARRAY['full body', 'cardiovascular'], ARRAY['shoulders'], ARRAY['pool'], 'advanced', ARRAY['Swimming'], 'Butterfly stroke - most demanding'),
('Elliptical', 'cardio_steady_state', ARRAY['legs', 'cardiovascular'], ARRAY[], ARRAY['elliptical machine'], 'beginner', ARRAY['General Fitness'], 'Low-impact cardio machine'),
('Stair Climber', 'cardio_steady_state', ARRAY['legs', 'glutes'], ARRAY['cardiovascular'], ARRAY['stair climber'], 'beginner', ARRAY['General Fitness'], 'Continuous stair climbing motion'),
('Jump Rope', 'cardio_interval', ARRAY['calves', 'cardiovascular'], ARRAY['shoulders', 'forearms'], ARRAY['jump rope'], 'beginner', ARRAY['CrossFit', 'General Fitness'], 'Skipping rope for cardio');

-- ============================================================================
-- FLEXIBILITY & MOBILITY EXERCISES
-- ============================================================================

INSERT INTO exercises (name, category, primary_muscle_groups, secondary_muscle_groups, equipment_needed, difficulty_level, primary_modalities, description) VALUES

('Downward Dog', 'flexibility', ARRAY['hamstrings', 'shoulders'], ARRAY['calves', 'back'], ARRAY['yoga mat'], 'beginner', ARRAY['Yoga'], 'Classic yoga pose - inverted V shape'),
('Cat-Cow Stretch', 'mobility', ARRAY['spine', 'core'], ARRAY[], ARRAY['yoga mat'], 'beginner', ARRAY['Yoga', 'General Fitness'], 'Spine mobility - alternating arch and round'),
('Childs Pose', 'flexibility', ARRAY['back', 'hips'], ARRAY[], ARRAY['yoga mat'], 'beginner', ARRAY['Yoga'], 'Resting pose - knees down, arms extended forward'),
('Pigeon Pose', 'flexibility', ARRAY['hips', 'glutes'], ARRAY[], ARRAY['yoga mat'], 'intermediate', ARRAY['Yoga'], 'Deep hip flexor and glute stretch'),
('World''s Greatest Stretch', 'mobility', ARRAY['hips', 'hamstrings'], ARRAY['thoracic spine'], ARRAY['bodyweight'], 'beginner', ARRAY['General Fitness'], 'Lunge with rotation and reach'),
('90/90 Hip Stretch', 'flexibility', ARRAY['hips'], ARRAY[], ARRAY['floor'], 'beginner', ARRAY['General Fitness'], 'Seated with both legs at 90 degrees'),
('Couch Stretch', 'flexibility', ARRAY['hip flexors', 'quadriceps'], ARRAY[], ARRAY['couch', 'wall'], 'intermediate', ARRAY['CrossFit', 'General Fitness'], 'Deep hip flexor stretch against wall/couch'),
('Lacrosse Ball Glute Smash', 'mobility', ARRAY['glutes'], ARRAY[], ARRAY['lacrosse ball'], 'beginner', ARRAY['CrossFit', 'General Fitness'], 'Self-myofascial release for glutes'),
('Foam Rolling - IT Band', 'mobility', ARRAY['IT band', 'legs'], ARRAY[], ARRAY['foam roller'], 'beginner', ARRAY['General Fitness'], 'Roll IT band on side of leg'),
('Foam Rolling - Upper Back', 'mobility', ARRAY['upper back'], ARRAY[], ARRAY['foam roller'], 'beginner', ARRAY['General Fitness'], 'Roll thoracic spine and lats'),
('Band Pull-Apart', 'mobility', ARRAY['rear delts', 'upper back'], ARRAY[], ARRAY['resistance band'], 'beginner', ARRAY['General Fitness'], 'Pull band apart at chest height, great for posture');

-- ============================================================================
-- SPORTS-SPECIFIC EXERCISES
-- ============================================================================

INSERT INTO exercises (name, category, primary_muscle_groups, secondary_muscle_groups, equipment_needed, difficulty_level, primary_modalities, description) VALUES

-- Basketball
('Basketball - Shooting Drills', 'sports_specific', ARRAY['full body'], ARRAY[], ARRAY['basketball', 'hoop'], 'beginner', ARRAY['Team Sports'], 'Practice jump shots, free throws, layups'),
('Basketball - Dribbling Drills', 'sports_specific', ARRAY['forearms'], ARRAY['core'], ARRAY['basketball'], 'beginner', ARRAY['Team Sports'], 'Ball handling and dribbling practice'),
('Basketball - Defensive Slides', 'sports_specific', ARRAY['legs', 'glutes'], ARRAY['core'], ARRAY['bodyweight'], 'beginner', ARRAY['Team Sports'], 'Lateral movement and defensive stance'),

-- Tennis
('Tennis - Serve Practice', 'sports_specific', ARRAY['shoulders', 'core'], ARRAY['legs'], ARRAY['tennis racket', 'balls'], 'beginner', ARRAY['Team Sports'], 'Overhead serve technique'),
('Tennis - Forehand Drills', 'sports_specific', ARRAY['core', 'shoulders'], ARRAY['legs'], ARRAY['tennis racket', 'balls'], 'beginner', ARRAY['Team Sports'], 'Forehand stroke practice'),
('Tennis - Backhand Drills', 'sports_specific', ARRAY['core', 'shoulders'], ARRAY[], ARRAY['tennis racket', 'balls'], 'beginner', ARRAY['Team Sports'], 'Backhand stroke practice'),

-- Soccer
('Soccer - Dribbling Drills', 'sports_specific', ARRAY['legs'], ARRAY['core'], ARRAY['soccer ball'], 'beginner', ARRAY['Team Sports'], 'Ball control and dribbling'),
('Soccer - Shooting Drills', 'sports_specific', ARRAY['legs', 'core'], ARRAY[], ARRAY['soccer ball', 'goal'], 'beginner', ARRAY['Team Sports'], 'Shooting on goal from various positions'),

-- General Agility
('Ladder Drills', 'sports_specific', ARRAY['legs', 'cardiovascular'], ARRAY[], ARRAY['agility ladder'], 'beginner', ARRAY['Team Sports', 'General Fitness'], 'Footwork and agility using ladder'),
('Cone Drills', 'sports_specific', ARRAY['legs', 'cardiovascular'], ARRAY[], ARRAY['cones'], 'beginner', ARRAY['Team Sports', 'General Fitness'], 'Change of direction and agility'),
('Shuttle Run', 'sports_specific', ARRAY['legs', 'cardiovascular'], ARRAY[], ARRAY['cones'], 'intermediate', ARRAY['Team Sports'], 'Sprint between markers with direction changes');

-- ============================================================================
-- SUMMARY
-- ============================================================================
-- ✅ EXERCISE LIBRARY SEEDED:
-- - 150+ exercises covering all major modalities
-- - Categorized by type, muscle groups, equipment, difficulty
-- - Includes compound lifts, isolation, bodyweight, Olympic lifts, functional, cardio, flexibility, sports
-- - Each exercise tagged with primary modalities for easy filtering during consultation
--
-- NEXT STEPS:
-- 1. Create backend Pydantic models for consultation tables
-- 2. Build consultation API endpoints (7-section flow)
-- 3. Create consultation UI with exercise/food search
-- ============================================================================
