-- Migration: Fix RPC Servings Return
-- Date: 2025-10-16
-- Issue: RPC function search_foods_safe returns foods but with empty servings array
-- Root Cause: UUID/timestamp types causing silent JSONB serialization failures
--
-- Solution: Cast all UUIDs and timestamps to text for JSONB compatibility

BEGIN;

-- Drop and recreate the function with proper type casting
DROP FUNCTION IF EXISTS search_foods_safe(TEXT, INTEGER, UUID);

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
            -- Get servings for this food (with explicit casting for JSONB compatibility)
            BEGIN
                SELECT COALESCE(
                    jsonb_agg(
                        jsonb_build_object(
                            'id', fs.id::text,
                            'food_id', fs.food_id::text,
                            'serving_size', fs.serving_size,
                            'serving_unit', fs.serving_unit,
                            'serving_label', fs.serving_label,
                            'grams_per_serving', fs.grams_per_serving,
                            'is_default', fs.is_default,
                            'display_order', fs.display_order,
                            'created_at', fs.created_at::text,
                            'updated_at', fs.updated_at::text
                        ) ORDER BY fs.display_order ASC NULLS LAST, fs.is_default DESC NULLS LAST
                    ),
                    '[]'::jsonb
                )
                INTO servings_json
                FROM food_servings fs
                WHERE fs.food_id = food_row.id;
            EXCEPTION
                WHEN OTHERS THEN
                    -- Log warning and return empty servings
                    RAISE WARNING 'Failed to fetch servings for food_id %: %', food_row.id, SQLERRM;
                    servings_json := '[]'::jsonb;
            END;

            -- Add food with servings to result (cast UUIDs/timestamps to text)
            result := result || jsonb_build_object(
                'id', food_row.id::text,
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
                'created_by', food_row.created_by::text,
                'created_at', food_row.created_at::text,
                'updated_at', food_row.updated_at::text,
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
                -- Get servings for this food (with explicit casting)
                BEGIN
                    SELECT COALESCE(
                        jsonb_agg(
                            jsonb_build_object(
                                'id', fs.id::text,
                                'food_id', fs.food_id::text,
                                'serving_size', fs.serving_size,
                                'serving_unit', fs.serving_unit,
                                'serving_label', fs.serving_label,
                                'grams_per_serving', fs.grams_per_serving,
                                'is_default', fs.is_default,
                                'display_order', fs.display_order,
                                'created_at', fs.created_at::text,
                                'updated_at', fs.updated_at::text
                            ) ORDER BY fs.display_order ASC NULLS LAST, fs.is_default DESC NULLS LAST
                        ),
                        '[]'::jsonb
                    )
                    INTO servings_json
                    FROM food_servings fs
                    WHERE fs.food_id = food_row.id;
                EXCEPTION
                    WHEN OTHERS THEN
                        RAISE WARNING 'Failed to fetch servings for food_id %: %', food_row.id, SQLERRM;
                        servings_json := '[]'::jsonb;
                END;

                -- Add custom food with servings to result
                result := result || jsonb_build_object(
                    'id', food_row.id::text,
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
                    'created_by', food_row.created_by::text,
                    'created_at', food_row.created_at::text,
                    'updated_at', food_row.updated_at::text,
                    'servings', servings_json
                );
            END LOOP;
        EXCEPTION
            WHEN OTHERS THEN
                -- If custom foods search fails, just return public foods
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

-- Grant execute permission
GRANT EXECUTE ON FUNCTION search_foods_safe(TEXT, INTEGER, UUID) TO authenticated;
GRANT EXECUTE ON FUNCTION search_foods_safe(TEXT, INTEGER, UUID) TO service_role;

COMMIT;
