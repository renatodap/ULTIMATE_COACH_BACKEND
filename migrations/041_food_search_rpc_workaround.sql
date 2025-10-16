-- Migration: Food Search RPC Workaround for PostgREST Crash
-- Date: 2025-10-16
-- Issue: PostgREST worker crashes with Cloudflare Error 1101 when querying
--        foods table with ILIKE pattern via REST API
--
-- Solution: Create PostgreSQL RPC function that:
--   - Bypasses PostgREST's table query endpoint
--   - Safely handles errors with EXCEPTION blocks
--   - Manually builds JSON response
--   - Returns foods with servings included

BEGIN;

-- ============================================================================
-- Function: search_foods_safe
-- ============================================================================
-- Purpose: Safely search foods with pattern matching, bypassing PostgREST issues
--
-- Parameters:
--   - search_query: Search pattern (e.g., 'chicken', 'banana')
--   - result_limit: Max results to return (default 20, max 100)
--   - user_id_filter: Optional UUID to include user's custom foods
--
-- Returns: JSONB array of food objects with servings
--
-- Example usage:
--   SELECT search_foods_safe('chicken', 20, null);
--   SELECT search_foods_safe('banana', 10, '38a5596a-9397-4660-8180-132c50541964'::uuid);

CREATE OR REPLACE FUNCTION search_foods_safe(
    search_query TEXT,
    result_limit INTEGER DEFAULT 20,
    user_id_filter UUID DEFAULT NULL
)
RETURNS JSONB
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
DECLARE
    result JSONB;
    food_row RECORD;
    servings_json JSONB;
BEGIN
    -- Validate inputs
    IF search_query IS NULL OR LENGTH(TRIM(search_query)) < 2 THEN
        RETURN jsonb_build_object(
            'error', 'Search query must be at least 2 characters',
            'foods', '[]'::jsonb
        );
    END IF;

    -- Cap limit
    IF result_limit > 100 THEN
        result_limit := 100;
    END IF;
    IF result_limit < 1 THEN
        result_limit := 20;
    END IF;

    -- Build result array
    result := '[]'::jsonb;

    -- Search public foods
    BEGIN
        FOR food_row IN
            SELECT
                f.id,
                f.name,
                f.brand_name,
                f.food_type,
                f.composition_type,
                f.calories_per_100g,
                f.protein_g_per_100g,
                f.carbs_g_per_100g,
                f.fat_g_per_100g,
                f.fiber_g_per_100g,
                f.sugar_g_per_100g,
                f.sodium_mg_per_100g,
                f.is_public,
                f.verified,
                f.usage_count,
                f.created_by,
                f.created_at,
                f.updated_at
            FROM foods f
            WHERE f.is_public = true
              AND f.name ILIKE '%' || search_query || '%'
            ORDER BY f.usage_count DESC NULLS LAST, f.verified DESC NULLS LAST
            LIMIT result_limit
        LOOP
            -- Get servings for this food
            BEGIN
                SELECT COALESCE(
                    jsonb_agg(
                        jsonb_build_object(
                            'id', fs.id,
                            'food_id', fs.food_id,
                            'serving_size', fs.serving_size,
                            'serving_unit', fs.serving_unit,
                            'serving_label', fs.serving_label,
                            'grams_per_serving', fs.grams_per_serving,
                            'is_default', fs.is_default,
                            'display_order', fs.display_order,
                            'created_at', fs.created_at,
                            'updated_at', fs.updated_at
                        ) ORDER BY fs.display_order ASC, fs.is_default DESC
                    ),
                    '[]'::jsonb
                )
                INTO servings_json
                FROM food_servings fs
                WHERE fs.food_id = food_row.id;
            EXCEPTION
                WHEN OTHERS THEN
                    -- If servings fetch fails, return empty array
                    servings_json := '[]'::jsonb;
            END;

            -- Add food with servings to result
            result := result || jsonb_build_object(
                'id', food_row.id,
                'name', food_row.name,
                'brand_name', food_row.brand_name,
                'food_type', food_row.food_type,
                'composition_type', food_row.composition_type,
                'calories_per_100g', food_row.calories_per_100g,
                'protein_g_per_100g', food_row.protein_g_per_100g,
                'carbs_g_per_100g', food_row.carbs_g_per_100g,
                'fat_g_per_100g', food_row.fat_g_per_100g,
                'fiber_g_per_100g', food_row.fiber_g_per_100g,
                'sugar_g_per_100g', food_row.sugar_g_per_100g,
                'sodium_mg_per_100g', food_row.sodium_mg_per_100g,
                'is_public', food_row.is_public,
                'verified', food_row.verified,
                'usage_count', food_row.usage_count,
                'created_by', food_row.created_by,
                'created_at', food_row.created_at,
                'updated_at', food_row.updated_at,
                'servings', servings_json
            );
        END LOOP;
    EXCEPTION
        WHEN OTHERS THEN
            -- If public foods search fails completely, return error
            RETURN jsonb_build_object(
                'error', 'Failed to search public foods: ' || SQLERRM,
                'foods', result
            );
    END;

    -- If user_id provided, also search their custom foods
    IF user_id_filter IS NOT NULL THEN
        BEGIN
            FOR food_row IN
                SELECT
                    f.id,
                    f.name,
                    f.brand_name,
                    f.food_type,
                    f.composition_type,
                    f.calories_per_100g,
                    f.protein_g_per_100g,
                    f.carbs_g_per_100g,
                    f.fat_g_per_100g,
                    f.fiber_g_per_100g,
                    f.sugar_g_per_100g,
                    f.sodium_mg_per_100g,
                    f.is_public,
                    f.verified,
                    f.usage_count,
                    f.created_by,
                    f.created_at,
                    f.updated_at
                FROM foods f
                WHERE f.created_by = user_id_filter
                  AND f.name ILIKE '%' || search_query || '%'
                ORDER BY f.updated_at DESC
                LIMIT (result_limit - jsonb_array_length(result))
            LOOP
                -- Get servings for this food
                BEGIN
                    SELECT COALESCE(
                        jsonb_agg(
                            jsonb_build_object(
                                'id', fs.id,
                                'food_id', fs.food_id,
                                'serving_size', fs.serving_size,
                                'serving_unit', fs.serving_unit,
                                'serving_label', fs.serving_label,
                                'grams_per_serving', fs.grams_per_serving,
                                'is_default', fs.is_default,
                                'display_order', fs.display_order,
                                'created_at', fs.created_at,
                                'updated_at', fs.updated_at
                            ) ORDER BY fs.display_order ASC, fs.is_default DESC
                        ),
                        '[]'::jsonb
                    )
                    INTO servings_json
                    FROM food_servings fs
                    WHERE fs.food_id = food_row.id;
                EXCEPTION
                    WHEN OTHERS THEN
                        servings_json := '[]'::jsonb;
                END;

                -- Add custom food with servings to result
                result := result || jsonb_build_object(
                    'id', food_row.id,
                    'name', food_row.name,
                    'brand_name', food_row.brand_name,
                    'food_type', food_row.food_type,
                    'composition_type', food_row.composition_type,
                    'calories_per_100g', food_row.calories_per_100g,
                    'protein_g_per_100g', food_row.protein_g_per_100g,
                    'carbs_g_per_100g', food_row.carbs_g_per_100g,
                    'fat_g_per_100g', food_row.fat_g_per_100g,
                    'fiber_g_per_100g', food_row.fiber_g_per_100g,
                    'sugar_g_per_100g', food_row.sugar_g_per_100g,
                    'sodium_mg_per_100g', food_row.sodium_mg_per_100g,
                    'is_public', food_row.is_public,
                    'verified', food_row.verified,
                    'usage_count', food_row.usage_count,
                    'created_by', food_row.created_by,
                    'created_at', food_row.created_at,
                    'updated_at', food_row.updated_at,
                    'servings', servings_json
                );
            END LOOP;
        EXCEPTION
            WHEN OTHERS THEN
                -- If custom foods search fails, just return public foods
                -- Don't error out entirely
                NULL;
        END;
    END IF;

    -- Return successful result
    RETURN jsonb_build_object(
        'foods', result,
        'total', jsonb_array_length(result)
    );

