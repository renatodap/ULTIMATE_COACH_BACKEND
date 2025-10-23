-- ============================================================================
-- Update Training Modalities - Enhanced Onboarding
-- ============================================================================
-- Version: 1.1.0
-- Created: 2025-10-21
-- Description: Rename "Bodybuilding" to "Strength Training" and add searchable
--              sports modalities for enhanced onboarding flow
-- ============================================================================

-- Update "Bodybuilding" to "Strength Training"
UPDATE training_modalities
SET
  name = 'Strength Training',
  description = 'Resistance training for muscle building and strength development using weights, machines, or bodyweight',
  typical_frequency_per_week = 4
WHERE name = 'Bodybuilding';

-- Add more searchable modalities for diverse users
INSERT INTO training_modalities (name, description, typical_frequency_per_week, equipment_required, display_order)
VALUES
  ('Tennis', 'Racquet sport for cardiovascular fitness, agility, and hand-eye coordination', 3, ARRAY['tennis racquet', 'tennis balls', 'court access'], 13),
  ('Rock Climbing', 'Climbing sport for strength, problem-solving, and full-body fitness', 3, ARRAY['climbing shoes', 'harness', 'chalk'], 14),
  ('Hiking', 'Outdoor walking on trails for cardiovascular fitness and leg strength', 2, ARRAY['hiking boots', 'backpack'], 15),
  ('Golf', 'Walking-based sport with rotational strength and precision', 2, ARRAY['golf clubs', 'golf balls', 'course access'], 16),
  ('Rowing', 'Full-body cardiovascular and strength exercise on water or machine', 4, ARRAY['rowing machine or boat'], 17),
  ('Dance', 'Movement-based fitness including ballet, hip-hop, ballroom, salsa', 3, ARRAY['dance shoes'], 18),
  ('Pilates', 'Low-impact core and flexibility training with controlled movements', 3, ARRAY['mat', 'reformer'], 19),
  ('Softball/Baseball', 'Team sport combining sprinting, throwing, and rotational power', 2, ARRAY['bat', 'glove', 'ball'], 20),
  ('Volleyball', 'Jumping and agility-based team sport', 2, ARRAY['volleyball', 'court access'], 21),
  ('Pickleball', 'Fast-paced paddle sport combining tennis, badminton, and ping-pong', 3, ARRAY['paddle', 'pickleballs', 'court access'], 22),
  ('Skiing/Snowboarding', 'Winter sports for leg strength and balance', 1, ARRAY['skis/snowboard', 'boots', 'mountain access'], 23),
  ('Skateboarding', 'Board sport for balance, core strength, and trick progression', 3, ARRAY['skateboard', 'helmet'], 24),
  ('Surfing', 'Water sport for upper body strength, balance, and core', 2, ARRAY['surfboard', 'wetsuit', 'ocean access'], 25),
  ('Gymnastics', 'Bodyweight strength, flexibility, and skill-based training', 4, ARRAY['gym access', 'mats'], 26),
  ('Bouldering', 'Climbing without ropes on shorter walls, focused on power and problem-solving', 3, ARRAY['climbing shoes', 'chalk'], 27),
  ('Track & Field', 'Running, jumping, and throwing events for speed and power', 4, ARRAY['running shoes', 'track access'], 28),
  ('Ultimate Frisbee', 'Fast-paced team sport combining running and throwing', 2, ARRAY['frisbee'], 29),
  ('Racquetball/Squash', 'Indoor racquet sports for cardio and agility', 3, ARRAY['racquet', 'ball', 'court access'], 30),
  ('Parkour', 'Urban movement training for agility, strength, and creativity', 3, ARRAY['minimal equipment'], 31),
  ('Ice Hockey', 'Fast-paced team sport on ice combining skating, stickhandling, and shooting', 3, ARRAY['skates', 'stick', 'pads', 'rink access'], 32),
  ('Lacrosse', 'Team sport combining running, stick skills, and contact', 3, ARRAY['stick', 'ball', 'pads'], 33),
  ('Rugby', 'Full-contact team sport for strength, speed, and endurance', 3, ARRAY['rugby ball', 'field access'], 34),
  ('Football (American)', 'Team sport combining strength, speed, and strategy', 3, ARRAY['football', 'pads', 'field access'], 35),
  ('Soccer (Football)', 'Team sport for cardiovascular fitness, agility, and skill', 3, ARRAY['soccer ball', 'cleats', 'field access'], 36),
  ('Badminton', 'Fast racquet sport for hand-eye coordination and cardio', 3, ARRAY['racquet', 'shuttlecock', 'court access'], 37),
  ('Table Tennis', 'Fast-paced paddle sport for reflexes and hand-eye coordination', 3, ARRAY['paddle', 'balls', 'table'], 38),
  ('Fencing', 'Sword sport for agility, strategy, and precision', 3, ARRAY['foil/epee/sabre', 'mask', 'protective gear'], 39),
  ('Archery', 'Precision sport for upper body strength and focus', 2, ARRAY['bow', 'arrows', 'range access'], 40),
  ('Equestrian', 'Horse riding for core strength, balance, and coordination', 3, ARRAY['horse access', 'riding gear'], 41),
  ('Stand-Up Paddleboarding (SUP)', 'Water sport for core strength and balance', 2, ARRAY['paddleboard', 'paddle', 'water access'], 42),
  ('Kayaking/Canoeing', 'Water sport for upper body and core strength', 2, ARRAY['kayak/canoe', 'paddle', 'water access'], 43),
  ('Mountain Biking', 'Off-road cycling for leg strength and cardiovascular fitness', 3, ARRAY['mountain bike', 'helmet', 'trail access'], 44),
  ('BMX', 'Bike sport for tricks, jumps, and skill progression', 3, ARRAY['BMX bike', 'helmet'], 45),
  ('Cheerleading', 'Team sport combining acrobatics, dance, and stunts', 4, ARRAY['mat', 'gym access'], 46),
  ('Jump Rope', 'Cardiovascular exercise for coordination and conditioning', 5, ARRAY['jump rope'], 47),
  ('Kettlebell Training', 'Dynamic strength and conditioning with kettlebells', 4, ARRAY['kettlebells'], 48),
  ('TRX/Suspension Training', 'Bodyweight training using suspension straps', 4, ARRAY['TRX straps', 'anchor point'], 49),
  ('Tai Chi', 'Slow-movement martial art for balance, flexibility, and mindfulness', 3, ARRAY['minimal equipment'], 50)
ON CONFLICT (name) DO NOTHING;

-- ============================================================================
-- SUMMARY
-- ============================================================================
-- ✅ Updated "Bodybuilding" to "Strength Training" for more inclusive terminology
-- ✅ Added 38 new training modalities covering diverse sports and activities
-- ✅ Total modalities now: 50+ options for users to search and select
-- ✅ Ready for enhanced onboarding flow with modality search functionality
-- ============================================================================
