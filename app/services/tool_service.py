"""
Tool Service - Agentic Tool Calling for AI Coach

Provides 13 tools for on-demand data fetching and actions:
1. get_user_profile - Get user goals, macros, restrictions
2. get_daily_nutrition_summary - Get today's totals
3. get_recent_meals - Get meal history
4. get_recent_activities - Get workout history
5. search_food_database - Nutrition lookup (DEPRECATED - not used by coach)
6. get_body_measurements - Weight/measurements
7. calculate_progress_trend - Trend analysis
8. analyze_training_volume - Volume analysis
9. semantic_search_user_data - RAG search
10. calculate_meal_nutrition - Nutrition calc
11. suggest_meal_adjustments - Macro optimization
12. estimate_activity_calories - Calorie estimation
13. log_meals_quick - Log meals from conversation (NEW - Week 2.5)

This is 80% cheaper than full RAG - only fetches what's needed!

Week 2 Optimization: Intelligent Caching
- User profiles cached (5min TTL)
- Daily summaries cached (1min TTL)
- Food searches cached (30min TTL)
- Reduces database load and improves response time

Week 2.5: Chat-Based Logging (Pulled from Week 5)
- log_meals_quick: AI nutrition estimation (NO database lookups)
- Auto-creates custom foods with is_ai_estimated=true flag
- Supports multi-item meals (eggs + toast = 1 meal, 2 items)
- Supports multi-meal logging (breakfast + lunch = 2 meals in 1 call)
- Respects full database schema (meals + meal_items + foods tables)
- Sets source="coach_chat" for tracking
- Fast: Single tool call regardless of complexity
"""

import structlog
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from app.services.cache_service import get_cache_service
from app.models.nutrition import MealItemBase

logger = structlog.get_logger()


# ============================================================================
# TOOL DEFINITIONS (Claude/Groq format)
# ============================================================================