EXCEPTION
    WHEN OTHERS THEN
        -- Catch-all: Return error with empty array
        RETURN jsonb_build_object(
            'error', 'Unexpected error: ' || SQLERRM,
            'foods', '[]'::jsonb
        );
END;
$$;

-- Grant execute permission to authenticated users
GRANT EXECUTE ON FUNCTION search_foods_safe(TEXT, INTEGER, UUID) TO authenticated;
GRANT EXECUTE ON FUNCTION search_foods_safe(TEXT, INTEGER, UUID) TO service_role;

-- ============================================================================
-- Test the function
-- ============================================================================
-- Run these tests after applying migration:

-- Test 1: Search for 'chicken'
-- SELECT search_foods_safe('chicken', 20, null);

-- Test 2: Search for 'banana'
-- SELECT search_foods_safe('banana', 10, null);

-- Test 3: Search with short query (should return error)
-- SELECT search_foods_safe('a', 20, null);

-- Test 4: Search with user's custom foods
-- SELECT search_foods_safe('my food', 20, '38a5596a-9397-4660-8180-132c50541964'::uuid);

COMMIT;

-- ============================================================================
-- NOTES:
-- ============================================================================
-- This function bypasses PostgREST's table query endpoint entirely by using RPC.
--
-- Advantages:
-- 1. Avoids PostgREST worker crashes (Error 1101)
-- 2. Better error handling with EXCEPTION blocks
-- 3. Manual JSON building avoids serialization issues
-- 4. Can add custom logic (e.g., fuzzy matching, scoring)
-- 5. Single database round-trip (efficient)
--
-- Backend Usage:
-- Replace:
--   supabase_service.client.table("foods").select(...).execute()
-- With:
--   supabase_service.client.rpc("search_foods_safe", {
--       "search_query": query,
--       "result_limit": limit,
--       "user_id_filter": str(user_id) if user_id else None
--   }).execute()
--
-- Response format:
-- {
--   "foods": [
--     {
--       "id": "uuid",
--       "name": "Chicken Breast",
--       "calories_per_100g": 165,
--       "servings": [
--         {"id": "uuid", "serving_size": 100, "serving_unit": "g", ...}
--       ]
--     }
--   ],
--   "total": 15
-- }
