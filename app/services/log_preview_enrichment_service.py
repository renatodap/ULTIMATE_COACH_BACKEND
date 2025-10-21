"""
Log Preview Enrichment Service

Enhances log previews with:
- Matched foods from database (with alternatives)
- Editable fields marked
- Validation warnings
- User history prioritization

This service runs BEFORE showing preview to user, allowing them to:
- See what foods were matched
- Change matches if wrong
- Edit quantities/grams
- Add missing foods as custom
"""

import structlog
from typing import Dict, Any, List, Optional, Tuple
from uuid import UUID

logger = structlog.get_logger()


class LogPreviewEnrichmentService:
    """
    Enriches log previews with food matching and editability metadata.

    Key Features:
    - Fuzzy food matching with confidence scores
    - Top 3 alternatives for user selection
    - Editable field markers
    - Validation warnings (low confidence, missing foods)
    """

    def __init__(self, supabase_client):
        self.supabase = supabase_client

    async def enrich_meal_preview(
        self,
        structured_data: Dict[str, Any],
        user_id: str
    ) -> Tuple[Dict[str, Any], List[str]]:
        """
        Enrich meal preview with food matches and alternatives.

        Args:
            structured_data: LLM-extracted data with foods array
            user_id: User UUID for history prioritization

        Returns:
            Tuple of (enriched_data, warnings)

        enriched_data format:
        {
            "meal_type": "breakfast",
            "items": [
                {
                    "original_llm_text": "3 eggs",
                    "matched_food": {
                        "id": "uuid-123",
                        "name": "Whole Eggs (Large)",
                        "calories_per_100g": 143,
                        ...
                    },
                    "match_confidence": 0.92,
                    "match_reason": "user_history",
                    "alternatives": [
                        {
                            "id": "uuid-456",
                            "name": "Egg Whites Only",
                            "calories_per_100g": 52
                        },
                        ...
                    ],
                    "quantity": 3,
                    "unit": "pieces",
                    "estimated_grams": 180,
                    "calculated_nutrition": {
                        "grams": 180,
                        "calories": 257,
                        "protein_g": 22.3,
                        "carbs_g": 1.1,
                        "fat_g": 17.6
                    },
                    "editable_fields": ["quantity", "grams", "matched_food"],
                    "warnings": []
                }
            ],
            "nutrition_summary": {
                "calories": 257,
                "protein_g": 22.3,
                "carbs_g": 1.1,
                "fat_g": 17.6
            },
            "warnings": [],
            "missing_foods": []
        }
        """
        logger.info("[LogEnrichment] 🔍 Enriching meal preview with food matches")

        foods = structured_data.get("foods", [])
        if not foods:
            logger.warning("[LogEnrichment] ⚠️ No foods in structured_data")
            return structured_data, ["No foods detected in message"]

        enriched_items = []
        missing_foods = []
        all_warnings = []
        total_nutrition = {
            "calories": 0,
            "protein_g": 0,
            "carbs_g": 0,
            "fat_g": 0
        }

        for idx, food_data in enumerate(foods):
            food_name = food_data.get("name", "Unknown")
            quantity = food_data.get("quantity")
            unit = food_data.get("unit", "grams")
            estimated_grams = food_data.get("estimated_grams", 100)

            logger.info(
                f"[LogEnrichment] Processing food {idx+1}/{len(foods)}: "
                f"'{food_name}' ({quantity} {unit}, ~{estimated_grams}g)"
            )

            # Search for food with alternatives
            match_result = await self._search_food_with_alternatives(
                food_name=food_name,
                user_id=user_id,
                unit=unit,
                top_n=3
            )

            if not match_result:
                # Food not found in database
                logger.warning(f"[LogEnrichment] ❌ Food not found: '{food_name}'")
                missing_foods.append({
                    "name": food_name,
                    "quantity": quantity,
                    "unit": unit,
                    "estimated_grams": estimated_grams,
                    "suggested_action": "create_custom_food"
                })

                # Add warning
                all_warnings.append(f"'{food_name}' not found in database - you can add it as custom food")
                continue

            matched_food, match_score, match_reason, alternatives = match_result

            # Calculate nutrition
            nutrition = self._calculate_nutrition(
                food=matched_food,
                quantity=quantity,
                unit=unit,
                estimated_grams=estimated_grams
            )

            # Build enriched item
            item_warnings = []
            if match_score < 85:
                item_warnings.append(f"Low match confidence ({match_score:.0f}%) - verify this is correct")

            enriched_item = {
                "original_llm_text": f"{quantity} {unit} {food_name}" if quantity else food_name,
                "matched_food": {
                    "id": matched_food["id"],
                    "name": matched_food["name"],
                    "brand_name": matched_food.get("brand_name"),
                    "calories_per_100g": matched_food["calories_per_100g"],
                    "protein_g_per_100g": matched_food["protein_g_per_100g"],
                    "carbs_g_per_100g": matched_food["carbs_g_per_100g"],
                    "fat_g_per_100g": matched_food["fat_g_per_100g"],
                    "composition_type": matched_food.get("composition_type", "simple")
                },
                "match_confidence": match_score,
                "match_reason": match_reason,
                "alternatives": [
                    {
                        "id": alt["id"],
                        "name": alt["name"],
                        "brand_name": alt.get("brand_name"),
                        "calories_per_100g": alt["calories_per_100g"]
                    }
                    for alt in alternatives
                ],
                "quantity": quantity,
                "unit": unit,
                "estimated_grams": estimated_grams,
                "calculated_nutrition": nutrition,
                "editable_fields": ["quantity", "estimated_grams", "matched_food"],
                "warnings": item_warnings
            }

            enriched_items.append(enriched_item)

            # Add to totals
            total_nutrition["calories"] += nutrition["calories"]
            total_nutrition["protein_g"] += nutrition["protein_g"]
            total_nutrition["carbs_g"] += nutrition["carbs_g"]
            total_nutrition["fat_g"] += nutrition["fat_g"]

            logger.info(
                f"[LogEnrichment] ✅ Matched '{food_name}' → '{matched_food['name']}' "
                f"(score: {match_score:.0f}%, {nutrition['calories']} cal)"
            )

        # Build enriched structured_data
        enriched_data = {
            **structured_data,
            "items": enriched_items,
            "nutrition_summary": total_nutrition,
            "warnings": all_warnings,
            "missing_foods": missing_foods,
            "enrichment_metadata": {
                "total_items": len(foods),
                "matched_items": len(enriched_items),
                "missing_items": len(missing_foods),
                "low_confidence_items": sum(1 for item in enriched_items if item["match_confidence"] < 85)
            }
        }

        logger.info(
            f"[LogEnrichment] ✅ Enrichment complete: "
            f"{len(enriched_items)} matched, {len(missing_foods)} missing"
        )

        return enriched_data, all_warnings

    async def _search_food_with_alternatives(
        self,
        food_name: str,
        user_id: str,
        unit: str,
        top_n: int = 3
    ) -> Optional[Tuple[Dict[str, Any], float, str, List[Dict[str, Any]]]]:
        """
        Search for food with alternatives.

        Returns:
            Tuple of (matched_food, match_score, match_reason, alternatives)
            OR None if no match found
        """
        try:
            # STEP 1: Try exact user history match first
            user_history_query = self.supabase.table("meal_items")\
                .select("food_id, foods(id, name, brand_name, calories_per_100g, protein_g_per_100g, carbs_g_per_100g, fat_g_per_100g, composition_type)")\
                .eq("meals.user_id", user_id)\
                .limit(100)\
                .execute()

            if user_history_query.data:
                # Extract unique food_ids from user's history
                user_food_ids = list(set([
                    item["food_id"] for item in user_history_query.data
                    if item.get("foods")
                ]))

                # Check if any user food matches
                for item in user_history_query.data:
                    if not item.get("foods"):
                        continue
                    food = item["foods"]
                    similarity = self._calculate_similarity(food_name.lower(), food["name"].lower())
                    if similarity >= 0.85:
                        # User has logged this before - high priority
                        alternatives = await self._get_alternatives(food_name, food["id"], top_n)
                        return (food, similarity * 100, "user_history", alternatives)

            # STEP 2: Fuzzy search in all foods
            search_query = self.supabase.table("foods")\
                .select("id, name, brand_name, calories_per_100g, protein_g_per_100g, carbs_g_per_100g, fat_g_per_100g, composition_type, is_public")\
                .or_(f"name.ilike.%{food_name}%,brand_name.ilike.%{food_name}%")\
                .eq("is_public", True)\
                .limit(10)\
                .execute()

            if not search_query.data:
                return None

            # Calculate similarity scores
            scored_foods = []
            for food in search_query.data:
                name_similarity = self._calculate_similarity(food_name.lower(), food["name"].lower())
                brand_similarity = 0
                if food.get("brand_name"):
                    brand_similarity = self._calculate_similarity(food_name.lower(), food["brand_name"].lower())

                max_similarity = max(name_similarity, brand_similarity)
                scored_foods.append((food, max_similarity))

            # Sort by similarity
            scored_foods.sort(key=lambda x: x[1], reverse=True)

            if scored_foods[0][1] < 0.60:
                # No good match
                return None

            best_match = scored_foods[0][0]
            match_score = scored_foods[0][1] * 100

            # Get alternatives (top 3 excluding best match)
            alternatives = [food for food, _ in scored_foods[1:top_n+1]]

            return (best_match, match_score, "fuzzy_search", alternatives)

        except Exception as e:
            logger.error(f"[LogEnrichment] ❌ Food search error: {e}", exc_info=True)
            return None

    async def _get_alternatives(
        self,
        food_name: str,
        exclude_id: str,
        top_n: int
    ) -> List[Dict[str, Any]]:
        """Get alternative foods similar to the search term."""
        try:
            query = self.supabase.table("foods")\
                .select("id, name, brand_name, calories_per_100g")\
                .neq("id", exclude_id)\
                .or_(f"name.ilike.%{food_name}%,brand_name.ilike.%{food_name}%")\
                .eq("is_public", True)\
                .limit(top_n)\
                .execute()

            return query.data or []
        except Exception as e:
            logger.error(f"[LogEnrichment] ❌ Alternatives search error: {e}")
            return []

    def _calculate_similarity(self, str1: str, str2: str) -> float:
        """Calculate similarity between two strings (0.0 - 1.0)."""
        # Simple Levenshtein-based similarity
        from difflib import SequenceMatcher
        return SequenceMatcher(None, str1, str2).ratio()

    def _calculate_nutrition(
        self,
        food: Dict[str, Any],
        quantity: Optional[float],
        unit: str,
        estimated_grams: float
    ) -> Dict[str, float]:
        """
        Calculate nutrition for a food item.

        Returns:
            Dict with grams, calories, protein_g, carbs_g, fat_g
        """
        # Use estimated_grams as the authoritative value
        # (LLM has already estimated based on quantity + unit)
        grams = estimated_grams

        # Calculate nutrition from per_100g values
        factor = grams / 100.0

        return {
            "grams": round(grams, 1),
            "calories": round(food["calories_per_100g"] * factor),
            "protein_g": round(food["protein_g_per_100g"] * factor, 1),
            "carbs_g": round(food["carbs_g_per_100g"] * factor, 1),
            "fat_g": round(food["fat_g_per_100g"] * factor, 1)
        }


# Singleton
_log_preview_enrichment_service: Optional[LogPreviewEnrichmentService] = None

def get_log_preview_enrichment_service(supabase_client=None) -> LogPreviewEnrichmentService:
    """Get singleton LogPreviewEnrichmentService instance."""
    global _log_preview_enrichment_service
    if _log_preview_enrichment_service is None:
        if supabase_client is None:
            raise ValueError("supabase_client required for first initialization")
        _log_preview_enrichment_service = LogPreviewEnrichmentService(supabase_client)
    return _log_preview_enrichment_service