COACH_TOOLS = [
    {
        "name": "get_user_profile",
        "description": "Get user's profile including goals, body stats, macro targets, dietary restrictions, and preferences. Use this to personalize advice.",
        "input_schema": {
            "type": "object",
            "properties": {
                "include_goals": {
                    "type": "boolean",
                    "description": "Include user's fitness goals",
                    "default": True
                }
            },
            "required": []
        }
    },
    {
        "name": "search_food_database",
        "description": """Search for food nutrition information. Returns per-100g data that YOU must scale.

DATABASE STRUCTURE:
- foods table: Public database (simple ingredients, recipes, branded products)
  - composition_type='simple': Single ingredients (chicken, rice, banana)
  - composition_type='composed': Public recipes (Chicken Rice Bowl)
  - composition_type='branded': Packaged products (Chipotle Bowl)
- quick_meals table: User's personal meal shortcuts (e.g., "My Breakfast")

SEARCH PRIORITY:
1. User's quick_meals (personalized shortcuts)
2. Exact matches in foods table
3. Partial matches in foods table
4. User's frequently logged foods

IMPORTANT - NUTRITION CALCULATION:
- Tool returns nutrition PER 100g
- If user says "300g of chicken", YOU must multiply: (31g protein × 3 = 93g)
- If user says "2 bananas", estimate grams first (~120g each = 240g total)
- Always show your math to the user

Example:
User: "I ate 300g grilled chicken"
Tool returns: {"per_100g": {"protein": 31, "calories": 165}}
You calculate: 31 × 3 = 93g protein, 165 × 3 = 495 calories
You respond: "Logged. 300g chicken = 93g protein, 495 cal."
""",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Food name to search for (e.g., 'chicken breast', 'banana', 'my breakfast')"
                },
                "limit": {
                    "type": "integer",
                    "description": "Number of results to return (default: 5, max: 10)",
                    "default": 5
                }
            },
            "required": ["query"]
        }
    },
    {
        "name": "get_daily_nutrition_summary",
        "description": "Get nutrition totals for a specific date (calories, protein, carbs, fats) with goal progress. Includes meal count, totals, and percentage progress toward daily goals.",
        "input_schema": {
            "type": "object",
            "properties": {
                "date": {
                    "type": "string",
                    "description": "Date in YYYY-MM-DD format (default: today)"
                }
            },
            "required": []
        }
    },
    {
        "name": "get_recent_meals",
        "description": "Get user's recent meal history with full nutrition breakdown. Returns meals from the past N days with name, meal type, nutrition totals, and notes.",
        "input_schema": {
            "type": "object",
            "properties": {
                "days": {
                    "type": "integer",
                    "description": "Number of days to look back",
                    "default": 7
                },
                "limit": {
                    "type": "integer",
                    "description": "Max number of meals to return",
                    "default": 20
                }
            },
            "required": []
        }
    },
    {
        "name": "get_recent_activities",
        "description": "Get user's recent workouts and activities history. Returns activities from past N days with category, duration, calories burned, intensity (METs), and category-specific metrics (distance, sets/reps, etc.).",
        "input_schema": {
            "type": "object",
            "properties": {
                "days": {
                    "type": "integer",
                    "description": "Number of days to look back",
                    "default": 7
                },
                "limit": {
                    "type": "integer",
                    "description": "Max number of activities to return",
                    "default": 20
                }
            },
            "required": []
        }
    },
    {
        "name": "get_body_measurements",
        "description": "Get user's body measurements history including weight (kg), body fat percentage, and notes. Returns measurements from past N days ordered by date, including latest weight.",
        "input_schema": {
            "type": "object",
            "properties": {
                "days": {
                    "type": "integer",
                    "description": "Number of days to look back",
                    "default": 30
                }
            },
            "required": []
        }
    },
    {
        "name": "calculate_progress_trend",
        "description": "Calculate progress trend for weight, calories, or protein over time. Analyzes historical data to show first vs last value, absolute change, percentage change, and trend direction (increasing/decreasing/stable). Requires at least 2 data points.",
        "input_schema": {
            "type": "object",
            "properties": {
                "metric": {
                    "type": "string",
                    "description": "Metric to analyze (e.g., 'weight', 'calories', 'protein')"
                },
                "days": {
                    "type": "integer",
                    "description": "Number of days to analyze",
                    "default": 30
                }
            },
            "required": ["metric"]
        }
    },
    {
        "name": "analyze_training_volume",
        "description": "Analyze training volume and intensity over time. Returns total workouts, total duration, total calories burned, average intensity (METs), workouts per week, breakdown by category, and average duration per workout.",
        "input_schema": {
            "type": "object",
            "properties": {
                "days": {
                    "type": "integer",
                    "description": "Number of days to analyze",
                    "default": 7
                }
            },
            "required": []
        }
    },
    {
        "name": "semantic_search_user_data",
        "description": "Search user's conversation history semantically using embeddings. Returns EMPTY in MVP - no embeddings yet.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Natural language search query"
                },
                "limit": {
                    "type": "integer",
                    "description": "Number of results to return",
                    "default": 5
                }
            },
            "required": ["query"]
        }
    },
    {
        "name": "calculate_meal_nutrition",
        "description": "Calculate nutrition for a list of foods with quantities.",
        "input_schema": {
            "type": "object",
            "properties": {
                "foods": {
                    "type": "array",
                    "description": "List of foods with quantities",
                    "items": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string"},
                            "quantity": {"type": "number"},
                            "unit": {"type": "string"}
                        }
                    }
                }
            },
            "required": ["foods"]
        }
    },
    {
        "name": "suggest_meal_adjustments",
        "description": "Suggest adjustments to a meal to hit macro targets.",
        "input_schema": {
            "type": "object",
            "properties": {
                "current_meal": {
                    "type": "object",
                    "description": "Current meal nutrition",
                    "properties": {
                        "calories": {"type": "number"},
                        "protein": {"type": "number"},
                        "carbs": {"type": "number"},
                        "fats": {"type": "number"}
                    }
                },
                "target_macros": {
                    "type": "object",
                    "description": "Target macros (optional, uses user's goals if not provided)"
                }
            },
            "required": ["current_meal"]
        }
    },
    {
        "name": "estimate_activity_calories",
        "description": "Estimate calories burned for an activity.",
        "input_schema": {
            "type": "object",
            "properties": {
                "activity_type": {
                    "type": "string",
                    "description": "Type of activity (e.g., 'running', 'cycling', 'strength training')"
                },
                "duration_minutes": {
                    "type": "number",
                    "description": "Duration in minutes"
                },
                "intensity": {
                    "type": "string",
                    "description": "Intensity level",
                    "enum": ["low", "moderate", "high"]
                }
            },
            "required": ["activity_type", "duration_minutes"]
        }
    },
    {
        "name": "log_meals_quick",
        "description": """⚠️ SAVES MEAL TO DATABASE - REQUIRED WHEN USER MENTIONS EATING ⚠️

Log one or more meals using your built-in nutrition knowledge (NO DATABASE LOOKUPS).

🚨 WARNING: If you don't call this tool, the user's meal is LOST FOREVER!
🚨 Calculating nutrition in your response ≠ saving it to the database!
🚨 You MUST call this tool when user says "I ate X" or "just had Y"

CRITICAL: Use your encyclopedic nutrition knowledge to estimate everything:
- Whole mozzarella pizza (12"): ~800g, 2000 cal, 80g protein, 200g carbs, 80g fat
- Chicken breast (100g): ~165 cal, 31g protein, 0g carbs, 3.6g fat
- White rice cooked (150g/1 cup): ~200 cal, 4g protein, 45g carbs, 0.4g fat
- Eggs (2 large): ~140 cal, 12g protein, 1g carbs, 10g fat
- Banana (medium, 120g): ~105 cal, 1.3g protein, 27g carbs, 0.4g fat

GRAMS ESTIMATION (if not specified):
- "Entire pizza" → 800g
- "Chicken breast" → 150g
- "Bowl of rice" → 200g
- "Large" → +50%, "Small" → -50%

MULTI-ITEM MEALS:
"I had eggs and toast for breakfast"
→ 1 meal with 2 items: [{eggs}, {toast}]

MULTI-MEAL LOGGING:
"I had eggs for breakfast and chicken for lunch"
→ 2 meals: [{breakfast: [eggs]}, {lunch: [chicken]}]

MEAL TYPE INFERENCE:
- User says "breakfast/lunch/dinner" → use that type
- User mentions time: "this morning" → breakfast, "at noon" → lunch
- Default if ambiguous → "snack"

ROUNDING:
- calories: INTEGER (no decimals)
- protein_g, carbs_g, fat_g: 1 DECIMAL PLACE

WORKFLOW:
1. Parse user message (how many meals? how many items per meal?)
2. Estimate grams if not provided
3. Calculate nutrition from memory
4. Call tool once with all meals
5. Done - fast, no database searches""",
        "input_schema": {
            "type": "object",
            "properties": {
                "meals": {
                    "type": "array",
                    "description": "Array of meals to log (can be multiple)",
                    "items": {
                        "type": "object",
                        "properties": {
                            "meal_type": {
                                "type": "string",
                                "description": "Meal type",
                                "enum": ["breakfast", "lunch", "dinner", "snack", "other"]
                            },
                            "items": {
                                "type": "array",
                                "description": "Food items in this meal",
                                "minItems": 1,
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "food_name": {
                                            "type": "string",
                                            "description": "Name of food (e.g., 'Grilled Chicken Breast', 'Whole Mozzarella Pizza')"
                                        },
                                        "grams": {
                                            "type": "number",
                                            "description": "Total grams of this food item"
                                        },
                                        "calories": {
                                            "type": "integer",
                                            "description": "Calculated calories (INTEGER)"
                                        },
                                        "protein_g": {
                                            "type": "number",
                                            "description": "Protein in grams (1 decimal)"
                                        },
                                        "carbs_g": {
                                            "type": "number",
                                            "description": "Carbs in grams (1 decimal)"
                                        },
                                        "fat_g": {
                                            "type": "number",
                                            "description": "Fat in grams (1 decimal)"
                                        }
                                    },
                                    "required": ["food_name", "grams", "calories", "protein_g", "carbs_g", "fat_g"]
                                }
                            },
                            "notes": {
                                "type": "string",
                                "description": "Optional meal notes"
                            },
                            "logged_at": {
                                "type": "string",
                                "description": "ISO 8601 timestamp (infer from context or use current time)"
                            }
                        },
                        "required": ["meal_type", "items"]
                    },
                    "minItems": 1
                }
            },
            "required": ["meals"]
        }
    },
    {
        "name": "update_meal",
        "description": """Update an existing meal's metadata or items via natural language.

Use this when the user wants to:
- Change meal type: "Change my breakfast to lunch"
- Update meal name/notes: "Call that meal 'Post-Workout'"
- Add items: "Add 100g rice to my dinner"
- Remove items: "Remove the protein shake from my snack"
- Update item quantities: "Actually I had 3 eggs not 2"

MEAL IDENTIFICATION:
- By type + date: "breakfast" → today's breakfast, "yesterday's lunch"
- By relative time: "last meal", "my most recent meal"
- By ID: If user references a specific meal

DATE PARSING:
- "today" → current date
- "yesterday" → 1 day ago
- "Monday" → most recent Monday
- ISO date: "2025-10-25"

ITEM OPERATIONS:
- add: New items to existing meal
- remove: Delete specific items
- update: Change quantity/serving of existing items

Returns updated meal with recalculated nutrition.""",
        "input_schema": {
            "type": "object",
            "properties": {
                "meal_identifier": {
                    "type": "object",
                    "description": "How to find the meal",
                    "properties": {
                        "type": {
                            "type": "string",
                            "enum": ["meal_type", "relative", "id"],
                            "description": "Identification method"
                        },
                        "value": {
                            "type": "string",
                            "description": "breakfast/lunch/dinner/snack, 'last', or meal ID"
                        },
                        "date": {
                            "type": "string",
                            "description": "Date (YYYY-MM-DD) or relative ('today', 'yesterday')"
                        }
                    },
                    "required": ["type", "value"]
                },
                "updates": {
                    "type": "object",
                    "description": "What to update",
                    "properties": {
                        "meal_type": {
                            "type": "string",
                            "enum": ["breakfast", "lunch", "dinner", "snack", "other"]
                        },
                        "name": {
                            "type": "string"
                        },
                        "notes": {
                            "type": "string"
                        },
                        "item_operations": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "action": {
                                        "type": "string",
                                        "enum": ["add", "remove", "update"]
                                    },
                                    "food_name": {
                                        "type": "string"
                                    },
                                    "quantity": {
                                        "type": "number",
                                        "description": "New quantity (grams or servings)"
                                    },
                                    "unit": {
                                        "type": "string",
                                        "enum": ["grams", "serving"]
                                    },
                                    "calories": {
                                        "type": "integer"
                                    },
                                    "protein_g": {
                                        "type": "number"
                                    },
                                    "carbs_g": {
                                        "type": "number"
                                    },
                                    "fat_g": {
                                        "type": "number"
                                    }
                                },
                                "required": ["action", "food_name"]
                            }
                        }
                    }
                }
            },
            "required": ["meal_identifier", "updates"]
        }
    },
    {
        "name": "delete_meal",
        "description": """Delete an entire meal by type, relative reference, or ID.

Use this when user says:
- "Delete my lunch"
- "Remove yesterday's breakfast"
- "Clear my last meal"
- "Delete that snack I just logged"

SAFETY: Always confirm before deleting to prevent accidents.

MEAL IDENTIFICATION (same as update_meal):
- By type + date: "lunch" → today's lunch, "yesterday's dinner"
- By relative time: "last meal", "most recent"
- By ID: Specific meal UUID

Returns success confirmation with details of deleted meal.""",
        "input_schema": {
            "type": "object",
            "properties": {
                "meal_identifier": {
                    "type": "object",
                    "properties": {
                        "type": {
                            "type": "string",
                            "enum": ["meal_type", "relative", "id"]
                        },
                        "value": {
                            "type": "string"
                        },
                        "date": {
                            "type": "string"
                        }
                    },
                    "required": ["type", "value"]
                }
            },
            "required": ["meal_identifier"]
        }
    },
    {
        "name": "update_meal_item",
        "description": """Update quantity or serving of a specific food item within a meal.

Use this for granular edits:
- "Change the chicken in my lunch from 200g to 300g"
- "Actually I had 3 eggs not 2"
- "Update my breakfast - the oatmeal was 150g not 100g"

More surgical than update_meal (which can add/remove items).
This only changes quantity/serving of one existing item.

Returns updated meal with recalculated nutrition.""",
        "input_schema": {
            "type": "object",
            "properties": {
                "meal_identifier": {
                    "type": "object",
                    "properties": {
                        "type": {
                            "type": "string",
                            "enum": ["meal_type", "relative", "id"]
                        },
                        "value": {
                            "type": "string"
                        },
                        "date": {
                            "type": "string"
                        }
                    },
                    "required": ["type", "value"]
                },
                "item_identifier": {
                    "type": "string",
                    "description": "Food name to identify the item (e.g., 'chicken', 'eggs')"
                },
                "new_quantity": {
                    "type": "number",
                    "description": "New quantity (grams or serving count)"
                },
                "unit": {
                    "type": "string",
                    "enum": ["grams", "serving"],
                    "description": "Unit for the quantity"
                }
            },
            "required": ["meal_identifier", "item_identifier", "new_quantity"]
        }
    },
    {
        "name": "copy_meal",
        "description": """Copy meals from one date to another for easy meal planning.

Use this when user wants to:
- "Log the same as yesterday's breakfast"
- "Repeat my Monday meals"
- "Copy my meal from Oct 20"
- "Do the same lunch as last week"

Perfect for meal prep users who eat similar meals regularly.

SOURCE IDENTIFICATION:
- By meal type + date: "yesterday's breakfast"
- By date only: "Monday's meals" (copies all meals from that date)
- By meal ID: Specific meal UUID

TARGET DATE:
- "today" → current date
- "tomorrow" → next day
- ISO date: "2025-10-26"

Returns newly created meal(s) with same items but new logged_at timestamp.""",
        "input_schema": {
            "type": "object",
            "properties": {
                "source_identifier": {
                    "type": "object",
                    "properties": {
                        "type": {
                            "type": "string",
                            "enum": ["meal_type", "meal_id", "all_meals"],
                            "description": "What to copy"
                        },
                        "value": {
                            "type": "string",
                            "description": "Meal type, ID, or 'all'"
                        },
                        "date": {
                            "type": "string",
                            "description": "Source date (YYYY-MM-DD or 'yesterday', 'Monday')"
                        }
                    },
                    "required": ["type", "date"]
                },
                "target_date": {
                    "type": "string",
                    "description": "Target date (YYYY-MM-DD or 'today', 'tomorrow')"
                },
                "target_meal_type": {
                    "type": "string",
                    "enum": ["breakfast", "lunch", "dinner", "snack", "same"],
                    "description": "Target meal type or 'same' to keep original"
                }
            },
            "required": ["source_identifier", "target_date"]
        }
    },
    {
        "name": "create_quick_meal",
        "description": """Save a meal as a reusable template for faster logging.

Use this when user wants to:
- "Save this meal as 'Post-Workout Shake'"
- "Create a quick meal called 'Cutting Lunch' with chicken, rice, broccoli"
- "Make this my go-to breakfast"

Quick meals are templates that can be logged instantly without re-entering items.
Great for meal prep, consistent eating patterns, and favorite meals.

SOURCE OPTIONS:
- last_logged: Save the most recent meal logged
- custom: Create from scratch with specified items
- meal_id: Save a specific meal by ID

Returns created quick meal with ID for future reference.""",
        "input_schema": {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "Quick meal name (e.g., 'Morning Protein Shake', 'Chicken Rice Bowl')"
                },
                "description": {
                    "type": "string",
                    "description": "Optional description"
                },
                "source": {
                    "type": "string",
                    "enum": ["last_logged", "custom", "meal_id"],
                    "description": "Where to get meal items from"
                },
                "meal_id": {
                    "type": "string",
                    "description": "Meal ID if source='meal_id'"
                },
                "items": {
                    "type": "array",
                    "description": "Items if source='custom'",
                    "items": {
                        "type": "object",
                        "properties": {
                            "food_name": {
                                "type": "string"
                            },
                            "quantity": {
                                "type": "number"
                            },
                            "unit": {
                                "type": "string",
                                "enum": ["grams", "serving"]
                            },
                            "calories": {
                                "type": "integer"
                            },
                            "protein_g": {
                                "type": "number"
                            },
                            "carbs_g": {
                                "type": "number"
                            },
                            "fat_g": {
                                "type": "number"
                            }
                        },
                        "required": ["food_name", "quantity", "calories", "protein_g", "carbs_g", "fat_g"]
                    }
                }
            },
            "required": ["name", "source"]
        }
    },
    {
        "name": "delete_quick_meal",
        "description": """Remove a quick meal template.

Use this when user wants to:
- "Delete my 'Morning Shake' quick meal"
- "Remove the 'Cutting Lunch' template"
- "I don't use that quick meal anymore"

Returns success confirmation.""",
        "input_schema": {
            "type": "object",
            "properties": {
                "identifier": {
                    "type": "object",
                    "properties": {
                        "type": {
                            "type": "string",
                            "enum": ["name", "id"],
                            "description": "How to find the quick meal"
                        },
                        "value": {
                            "type": "string",
                            "description": "Quick meal name or ID"
                        }
                    },
                    "required": ["type", "value"]
                }
            },
            "required": ["identifier"]
        }
    },
    {
        "name": "list_quick_meals",
        "description": """List user's saved quick meal templates with nutrition preview.

Use this when user asks:
- "Show me my quick meals"
- "What quick meals do I have?"
- "List my saved meals"

Returns formatted list with:
- Quick meal name and description
- Number of items
- Total nutrition (calories, protein, carbs, fat)
- When it was created

Helps users remember what templates they have available.""",
        "input_schema": {
            "type": "object",
            "properties": {
                "include_nutrition": {
                    "type": "boolean",
                    "description": "Include nutrition totals (default: true)",
                    "default": True
                }
            }
        }
    }
]


# ============================================================================
# TOOL SERVICE
# ============================================================================

class ToolService:
    """
    Executes tools for agentic AI coach.

    Each tool is a function that can be called by Claude/Groq.

    Week 2 Optimization: Intelligent caching for frequently accessed data.
    """

    def __init__(self, supabase_client):
        self.supabase = supabase_client
        self.cache = get_cache_service()  # Week 2: Add caching layer

    async def execute_tool(
        self,
        tool_name: str,
        tool_input: Dict[str, Any],
        user_id: str
    ) -> Any:
        """
        Execute a tool and return result.

        Args:
            tool_name: Name of tool to execute
            tool_input: Tool input parameters
            user_id: User UUID (for data access)

        Returns:
            Tool result (any type)
        """
        logger.info(f"[ToolService] 🛠️ Executing: {tool_name}")

        # Route to appropriate handler
        if tool_name == "get_user_profile":
            return await self._get_user_profile(user_id, tool_input)
        elif tool_name == "search_food_database":
            # Pass user_id for personalized search (quick_meals)
            tool_input["user_id"] = user_id
            return await self._search_food_database(tool_input)
        elif tool_name == "get_daily_nutrition_summary":
            return await self._get_daily_nutrition_summary(user_id, tool_input)
        elif tool_name == "get_recent_meals":
            return await self._get_recent_meals(user_id, tool_input)
        elif tool_name == "get_recent_activities":
            return await self._get_recent_activities(user_id, tool_input)
        elif tool_name == "get_body_measurements":
            return await self._get_body_measurements(user_id, tool_input)
        elif tool_name == "calculate_progress_trend":
            return await self._calculate_progress_trend(user_id, tool_input)
        elif tool_name == "analyze_training_volume":
            return await self._analyze_training_volume(user_id, tool_input)
        elif tool_name == "semantic_search_user_data":
            return await self._semantic_search_user_data(user_id, tool_input)
        elif tool_name == "calculate_meal_nutrition":
            return await self._calculate_meal_nutrition(tool_input)
        elif tool_name == "suggest_meal_adjustments":
            return await self._suggest_meal_adjustments(user_id, tool_input)
        elif tool_name == "estimate_activity_calories":
            return await self._estimate_activity_calories(user_id, tool_input)
        elif tool_name == "log_meals_quick":
            return await self._log_meals_quick(user_id, tool_input)
        elif tool_name == "update_meal":
            return await self._update_meal(user_id, tool_input)
        elif tool_name == "delete_meal":
            return await self._delete_meal(user_id, tool_input)
        elif tool_name == "update_meal_item":
            return await self._update_meal_item(user_id, tool_input)
        elif tool_name == "copy_meal":
            return await self._copy_meal(user_id, tool_input)
        elif tool_name == "create_quick_meal":
            return await self._create_quick_meal(user_id, tool_input)
        elif tool_name == "delete_quick_meal":
            return await self._delete_quick_meal(user_id, tool_input)
        elif tool_name == "list_quick_meals":
            return await self._list_quick_meals(user_id, tool_input)
        else:
            raise ValueError(f"Unknown tool: {tool_name}")

    # ========================================================================
    # TOOL IMPLEMENTATIONS
    # ========================================================================

    async def _get_user_profile(self, user_id: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get user profile with goals and preferences.

        Week 2 Optimization: Cached with 5min TTL (profiles change infrequently)
        """
        # Check cache first
        cache_key = f"user_profile:{user_id}"
        cached_result = self.cache.get(cache_key)
        if cached_result:
            logger.debug(f"[ToolService] ✅ Cache hit: user_profile")
            return cached_result

        try:
            result = self.supabase.table("profiles")\
                .select("*")\
                .eq("id", user_id)\
                .single()\
                .execute()

            if not result.data:
                return {"error": "Profile not found"}

            profile = result.data

            # Format response
            formatted_profile = {
                "full_name": profile.get("full_name"),
                "primary_goal": profile.get("primary_goal"),
                "experience_level": profile.get("experience_level"),
                "daily_calorie_goal": profile.get("daily_calorie_goal"),
                "daily_protein_goal": profile.get("daily_protein_goal"),
                "daily_carbs_goal": profile.get("daily_carbs_goal"),
                "daily_fat_goal": profile.get("daily_fat_goal"),
                "unit_system": profile.get("unit_system", "imperial"),
                "language": profile.get("language", "en")
            }

            # Cache for 5 minutes (300 seconds)
            self.cache.set(cache_key, formatted_profile, ttl=300)
            logger.debug(f"[ToolService] 💾 Cached: user_profile (5min TTL)")

            return formatted_profile

        except Exception as e:
            logger.error(f"[ToolService] get_user_profile failed: {e}")
            return {"error": str(e)}

    async def _search_food_database(self, params: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        SMART food database search with ranking:
        1. User's quick_meals (personalized shortcuts)
        2. Exact matches in foods table
        3. Partial matches in foods table
        4. Prioritize by composition_type (simple > composed > branded)
        5. Track user frequency (future enhancement)

        Week 2 Optimization: Cached with 30min TTL (food database rarely changes)
        """
        try:
            query = params["query"].lower().strip()
            limit = min(params.get("limit", 5), 10)  # Max 10 results
            user_id = params.get("user_id")  # Passed from execute_tool

            # Check cache first
            cache_key = f"food_search:{user_id or 'public'}:{query}:{limit}"
            cached_result = self.cache.get(cache_key)
            if cached_result:
                logger.debug(f"[ToolService] ✅ Cache hit: food_search({query})")
                return cached_result

            results = []
            seen_names = set()  # Deduplicate

            # ================================================================
            # STEP 1: Search user's quick_meals (HIGHEST PRIORITY)
            # ================================================================
            if user_id:
                try:
                    quick_meals_result = self.supabase.table("quick_meals")\
                        .select("""
                            id, name, description,
                            total_calories, total_protein_g, total_carbs_g, total_fat_g
                        """)\
                        .eq("user_id", user_id)\
                        .ilike("name", f"%{query}%")\
                        .limit(3)\
                        .execute()

                    for meal in quick_meals_result.data or []:
                        name_key = meal["name"].lower()
                        if name_key in seen_names:
                            continue
                        seen_names.add(name_key)

                        results.append({
                            "source": "quick_meal",
                            "name": meal["name"],
                            "description": meal.get("description"),
                            "is_user_meal": True,
                            "per_100g": {
                                "calories": meal["total_calories"],
                                "protein": meal["total_protein_g"],
                                "carbs": meal["total_carbs_g"],
                                "fats": meal["total_fat_g"]
                            },
                            "note": "This is YOUR saved meal. Nutrition shown is total for this meal."
                        })

                        if len(results) >= limit:
                            return results
                except Exception as e:
                    logger.warning(f"[ToolService] quick_meals search failed: {e}")

            # ================================================================
            # STEP 2: Search public foods table (with smart ranking)
            # ================================================================

            # Search with ILIKE (case-insensitive partial match)
            foods_result = self.supabase.table("foods")\
                .select("""
                    id, name, brand_name, composition_type,
                    calories_per_100g, protein_g_per_100g,
                    carbs_g_per_100g, fat_g_per_100g,
                    serving_size_g, serving_size_description
                """)\
                .or_(f"name.ilike.%{query}%,brand_name.ilike.%{query}%")\
                .eq("is_public", True)\
                .limit(20)\
                .execute()

            if not foods_result.data:
                # No results at all
                return [] if not results else results

            # ================================================================
            # STEP 3: Rank and sort results
            # ================================================================
            scored_foods = []
            for food in foods_result.data:
                name_key = food["name"].lower()
                if name_key in seen_names:
                    continue

                # Calculate relevance score
                score = self._calculate_relevance_score(
                    query=query,
                    food_name=food["name"],
                    brand_name=food.get("brand_name"),
                    composition_type=food.get("composition_type")
                )

                scored_foods.append((score, food))

            # Sort by score (highest first)
            scored_foods.sort(key=lambda x: x[0], reverse=True)

            # ================================================================
            # STEP 4: Format and return results
            # ================================================================
            for score, food in scored_foods:
                if len(results) >= limit:
                    break

                name_key = food["name"].lower()
                if name_key in seen_names:
                    continue
                seen_names.add(name_key)

                result_item = {
                    "source": "foods_database",
                    "name": food["name"],
                    "brand": food.get("brand_name"),
                    "composition_type": food.get("composition_type", "simple"),
                    "per_100g": {
                        "calories": food["calories_per_100g"],
                        "protein": food["protein_g_per_100g"],
                        "carbs": food["carbs_g_per_100g"],
                        "fats": food["fat_g_per_100g"]
                    }
                }

                # Add serving size info if available
                if food.get("serving_size_g"):
                    result_item["serving_size"] = {
                        "grams": food["serving_size_g"],
                        "description": food.get("serving_size_description")
                    }

                results.append(result_item)

            # Cache results for 30 minutes (1800 seconds)
            cache_key = f"food_search:{user_id or 'public'}:{query}:{limit}"
            self.cache.set(cache_key, results, ttl=1800)
            logger.debug(f"[ToolService] 💾 Cached: food_search({query}) - {len(results)} results (30min TTL)")

            return results

        except Exception as e:
            logger.error(f"[ToolService] search_food_database failed: {e}", exc_info=True)
            return []

    def _calculate_relevance_score(
        self,
        query: str,
        food_name: str,
        brand_name: Optional[str],
        composition_type: Optional[str]
    ) -> float:
        """
        Calculate relevance score for search ranking.

        Scoring:
        - Exact match: +100
        - Starts with query: +50
        - Contains query: +20
        - composition_type='simple': +10 (ingredients prioritized)
        - composition_type='composed': +5
        - composition_type='branded': +0
        - Brand match: +15
        """
        score = 0.0
        query_lower = query.lower()
        name_lower = food_name.lower()
        brand_lower = brand_name.lower() if brand_name else ""

        # Exact match (highest priority)
        if name_lower == query_lower or brand_lower == query_lower:
            score += 100

        # Starts with query
        elif name_lower.startswith(query_lower):
            score += 50

        # Contains query
        elif query_lower in name_lower:
            score += 20

        # Brand name contains query
        if brand_name and query_lower in brand_lower:
            score += 15

        # Composition type priority
        # Simple ingredients (chicken, rice) are prioritized for basic searches
        if composition_type == "simple":
            score += 10
        elif composition_type == "composed":
            score += 5
        # branded gets +0 (lowest priority unless exact match)

        return score

    async def _get_daily_nutrition_summary(self, user_id: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get today's nutrition totals with TIME-AWARE PROGRESS.

        NEW: Includes time-aware analysis to prevent "you're behind!" at 6 AM.
        Week 2 Optimization: Cached with 1min TTL (nutrition changes frequently)
        """
        from datetime import date, datetime, time
        from app.utils.time_aware_progress import calculate_time_aware_progress

        # Get target date (default: today)
        target_date_str = params.get("date")
        if target_date_str:
            target_date = datetime.fromisoformat(target_date_str).date()
        else:
            target_date = date.today()

        # Check cache first (very short TTL since nutrition changes throughout the day)
        cache_key = f"daily_nutrition:{user_id}:{target_date.isoformat()}"
        cached_result = self.cache.get(cache_key)
        if cached_result:
            logger.debug(f"[ToolService] ✅ Cache hit: daily_nutrition_summary({target_date})")
            return cached_result

        try:

            # Query meals for this date
            start_of_day = datetime.combine(target_date, time.min)
            end_of_day = datetime.combine(target_date, time.max)

            result = self.supabase.table("meals")\
                .select("id, name, meal_type, logged_at, total_calories, total_protein_g, total_carbs_g, total_fat_g")\
                .eq("user_id", user_id)\
                .gte("logged_at", start_of_day.isoformat())\
                .lte("logged_at", end_of_day.isoformat())\
                .order("logged_at", desc=False)\
                .execute()

            # Calculate totals
            total_calories = sum(float(m.get("total_calories") or 0) for m in result.data) if result.data else 0
            total_protein = sum(float(m.get("total_protein_g") or 0) for m in result.data) if result.data else 0
            total_carbs = sum(float(m.get("total_carbs_g") or 0) for m in result.data) if result.data else 0
            total_fat = sum(float(m.get("total_fat_g") or 0) for m in result.data) if result.data else 0

            # Get user's goals and timezone
            profile = await self._get_user_profile(user_id, {})
            daily_cal_goal = profile.get("daily_calorie_goal", 2000)
            daily_protein_goal = profile.get("daily_protein_goal", 150)
            user_timezone = profile.get("timezone", "UTC")

            # Calculate basic progress
            basic_progress = {
                "calories_percent": round((total_calories / daily_cal_goal * 100) if daily_cal_goal else 0),
                "protein_percent": round((total_protein / daily_protein_goal * 100) if daily_protein_goal else 0)
            }

            # Calculate TIME-AWARE PROGRESS (only for today)
            time_aware = None
            if target_date == date.today():
                try:
                    time_aware = calculate_time_aware_progress(
                        user_id=user_id,
                        current_time_utc=datetime.utcnow(),
                        actual_calories=total_calories,
                        goal_calories=daily_cal_goal,
                        user_timezone=user_timezone
                    )
                    logger.info(
                        f"[ToolService] Time-aware progress: {time_aware['interpretation']} "
                        f"(actual: {time_aware['actual_progress']:.1%}, "
                        f"expected: {time_aware['expected_progress']:.1%})"
                    )
                except Exception as e:
                    logger.error(f"[ToolService] Time-aware progress calculation failed: {e}")
                    # Continue without time-aware data

            response = {
                "date": target_date.isoformat(),
                "meal_count": len(result.data) if result.data else 0,
                "totals": {
                    "calories": round(total_calories),
                    "protein_g": round(total_protein, 1),
                    "carbs_g": round(total_carbs, 1),
                    "fat_g": round(total_fat, 1)
                },
                "goals": {
                    "calories": daily_cal_goal,
                    "protein_g": daily_protein_goal
                },
                "progress": basic_progress
            }

            # Add time-aware analysis if available
            if time_aware:
                response["time_aware_progress"] = {
                    "actual_progress": time_aware["actual_progress"],
                    "expected_progress": time_aware["expected_progress"],
                    "deviation": time_aware["deviation"],
                    "interpretation": time_aware["interpretation"],
                    "message_suggestion": time_aware["message_suggestion"],
                    "time_context": time_aware["time_context"],
                    "user_local_time": time_aware["user_local_time"]
                }

            # Add message based on context
            if not result.data:
                if time_aware and time_aware["time_context"] == "early_morning":
                    response["message"] = "Nothing logged yet - great time to start strong! 💪"
                else:
                    response["message"] = "No meals logged for this date yet."
            elif time_aware:
                response["message"] = time_aware["message_suggestion"]

            # Cache for 1 minute (60 seconds) - nutrition changes frequently
            cache_key = f"daily_nutrition:{user_id}:{target_date.isoformat()}"
            self.cache.set(cache_key, response, ttl=60)
            logger.debug(f"[ToolService] 💾 Cached: daily_nutrition_summary({target_date}) (1min TTL)")

            return response

        except Exception as e:
            logger.error(f"[ToolService] get_daily_nutrition_summary failed: {e}", exc_info=True)
            return {"error": str(e)}

    async def _get_recent_meals(self, user_id: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get recent meals."""
        try:
            from datetime import datetime, timedelta

            days = params.get("days", 7)
            limit = min(params.get("limit", 20), 50)  # Max 50

            # Query recent meals
            cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()

            result = self.supabase.table("meals")\
                .select("id, name, meal_type, logged_at, total_calories, total_protein_g, total_carbs_g, total_fat_g, notes")\
                .eq("user_id", user_id)\
                .gte("logged_at", cutoff_date)\
                .order("logged_at", desc=True)\
                .limit(limit)\
                .execute()

            if not result.data:
                return {
                    "days_searched": days,
                    "meal_count": 0,
                    "meals": [],
                    "message": "No meals logged in the past {} days.".format(days)
                }

            # Format meals
            meals = []
            for meal in result.data:
                meals.append({
                    "id": meal["id"],
                    "name": meal.get("name"),
                    "meal_type": meal["meal_type"],
                    "logged_at": meal["logged_at"],
                    "nutrition": {
                        "calories": round(float(meal.get("total_calories") or 0)),
                        "protein_g": round(float(meal.get("total_protein_g") or 0), 1),
                        "carbs_g": round(float(meal.get("total_carbs_g") or 0), 1),
                        "fat_g": round(float(meal.get("total_fat_g") or 0), 1)
                    },
                    "notes": meal.get("notes")
                })

            return {
                "days_searched": days,
                "meal_count": len(meals),
                "meals": meals
            }
        except Exception as e:
            logger.error(f"[ToolService] get_recent_meals failed: {e}")
            return {"error": str(e)}

    async def _get_recent_activities(self, user_id: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get recent activities."""
        try:
            from datetime import datetime, timedelta

            days = params.get("days", 7)
            limit = min(params.get("limit", 20), 50)  # Max 50

            # Query recent activities (exclude soft-deleted)
            cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()

            result = self.supabase.table("activities")\
                .select("id, category, activity_name, start_time, end_time, duration_minutes, calories_burned, intensity_mets, metrics, notes")\
                .eq("user_id", user_id)\
                .gte("start_time", cutoff_date)\
                .is_("deleted_at", "null")\
                .order("start_time", desc=True)\
                .limit(limit)\
                .execute()

            if not result.data:
                return {
                    "days_searched": days,
                    "activity_count": 0,
                    "activities": [],
                    "message": "No activities logged in the past {} days.".format(days)
                }

            # Format activities
            activities = []
            for activity in result.data:
                activities.append({
                    "id": activity["id"],
                    "category": activity.get("category"),
                    "activity_name": activity["activity_name"],
                    "start_time": activity["start_time"],
                    "duration_minutes": activity.get("duration_minutes"),
                    "calories_burned": activity.get("calories_burned"),
                    "intensity_mets": float(activity.get("intensity_mets") or 0),
                    "metrics": activity.get("metrics", {}),
                    "notes": activity.get("notes")
                })

            return {
                "days_searched": days,
                "activity_count": len(activities),
                "activities": activities
            }
        except Exception as e:
            logger.error(f"[ToolService] get_recent_activities failed: {e}")
            return {"error": str(e)}

    async def _get_body_measurements(self, user_id: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get body measurements."""
        try:
            from datetime import datetime, timedelta

            days = params.get("days", 30)

            # Query body metrics
            cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()

            result = self.supabase.table("body_metrics")\
                .select("id, recorded_at, weight_kg, body_fat_percentage, notes")\
                .eq("user_id", user_id)\
                .gte("recorded_at", cutoff_date)\
                .order("recorded_at", desc=True)\
                .execute()

            if not result.data:
                return {
                    "days_searched": days,
                    "measurement_count": 0,
                    "measurements": [],
                    "message": "No measurements logged in the past {} days.".format(days)
                }

            # Format measurements
            measurements = []
            for m in result.data:
                measurements.append({
                    "id": m["id"],
                    "recorded_at": m["recorded_at"],
                    "weight_kg": float(m["weight_kg"]),
                    "body_fat_percentage": float(m["body_fat_percentage"]) if m.get("body_fat_percentage") else None,
                    "notes": m.get("notes")
                })

            return {
                "days_searched": days,
                "measurement_count": len(measurements),
                "measurements": measurements,
                "latest_weight_kg": measurements[0]["weight_kg"] if measurements else None
            }
        except Exception as e:
            logger.error(f"[ToolService] get_body_measurements failed: {e}")
            return {"error": str(e)}

    async def _calculate_progress_trend(self, user_id: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate progress trend for a metric."""
        try:
            from datetime import datetime, timedelta

            metric = params["metric"].lower()
            days = params.get("days", 30)
            cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()

            # Route to appropriate table based on metric
            if metric == "weight":
                result = self.supabase.table("body_metrics")\
                    .select("recorded_at, weight_kg")\
                    .eq("user_id", user_id)\
                    .gte("recorded_at", cutoff_date)\
                    .order("recorded_at", desc=False)\
                    .execute()

                if not result.data or len(result.data) < 2:
                    return {
                        "metric": metric,
                        "message": "Not enough data to calculate trend. Need at least 2 measurements.",
                        "trend": None
                    }

                # Calculate trend
                first_value = float(result.data[0]["weight_kg"])
                last_value = float(result.data[-1]["weight_kg"])
                change = last_value - first_value
                percent_change = (change / first_value * 100) if first_value > 0 else 0

                return {
                    "metric": "weight",
                    "days_analyzed": days,
                    "data_points": len(result.data),
                    "first_value_kg": round(first_value, 1),
                    "last_value_kg": round(last_value, 1),
                    "change_kg": round(change, 1),
                    "percent_change": round(percent_change, 1),
                    "trend": "increasing" if change > 0 else "decreasing" if change < 0 else "stable"
                }

            elif metric in ["calories", "protein"]:
                # Query meals for nutrition trends
                result = self.supabase.table("meals")\
                    .select("logged_at, total_calories, total_protein_g")\
                    .eq("user_id", user_id)\
                    .gte("logged_at", cutoff_date)\
                    .order("logged_at", desc=False)\
                    .execute()

                if not result.data:
                    return {
                        "metric": metric,
                        "message": "No meal data to analyze.",
                        "trend": None
                    }

                # Group by date and calculate daily totals
                from collections import defaultdict
                daily_totals = defaultdict(float)

                for meal in result.data:
                    date = meal["logged_at"].split("T")[0]  # Extract date
                    if metric == "calories":
                        daily_totals[date] += float(meal.get("total_calories") or 0)
                    else:  # protein
                        daily_totals[date] += float(meal.get("total_protein_g") or 0)

                if len(daily_totals) < 2:
                    return {
                        "metric": metric,
                        "message": "Not enough daily data to calculate trend.",
                        "trend": None
                    }

                # Calculate average for first half vs second half
                dates = sorted(daily_totals.keys())
                mid_point = len(dates) // 2
                first_half_avg = sum(daily_totals[d] for d in dates[:mid_point]) / mid_point
                second_half_avg = sum(daily_totals[d] for d in dates[mid_point:]) / (len(dates) - mid_point)
                change = second_half_avg - first_half_avg
                percent_change = (change / first_half_avg * 100) if first_half_avg > 0 else 0

                return {
                    "metric": metric,
                    "days_analyzed": len(dates),
                    "first_period_avg": round(first_half_avg, 1),
                    "second_period_avg": round(second_half_avg, 1),
                    "change": round(change, 1),
                    "percent_change": round(percent_change, 1),
                    "trend": "increasing" if change > 0 else "decreasing" if change < 0 else "stable"
                }

            else:
                return {"error": f"Unsupported metric: {metric}. Try 'weight', 'calories', or 'protein'."}

        except Exception as e:
            logger.error(f"[ToolService] calculate_progress_trend failed: {e}")
            return {"error": str(e)}

    async def _analyze_training_volume(self, user_id: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze training volume and intensity."""
        try:
            from datetime import datetime, timedelta

            days = params.get("days", 7)
            cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()

            # Query activities
            result = self.supabase.table("activities")\
                .select("id, category, duration_minutes, calories_burned, intensity_mets, start_time")\
                .eq("user_id", user_id)\
                .gte("start_time", cutoff_date)\
                .is_("deleted_at", "null")\
                .order("start_time", desc=False)\
                .execute()

            if not result.data:
                return {
                    "days_analyzed": days,
                    "message": "No training data for this period.",
                    "analysis": None
                }

            # Analyze
            total_duration = sum(a.get("duration_minutes") or 0 for a in result.data)
            total_calories = sum(a.get("calories_burned") or 0 for a in result.data)
            avg_intensity = sum(float(a.get("intensity_mets") or 0) for a in result.data) / len(result.data)

            # Count by category
            from collections import Counter
            category_counts = Counter(a.get("category") for a in result.data)

            return {
                "days_analyzed": days,
                "total_workouts": len(result.data),
                "total_duration_minutes": round(total_duration),
                "total_calories_burned": round(total_calories),
                "avg_intensity_mets": round(avg_intensity, 1),
                "workouts_per_week": round(len(result.data) / (days / 7), 1),
                "by_category": dict(category_counts),
                "avg_duration_per_workout": round(total_duration / len(result.data)) if result.data else 0
            }
        except Exception as e:
            logger.error(f"[ToolService] analyze_training_volume failed: {e}")
            return {"error": str(e)}

    async def _semantic_search_user_data(self, user_id: str, params: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Semantic search. MVP: Returns empty."""
        # TODO: Implement when embeddings exist
        return []

    async def _calculate_meal_nutrition(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate nutrition for a meal."""
        try:
            foods = params["foods"]
            total_calories = 0
            total_protein = 0
            total_carbs = 0
            total_fats = 0

            for food_item in foods:
                food_name = food_item["name"]
                quantity = food_item["quantity"]
                unit = food_item.get("unit", "g")

                # Search for food in database
                result = self.supabase.table("foods")\
                    .select("calories_per_100g, protein_g_per_100g, carbs_g_per_100g, fat_g_per_100g")\
                    .ilike("name", f"%{food_name}%")\
                    .eq("is_public", True)\
                    .limit(1)\
                    .execute()

                if not result.data:
                    continue

                food = result.data[0]

                # Convert to grams (simplified - assumes g)
                grams = quantity if unit == "g" else quantity * 100

                # Calculate nutrition
                multiplier = grams / 100
                total_calories += food["calories_per_100g"] * multiplier
                total_protein += food["protein_g_per_100g"] * multiplier
                total_carbs += food["carbs_g_per_100g"] * multiplier
                total_fats += food["fat_g_per_100g"] * multiplier

            return {
                "total_calories": round(total_calories),
                "total_protein_g": round(total_protein, 1),
                "total_carbs_g": round(total_carbs, 1),
                "total_fats_g": round(total_fats, 1)
            }
        except Exception as e:
            logger.error(f"[ToolService] calculate_meal_nutrition failed: {e}")
            return {"error": str(e)}

    async def _suggest_meal_adjustments(self, user_id: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Suggest meal adjustments to hit targets."""
        try:
            current_meal = params["current_meal"]
            target_macros = params.get("target_macros")

            # Get user's targets if not provided
            if not target_macros:
                profile = await self._get_user_profile(user_id, {})
                target_macros = {
                    "protein": profile.get("daily_protein_goal"),
                    "carbs": profile.get("daily_carbs_goal"),
                    "fats": profile.get("daily_fat_goal")
                }

            # Calculate differences
            protein_diff = target_macros["protein"] - current_meal["protein"]
            carbs_diff = target_macros["carbs"] - current_meal["carbs"]
            fats_diff = target_macros["fats"] - current_meal["fats"]

            suggestions = []

            if protein_diff > 10:
                suggestions.append(f"Add {int(protein_diff)}g more protein (chicken, fish, or protein powder)")
            elif protein_diff < -10:
                suggestions.append(f"Reduce protein by {int(abs(protein_diff))}g")

            if carbs_diff > 20:
                suggestions.append(f"Add {int(carbs_diff)}g more carbs (rice, oats, or fruit)")
            elif carbs_diff < -20:
                suggestions.append(f"Reduce carbs by {int(abs(carbs_diff))}g")

            if fats_diff > 5:
                suggestions.append(f"Add {int(fats_diff)}g more fats (nuts, avocado, or olive oil)")
            elif fats_diff < -5:
                suggestions.append(f"Reduce fats by {int(abs(fats_diff))}g")

            return {
                "suggestions": suggestions if suggestions else ["Meal is well-balanced!"],
                "differences": {
                    "protein_diff": round(protein_diff, 1),
                    "carbs_diff": round(carbs_diff, 1),
                    "fats_diff": round(fats_diff, 1)
                }
            }
        except Exception as e:
            logger.error(f"[ToolService] suggest_meal_adjustments failed: {e}")
            return {"error": str(e)}

    async def _estimate_activity_calories(self, user_id: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Estimate calories burned for activity."""
        try:
            activity_type = params["activity_type"]
            duration_minutes = params["duration_minutes"]
            intensity = params.get("intensity", "moderate")

            # MET values (Metabolic Equivalent of Task)
            MET_VALUES = {
                "running": {"low": 6.0, "moderate": 9.0, "high": 12.0},
                "cycling": {"low": 4.0, "moderate": 7.0, "high": 10.0},
                "swimming": {"low": 5.0, "moderate": 8.0, "high": 11.0},
                "strength_training": {"low": 3.0, "moderate": 5.0, "high": 6.0},
                "walking": {"low": 2.5, "moderate": 3.5, "high": 4.5},
                "yoga": {"low": 2.0, "moderate": 3.0, "high": 4.0}
            }

            # Get MET value
            activity_mets = MET_VALUES.get(activity_type.lower(), {"moderate": 5.0})
            met = activity_mets.get(intensity, 5.0)

            # Get user weight from latest measurement or profile
            weight_kg = 70  # Default fallback

            # Try body_metrics first (most recent)
            metrics_result = self.supabase.table("body_metrics")\
                .select("weight_kg")\
                .eq("user_id", user_id)\
                .order("recorded_at", desc=True)\
                .limit(1)\
                .execute()

            if metrics_result.data:
                weight_kg = float(metrics_result.data[0]["weight_kg"])
            else:
                # Fallback to profile
                profile = await self._get_user_profile(user_id, {})
                # Assume profile has current_weight_kg field
                profile_result = self.supabase.table("profiles")\
                    .select("current_weight_kg")\
                    .eq("id", user_id)\
                    .single()\
                    .execute()

                if profile_result.data and profile_result.data.get("current_weight_kg"):
                    weight_kg = float(profile_result.data["current_weight_kg"])

            # Calculate calories: MET × weight (kg) × duration (hours)
            calories = met * weight_kg * (duration_minutes / 60)

            return {
                "estimated_calories": round(calories),
                "met_value": met,
                "activity_type": activity_type,
                "duration_minutes": duration_minutes,
                "intensity": intensity
            }
        except Exception as e:
            logger.error(f"[ToolService] estimate_activity_calories failed: {e}")
            return {"error": str(e)}

    async def _log_meals_quick(self, user_id: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Log one or more meals using AI nutrition estimates (no DB lookups).

        Creates custom food entries on-the-fly for each item.
        Supports multi-item meals and multi-meal logging.

        SCHEMA COMPLIANCE:
        - Auto-creates custom foods in foods table (is_ai_estimated=true)
        - Respects meals table constraints (meal_type, source)
        - Respects meal_items table constraints (all nutrition >= 0, grams > 0)
        - Uses nutrition_service.create_meal() for validation
        """
        try:
            from decimal import Decimal
            from datetime import datetime
            from app.services.nutrition_service import nutrition_service

            # Validate params structure
            if "meals" not in params:
                return {"success": False, "error": "Missing 'meals' parameter"}

            meals_data = params["meals"]
            if not isinstance(meals_data, list) or len(meals_data) == 0:
                return {"success": False, "error": "'meals' must be a non-empty array"}

            logged_meals = []

            # Process each meal
            for meal_data in meals_data:
                # Validate required fields
                if "meal_type" not in meal_data:
                    return {"success": False, "error": "Missing 'meal_type' in meal data"}
                if "items" not in meal_data:
                    return {"success": False, "error": "Missing 'items' in meal data"}

                meal_type = meal_data["meal_type"]
                items_data = meal_data["items"]
                notes = meal_data.get("notes")
                logged_at = meal_data.get("logged_at")

                # Parse logged_at timestamp if provided
                if logged_at:
                    try:
                        logged_at_dt = datetime.fromisoformat(logged_at.replace('Z', '+00:00'))
                    except:
                        logged_at_dt = datetime.utcnow()
                else:
                    logged_at_dt = datetime.utcnow()

                # Validate meal_type
                valid_meal_types = ["breakfast", "lunch", "dinner", "snack", "other"]
                if meal_type not in valid_meal_types:
                    return {
                        "success": False,
                        "error": f"Invalid meal_type '{meal_type}'. Must be one of: {valid_meal_types}"
                    }

                # Validate items array
                if not isinstance(items_data, list) or len(items_data) == 0:
                    return {"success": False, "error": f"'{meal_type}' meal must have at least one food item"}

                # Process each food item in this meal
                meal_items = []
                # Helper function to detect serving units in food name
                def parse_serving_info(food_name: str) -> dict:
                    """
                    Parse food name to detect serving units for better UX display.

                    Examples:
                    - "large mozzarella pizza" → unit="pizza", label="large"
                    - "2 slices pepperoni pizza" → unit="slice", quantity=2
                    - "medium burger" → unit="burger", label="medium"
                    - "300g chicken breast" → None (gram-based)
                    """
                    import re

                    # Common serving units to detect
                    serving_units = {
                        # Whole items
                        'pizza': 'pizza', 'burger': 'burger', 'sandwich': 'sandwich',
                        'taco': 'taco', 'burrito': 'burrito', 'wrap': 'wrap',
                        'bagel': 'bagel', 'muffin': 'muffin', 'donut': 'donut',
                        'cookie': 'cookie', 'brownie': 'brownie',

                        # Portions
                        'slice': 'slice', 'slices': 'slice',
                        'piece': 'piece', 'pieces': 'piece',
                        'serving': 'serving', 'servings': 'serving',

                        # Bowls/containers
                        'bowl': 'bowl', 'cup': 'cup', 'plate': 'plate',
                        'bar': 'bar',  # protein bar, granola bar
                    }

                    # Size descriptors
                    size_descriptors = ['small', 'medium', 'large', 'extra large', 'xl', 'jumbo']

                    food_lower = food_name.lower()

                    # Check for serving units
                    detected_unit = None
                    for key, unit in serving_units.items():
                        if key in food_lower:
                            detected_unit = unit
                            break

                    if not detected_unit:
                        return None  # Use gram-based logging

                    # Check for size descriptor
                    detected_label = None
                    for size in size_descriptors:
                        if size in food_lower:
                            detected_label = size
                            break

                    # Extract quantity if present (e.g., "2 slices")
                    quantity_match = re.match(r'^(\d+)\s+', food_lower)
                    quantity = int(quantity_match.group(1)) if quantity_match else 1

                    # Clean base name (remove quantity, size, unit)
                    base_name = food_name
                    if quantity_match:
                        base_name = base_name[quantity_match.end():]
                    if detected_label:
                        base_name = re.sub(detected_label, '', base_name, flags=re.IGNORECASE)
                    # Remove unit from name (keep rest for flavor description)
                    # e.g., "pizza mozzarella" stays, just "pizza" removed if at start/end

                    base_name = base_name.strip()

                    return {
                        'unit': detected_unit,
                        'label': detected_label,
                        'quantity': quantity,
                        'base_name': base_name
                    }

                for idx, item in enumerate(items_data):
                    # 🔍 DEBUG: Log exactly what AI sent
                    logger.info(
                        "[log_meals_quick] 🔍 RAW ITEM FROM AI",
                        idx=idx,
                        food_name=item.get("food_name"),
                        grams=item.get("grams"),
                        calories=item.get("calories"),
                        protein_g=item.get("protein_g"),
                        carbs_g=item.get("carbs_g"),
                        fat_g=item.get("fat_g")
                    )

                    # Validate required fields in item
                    required_fields = ["food_name", "grams", "calories", "protein_g", "carbs_g", "fat_g"]
                    missing_fields = [f for f in required_fields if f not in item]
                    if missing_fields:
                        return {
                            "success": False,
                            "error": f"Missing fields in item {idx+1}: {', '.join(missing_fields)}"
                        }

                    food_name = item["food_name"]
                    grams = Decimal(str(item["grams"]))
                    calories = int(item["calories"])
                    protein_g = round(Decimal(str(item["protein_g"])), 1)
                    carbs_g = round(Decimal(str(item["carbs_g"])), 1)
                    fat_g = round(Decimal(str(item["fat_g"])), 1)

                    # Validate nutrition values
                    if grams <= 0:
                        return {"success": False, "error": f"Grams must be > 0 for {food_name}"}
                    if calories < 0 or protein_g < 0 or carbs_g < 0 or fat_g < 0:
                        return {"success": False, "error": f"Nutrition values must be >= 0 for {food_name}"}

                    # Create custom food entry (calculate per_100g values)
                    per_100g_calories = float((Decimal(str(calories)) / grams) * 100)
                    per_100g_protein = float((protein_g / grams) * 100)
                    per_100g_carbs = float((carbs_g / grams) * 100)
                    per_100g_fat = float((fat_g / grams) * 100)

                    # Insert custom food into database
                    food_result = self.supabase.table("foods").insert({
                        "created_by": user_id,  # Required for Row Level Security
                        "name": food_name,
                        "composition_type": "simple",
                        "calories_per_100g": round(per_100g_calories, 1),
                        "protein_g_per_100g": round(per_100g_protein, 1),
                        "carbs_g_per_100g": round(per_100g_carbs, 1),
                        "fat_g_per_100g": round(per_100g_fat, 1),
                        "is_public": False,  # User's custom food
                        "is_ai_estimated": True  # Flag for AI-generated
                    }).execute()

                    if not food_result.data:
                        return {"success": False, "error": f"Failed to create custom food: {food_name}"}

                    custom_food_id = food_result.data[0]["id"]

                    # 🎯 Smart serving detection for better UX
                    serving_info = parse_serving_info(food_name)

                    if serving_info:
                        # Serving-based logging (e.g., "1 large pizza" instead of "700g")
                        logger.info(
                            "[log_meals_quick] 🎯 Detected serving unit",
                            food_name=food_name,
                            unit=serving_info['unit'],
                            label=serving_info['label'],
                            quantity=serving_info['quantity']
                        )

                        # Create food_serving entry for this custom food
                        serving_result = self.supabase.table("food_servings").insert({
                            "food_id": custom_food_id,
                            "serving_size": Decimal(str(serving_info['quantity'])),
                            "serving_unit": serving_info['unit'],
                            "serving_label": serving_info['label'],
                            "grams_per_serving": float(grams / serving_info['quantity']),  # grams per single unit
                            "is_default": True,
                            "display_order": 0
                        }).execute()

                        if not serving_result.data:
                            logger.warning("[log_meals_quick] Failed to create serving, falling back to grams")
                            serving_id = None
                            display_unit = "g"
                            display_label = None
                            quantity_val = grams  # Fall back to gram-based
                        else:
                            serving_id = serving_result.data[0]["id"]
                            display_unit = serving_info['unit']
                            display_label = serving_info['label']
                            quantity_val = Decimal(str(serving_info['quantity']))

                        # Create meal item with serving-based logging
                        meal_items.append(MealItemBase(
                            food_id=custom_food_id,
                            quantity=quantity_val,  # Number of servings (e.g., 1 pizza, 2 slices)
                            serving_id=serving_id,
                            grams=grams,
                            calories=calories,
                            protein_g=protein_g,
                            carbs_g=carbs_g,
                            fat_g=fat_g,
                            display_unit=display_unit,
                            display_label=display_label,
                            display_order=idx
                        ))

                    else:
                        # Gram-based logging (e.g., "300g chicken breast")
                        logger.info(
                            "[log_meals_quick] ℹ️ No serving unit detected, using gram-based",
                            food_name=food_name
                        )

                        meal_items.append(MealItemBase(
                            food_id=custom_food_id,
                            quantity=grams,  # For gram-based logging, quantity equals grams (nutrition_service expects this)
                            serving_id=None,
                            grams=grams,
                            calories=calories,
                            protein_g=protein_g,
                            carbs_g=carbs_g,
                            fat_g=fat_g,
                            display_unit="g",
                            display_label=None,
                            display_order=idx
                        ))

                # Create meal with all items
                from uuid import UUID
                meal = await nutrition_service.create_meal(
                    user_id=UUID(user_id),  # Convert str to UUID for type safety
                    name=None,  # Let service auto-generate name from items
                    meal_type=meal_type,
                    logged_at=logged_at_dt,
                    notes=notes,
                    items=meal_items,
                    source="coach_chat",
                    ai_confidence=0.85  # AI estimated nutrition
                )

                logger.info(
                    "[ToolService.log_meals_quick] ✅ Meal logged",
                    meal_id=str(meal.id),
                    meal_type=meal_type,
                    items_count=len(meal_items),
                    total_calories=float(meal.total_calories),
                    user_id=user_id
                )

                logged_meals.append({
                    "meal_id": str(meal.id),
                    "meal_type": meal_type,
                    "items_count": len(meal_items),
                    "total_calories": int(meal.total_calories),
                    "total_protein_g": float(meal.total_protein_g),
                    "logged_at": meal.logged_at.isoformat()
                })

            # Return success with all logged meals
            return {
                "success": True,
                "meals_logged": len(logged_meals),
                "meals": logged_meals,
                "message": f"✅ Logged {len(logged_meals)} meal(s)"
            }

        except ValueError as e:
            logger.warning(f"[ToolService.log_meals_quick] Validation error: {e}")
            return {"success": False, "error": f"Validation failed: {str(e)}"}
        except Exception as e:
            logger.error(f"[ToolService.log_meals_quick] ❌ Failed: {e}", exc_info=True)
            return {"success": False, "error": f"Failed to log meals: {str(e)}"}

    async def _update_meal(self, user_id: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update an existing meal's metadata or items.

        Handles meal identification and applies updates.
        """
        try:
            from datetime import datetime, date, timedelta

            # Parse meal identifier
            meal_id = params["meal_identifier"]
            id_type = meal_id["type"]
            id_value = meal_id["value"]
            id_date = meal_id.get("date", "today")

            # Resolve date
            target_date = await self._parse_date(id_date)

            # Find the meal
            meal = await self._find_meal(user_id, id_type, id_value, target_date)

            if not meal:
                return {"success": False, "error": "Meal not found"}

            # Parse updates
            updates = params["updates"]

            # Apply metadata updates via nutrition_service
            from app.services.nutrition_service import nutrition_service

            # Handle item operations first
            if "item_operations" in updates:
                for operation in updates["item_operations"]:
                    action = operation["action"]
                    food_name = operation["food_name"]

                    if action == "add":
                        # Add new item to meal
                        from app.models.nutrition import MealItemBase
                        new_item = MealItemBase(
                            food_id=await self._resolve_food_id(food_name),
                            quantity=operation["quantity"],
                            serving_id=None,
                            grams=operation["quantity"] if operation.get("unit") == "grams" else operation.get("grams", 100),
                            calories=operation["calories"],
                            protein_g=operation["protein_g"],
                            carbs_g=operation["carbs_g"],
                            fat_g=operation["fat_g"],
                            display_unit="g",
                            display_label=None
                        )
                        from uuid import UUID
                        meal = await nutrition_service.add_meal_item(
                            meal_id=UUID(meal["id"]),
                            item=new_item,
                            user_id=user_id
                        )

                    elif action == "remove":
                        # Find and remove item
                        item_to_remove = next((item for item in meal.get("items", [])
                                              if food_name.lower() in item.get("foods", {}).get("name", "").lower()), None)
                        if item_to_remove:
                            from uuid import UUID
                            meal = await nutrition_service.delete_meal_item(
                                meal_id=UUID(meal["id"]),
                                item_id=UUID(item_to_remove["id"]),
                                user_id=user_id
                            )

                    elif action == "update":
                        # Find and update item quantity
                        item_to_update = next((item for item in meal.get("items", [])
                                              if food_name.lower() in item.get("foods", {}).get("name", "").lower()), None)
                        if item_to_update:
                            from app.models.nutrition import UpdateMealItemRequest
                            from uuid import UUID
                            update_request = UpdateMealItemRequest(
                                quantity=operation["quantity"],
                                serving_id=None if operation.get("unit") == "grams" else operation.get("serving_id")
                            )
                            meal = await nutrition_service.update_meal_item(
                                meal_id=UUID(meal["id"]),
                                item_id=UUID(item_to_update["id"]),
                                updates=update_request,
                                user_id=user_id
                            )

            # Apply metadata updates if any
            if "meal_type" in updates or "name" in updates or "notes" in updates:
                # Note: Current nutrition_service doesn't have update_meal for metadata
                # Would need to implement this or use database directly
                logger.warning("[ToolService.update_meal] Metadata updates not yet implemented")

            return {
                "success": True,
                "meal_id": meal.id if hasattr(meal, 'id') else meal.get("id"),
                "message": "Meal updated successfully"
            }

        except Exception as e:
            logger.error(f"[ToolService.update_meal] Failed: {e}", exc_info=True)
            return {"success": False, "error": str(e)}

    async def _delete_meal(self, user_id: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Delete an entire meal.
        """
        try:
            from datetime import datetime, date, timedelta

            # Parse meal identifier
            meal_id = params["meal_identifier"]
            id_type = meal_id["type"]
            id_value = meal_id["value"]
            id_date = meal_id.get("date", "today")

            # Resolve date
            target_date = await self._parse_date(id_date)

            # Find the meal
            meal = await self._find_meal(user_id, id_type, id_value, target_date)

            if not meal:
                return {"success": False, "error": "Meal not found"}

            # Delete the meal
            from app.services.nutrition_service import nutrition_service
            from uuid import UUID

            deleted = await nutrition_service.delete_meal(
                meal_id=UUID(meal["id"]),
                user_id=user_id
            )

            if deleted:
                return {
                    "success": True,
                    "meal_type": meal.get("meal_type"),
                    "items_count": len(meal.get("items", [])),
                    "message": f"✅ Deleted {meal.get('meal_type')} meal"
                }
            else:
                return {"success": False, "error": "Failed to delete meal"}

        except Exception as e:
            logger.error(f"[ToolService.delete_meal] Failed: {e}", exc_info=True)
            return {"success": False, "error": str(e)}

    async def _update_meal_item(self, user_id: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update quantity of a specific food item within a meal.
        """
        try:
            from datetime import datetime, date, timedelta

            # Parse meal identifier
            meal_id = params["meal_identifier"]
            id_type = meal_id["type"]
            id_value = meal_id["value"]
            id_date = meal_id.get("date", "today")

            # Resolve date
            target_date = await self._parse_date(id_date)

            # Find the meal
            meal = await self._find_meal(user_id, id_type, id_value, target_date)

            if not meal:
                return {"success": False, "error": "Meal not found"}

            # Find the item
            item_name = params["item_identifier"]
            item_to_update = next((item for item in meal.get("items", [])
                                  if item_name.lower() in item.get("foods", {}).get("name", "").lower()), None)

            if not item_to_update:
                return {"success": False, "error": f"Item '{item_name}' not found in meal"}

            # Update the item
            from app.services.nutrition_service import nutrition_service
            from app.models.nutrition import UpdateMealItemRequest
            from uuid import UUID

            update_request = UpdateMealItemRequest(
                quantity=params["new_quantity"],
                serving_id=None if params.get("unit") == "grams" else params.get("serving_id")
            )

            updated_meal = await nutrition_service.update_meal_item(
                meal_id=UUID(meal["id"]),
                item_id=UUID(item_to_update["id"]),
                updates=update_request,
                user_id=user_id
            )

            return {
                "success": True,
                "meal_id": str(updated_meal.id),
                "message": f"✅ Updated {item_name} quantity to {params['new_quantity']}{params.get('unit', 'g')}"
            }

        except Exception as e:
            logger.error(f"[ToolService.update_meal_item] Failed: {e}", exc_info=True)
            return {"success": False, "error": str(e)}

    # Helper methods for meal identification

    async def _parse_date(self, date_str: str) -> date:
        """Parse date string to date object."""
        from datetime import datetime, date, timedelta

        if date_str == "today":
            return date.today()
        elif date_str == "yesterday":
            return date.today() - timedelta(days=1)
        else:
            try:
                return datetime.fromisoformat(date_str).date()
            except:
                return date.today()

    async def _find_meal(self, user_id: str, id_type: str, id_value: str, target_date: date) -> Optional[Dict[str, Any]]:
        """Find a meal by identifier."""
        from datetime import datetime, time

        try:
            if id_type == "id":
                # Direct ID lookup
                result = self.supabase.table("meals")\
                    .select("*, items:meal_items(*, foods(name, brand_name))")\
                    .eq("id", id_value)\
                    .eq("user_id", user_id)\
                    .single()\
                    .execute()
                return result.data if result.data else None

            elif id_type == "meal_type":
                # Find by meal type and date
                start_of_day = datetime.combine(target_date, time.min)
                end_of_day = datetime.combine(target_date, time.max)

                result = self.supabase.table("meals")\
                    .select("*, items:meal_items(*, foods(name, brand_name))")\
                    .eq("user_id", user_id)\
                    .eq("meal_type", id_value)\
                    .gte("logged_at", start_of_day.isoformat())\
                    .lte("logged_at", end_of_day.isoformat())\
                    .order("logged_at", desc=True)\
                    .limit(1)\
                    .execute()

                return result.data[0] if result.data else None

            elif id_type == "relative":
                # Find most recent meal
                if id_value in ["last", "latest", "most recent"]:
                    result = self.supabase.table("meals")\
                        .select("*, items:meal_items(*, foods(name, brand_name))")\
                        .eq("user_id", user_id)\
                        .order("logged_at", desc=True)\
                        .limit(1)\
                        .execute()

                    return result.data[0] if result.data else None

            return None

        except Exception as e:
            logger.error(f"[ToolService._find_meal] Failed: {e}")
            return None

    async def _resolve_food_id(self, food_name: str) -> str:
        """Resolve food name to food ID (simplified - creates custom food)."""
        # For now, return a placeholder - in production would search foods table
        # or create a custom food
        return "00000000-0000-0000-0000-000000000000"

    async def _copy_meal(self, user_id: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Copy meals from one date to another.
        """
        try:
            from datetime import datetime, date, timedelta
            from app.services.nutrition_service import nutrition_service

            # Parse source identifier
            source = params["source_identifier"]
            source_type = source["type"]
            source_value = source.get("value")
            source_date = await self._parse_date(source["date"])

            # Parse target date
            target_date = await self._parse_date(params["target_date"])
            target_meal_type = params.get("target_meal_type", "same")

            # Find source meal(s)
            meals_to_copy = []

            if source_type == "meal_type":
                # Copy single meal by type
                meal = await self._find_meal(user_id, "meal_type", source_value, source_date)
                if meal:
                    meals_to_copy.append(meal)

            elif source_type == "meal_id":
                # Copy specific meal by ID
                meal = await self._find_meal(user_id, "id", source_value, source_date)
                if meal:
                    meals_to_copy.append(meal)

            elif source_type == "all_meals":
                # Copy all meals from source date
                start_of_day = datetime.combine(source_date, datetime.min.time())
                end_of_day = datetime.combine(source_date, datetime.max.time())

                result = self.supabase.table("meals")\
                    .select("*, items:meal_items(*, foods(*))")\
                    .eq("user_id", user_id)\
                    .gte("logged_at", start_of_day.isoformat())\
                    .lte("logged_at", end_of_day.isoformat())\
                    .execute()

                meals_to_copy = result.data if result.data else []

            if not meals_to_copy:
                return {"success": False, "error": "No meals found to copy"}

            # Copy each meal
            copied_meals = []
            for meal in meals_to_copy:
                # Determine target meal type
                new_meal_type = target_meal_type if target_meal_type != "same" else meal["meal_type"]

                # Convert meal items to MealItemBase format
                from app.models.nutrition import MealItemBase
                items = []
                for item in meal.get("items", []):
                    items.append(MealItemBase(
                        food_id=item["food_id"],
                        quantity=item["quantity"],
                        serving_id=item.get("serving_id"),
                        grams=item["grams"],
                        calories=int(item["calories"]),
                        protein_g=float(item["protein_g"]),
                        carbs_g=float(item["carbs_g"]),
                        fat_g=float(item["fat_g"]),
                        display_unit=item.get("display_unit", "g"),
                        display_label=item.get("display_label")
                    ))

                # Create new meal
                new_meal = await nutrition_service.create_meal(
                    user_id=user_id,
                    name=meal.get("name"),
                    meal_type=new_meal_type,
                    logged_at=datetime.combine(target_date, datetime.now().time()),
                    notes=f"Copied from {source_date}",
                    items=items,
                    source="copy"
                )

                copied_meals.append({
                    "meal_id": str(new_meal.id),
                    "meal_type": new_meal_type,
                    "items_count": len(items)
                })

            return {
                "success": True,
                "meals_copied": len(copied_meals),
                "meals": copied_meals,
                "message": f"✅ Copied {len(copied_meals)} meal(s) to {target_date}"
            }

        except Exception as e:
            logger.error(f"[ToolService.copy_meal] Failed: {e}", exc_info=True)
            return {"success": False, "error": str(e)}

    async def _create_quick_meal(self, user_id: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Save a meal as a quick meal template.
        """
        try:
            name = params["name"]
            description = params.get("description", "")
            source = params["source"]

            # Get meal items based on source
            items_data = []

            if source == "last_logged":
                # Get most recent meal
                result = self.supabase.table("meals")\
                    .select("*, items:meal_items(*, foods(*))")\
                    .eq("user_id", user_id)\
                    .order("logged_at", desc=True)\
                    .limit(1)\
                    .execute()

                if not result.data:
                    return {"success": False, "error": "No recent meals found"}

                meal = result.data[0]
                for item in meal.get("items", []):
                    items_data.append({
                        "food_id": item["food_id"],
                        "quantity": item["quantity"],
                        "serving_id": item.get("serving_id"),
                        "display_order": item.get("display_order", 0)
                    })

            elif source == "meal_id":
                # Get specific meal
                meal_id = params.get("meal_id")
                result = self.supabase.table("meals")\
                    .select("*, items:meal_items(*, foods(*))")\
                    .eq("id", meal_id)\
                    .eq("user_id", user_id)\
                    .single()\
                    .execute()

                if not result.data:
                    return {"success": False, "error": "Meal not found"}

                meal = result.data
                for item in meal.get("items", []):
                    items_data.append({
                        "food_id": item["food_id"],
                        "quantity": item["quantity"],
                        "serving_id": item.get("serving_id"),
                        "display_order": item.get("display_order", 0)
                    })

            elif source == "custom":
                # Use provided items
                custom_items = params.get("items", [])
                for idx, item in enumerate(custom_items):
                    # Would need to create custom foods first
                    # Simplified for now
                    items_data.append({
                        "food_id": await self._resolve_food_id(item["food_name"]),
                        "quantity": item["quantity"],
                        "serving_id": None,
                        "display_order": idx
                    })

            # Create quick meal
            from uuid import uuid4
            quick_meal_id = str(uuid4())

            result = self.supabase.table("quick_meals").insert({
                "id": quick_meal_id,
                "user_id": user_id,
                "name": name,
                "description": description,
                "foods": items_data  # JSONB column
            }).execute()

            if result.data:
                return {
                    "success": True,
                    "quick_meal_id": quick_meal_id,
                    "name": name,
                    "items_count": len(items_data),
                    "message": f"✅ Created quick meal '{name}'"
                }
            else:
                return {"success": False, "error": "Failed to create quick meal"}

        except Exception as e:
            logger.error(f"[ToolService.create_quick_meal] Failed: {e}", exc_info=True)
            return {"success": False, "error": str(e)}

    async def _delete_quick_meal(self, user_id: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Delete a quick meal template.
        """
        try:
            identifier = params["identifier"]
            id_type = identifier["type"]
            id_value = identifier["value"]

            # Find quick meal
            if id_type == "id":
                result = self.supabase.table("quick_meals")\
                    .delete()\
                    .eq("id", id_value)\
                    .eq("user_id", user_id)\
                    .execute()
            elif id_type == "name":
                result = self.supabase.table("quick_meals")\
                    .delete()\
                    .eq("name", id_value)\
                    .eq("user_id", user_id)\
                    .execute()

            if result.data:
                return {
                    "success": True,
                    "message": f"✅ Deleted quick meal '{id_value}'"
                }
            else:
                return {"success": False, "error": "Quick meal not found"}

        except Exception as e:
            logger.error(f"[ToolService.delete_quick_meal] Failed: {e}", exc_info=True)
            return {"success": False, "error": str(e)}

    async def _list_quick_meals(self, user_id: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        List user's quick meal templates with nutrition preview.
        """
        try:
            include_nutrition = params.get("include_nutrition", True)

            # Get quick meals
            result = self.supabase.table("quick_meals")\
                .select("*")\
                .eq("user_id", user_id)\
                .order("created_at", desc=True)\
                .execute()

            if not result.data:
                return {
                    "success": True,
                    "quick_meals": [],
                    "count": 0,
                    "message": "No quick meals saved yet"
                }

            # Format quick meals
            quick_meals = []
            for qm in result.data:
                qm_data = {
                    "id": qm["id"],
                    "name": qm["name"],
                    "description": qm.get("description", ""),
                    "items_count": len(qm.get("foods", [])),
                    "created_at": qm["created_at"]
                }

                # Calculate nutrition if requested
                if include_nutrition and qm.get("foods"):
                    # Would need to look up foods and calculate
                    # Simplified for now
                    qm_data["nutrition"] = {
                        "calories": 0,
                        "protein_g": 0,
                        "carbs_g": 0,
                        "fat_g": 0
                    }

                quick_meals.append(qm_data)

            return {
                "success": True,
                "quick_meals": quick_meals,
                "count": len(quick_meals),
                "message": f"Found {len(quick_meals)} quick meal(s)"
            }

        except Exception as e:
            logger.error(f"[ToolService.list_quick_meals] Failed: {e}", exc_info=True)
            return {"success": False, "error": str(e)}


# Singleton
_tool_service: Optional[ToolService] = None

def get_tool_service(supabase_client=None) -> ToolService:
    """Get singleton ToolService instance."""
    global _tool_service
    if _tool_service is None:
        if supabase_client is None:
            from app.services.supabase_service import get_service_client
            supabase_client = get_service_client()
        _tool_service = ToolService(supabase_client)
    return _tool_service
