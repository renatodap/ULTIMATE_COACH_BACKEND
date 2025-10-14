"""
Meal Assembler

Builds meal plans from existing foods database, optimizing for:
- Macro targets (protein, carbs, fat)
- Calorie targets with confidence intervals
- Dietary preferences and restrictions
- Meal timing around training
- Variety and micronutrient density
"""

from typing import List, Dict, Optional, Literal, Tuple
from dataclasses import dataclass
from enum import Enum
import random


class MealType(str, Enum):
    """Meal timing categories"""

    BREAKFAST = "breakfast"
    LUNCH = "lunch"
    DINNER = "dinner"
    SNACK = "snack"
    PRE_WORKOUT = "pre_workout"
    POST_WORKOUT = "post_workout"


class DietaryPreference(str, Enum):
    """Dietary restriction types"""

    NONE = "none"
    VEGETARIAN = "vegetarian"
    VEGAN = "vegan"
    PESCATARIAN = "pescatarian"
    KETO = "keto"
    PALEO = "paleo"
    HALAL = "halal"
    KOSHER = "kosher"


@dataclass
class FoodItem:
    """Single food item from database"""

    food_id: str
    name: str
    calories: float
    protein_g: float
    carbs_g: float
    fat_g: float
    fiber_g: float
    serving_size: str
    serving_size_g: float
    food_group: str  # protein, vegetable, fruit, grain, dairy, fat
    tags: List[str]  # vegetarian, vegan, high_protein, etc.


@dataclass
class MealComponent:
    """A food item with specific quantity in a meal"""

    food: FoodItem
    servings: float  # Number of servings
    calories: float
    protein_g: float
    carbs_g: float
    fat_g: float


@dataclass
class Meal:
    """Complete meal with multiple food components"""

    meal_id: str
    meal_type: MealType
    meal_name: str
    components: List[MealComponent]
    total_calories: float
    total_protein_g: float
    total_carbs_g: float
    total_fat_g: float
    total_fiber_g: float
    prep_notes: str


@dataclass
class DailyMealPlan:
    """All meals for a single day"""

    day_number: int
    training_day: bool
    meals: List[Meal]
    daily_totals: Dict[str, float]  # calories, protein, carbs, fat
    adherence_to_targets: Dict[str, float]  # % deviation from targets


@dataclass
class MacroTargets:
    """Daily macro targets"""

    calories: int
    protein_g: int
    carbs_g: int
    fat_g: int
    fiber_g: int = 30  # Minimum fiber target


# Food Group Templates
# High-protein foods (>20g protein per serving)
HIGH_PROTEIN_FOODS = [
    {
        "name": "Chicken Breast (grilled)",
        "calories": 165,
        "protein": 31,
        "carbs": 0,
        "fat": 3.6,
        "fiber": 0,
        "serving": "100g",
        "serving_g": 100,
        "group": "protein",
        "tags": ["high_protein", "lean"],
    },
    {
        "name": "Salmon (baked)",
        "calories": 206,
        "protein": 22,
        "carbs": 0,
        "fat": 13,
        "fiber": 0,
        "serving": "100g",
        "serving_g": 100,
        "group": "protein",
        "tags": ["high_protein", "omega3", "pescatarian"],
    },
    {
        "name": "Greek Yogurt (non-fat)",
        "calories": 100,
        "protein": 17,
        "carbs": 7,
        "fat": 0.7,
        "fiber": 0,
        "serving": "170g",
        "serving_g": 170,
        "group": "dairy",
        "tags": ["high_protein", "vegetarian"],
    },
    {
        "name": "Eggs (whole)",
        "calories": 155,
        "protein": 13,
        "carbs": 1,
        "fat": 11,
        "fiber": 0,
        "serving": "2 large",
        "serving_g": 100,
        "group": "protein",
        "tags": ["high_protein", "vegetarian"],
    },
    {
        "name": "Tofu (extra firm)",
        "calories": 145,
        "protein": 17,
        "carbs": 3,
        "fat": 9,
        "fiber": 2,
        "serving": "100g",
        "serving_g": 100,
        "group": "protein",
        "tags": ["high_protein", "vegan", "vegetarian"],
    },
    {
        "name": "Lean Ground Beef (93/7)",
        "calories": 182,
        "protein": 20,
        "carbs": 0,
        "fat": 10,
        "fiber": 0,
        "serving": "100g",
        "serving_g": 100,
        "group": "protein",
        "tags": ["high_protein"],
    },
    {
        "name": "Tuna (canned in water)",
        "calories": 116,
        "protein": 26,
        "carbs": 0,
        "fat": 1,
        "fiber": 0,
        "serving": "100g",
        "serving_g": 100,
        "group": "protein",
        "tags": ["high_protein", "lean", "pescatarian"],
    },
    {
        "name": "Cottage Cheese (low-fat)",
        "calories": 82,
        "protein": 14,
        "carbs": 5,
        "fat": 1.2,
        "fiber": 0,
        "serving": "100g",
        "serving_g": 100,
        "group": "dairy",
        "tags": ["high_protein", "vegetarian"],
    },
]

# Complex carbs
CARB_FOODS = [
    {
        "name": "Brown Rice (cooked)",
        "calories": 112,
        "protein": 2.3,
        "carbs": 24,
        "fat": 0.9,
        "fiber": 1.8,
        "serving": "100g",
        "serving_g": 100,
        "group": "grain",
        "tags": ["vegan", "vegetarian", "whole_grain"],
    },
    {
        "name": "Sweet Potato (baked)",
        "calories": 90,
        "protein": 2,
        "carbs": 21,
        "fat": 0.2,
        "fiber": 3.3,
        "serving": "100g",
        "serving_g": 100,
        "group": "vegetable",
        "tags": ["vegan", "vegetarian", "nutrient_dense"],
    },
    {
        "name": "Oatmeal (cooked)",
        "calories": 71,
        "protein": 2.5,
        "carbs": 12,
        "fat": 1.5,
        "fiber": 1.7,
        "serving": "100g",
        "serving_g": 100,
        "group": "grain",
        "tags": ["vegan", "vegetarian", "whole_grain"],
    },
    {
        "name": "Quinoa (cooked)",
        "calories": 120,
        "protein": 4.4,
        "carbs": 21,
        "fat": 1.9,
        "fiber": 2.8,
        "serving": "100g",
        "serving_g": 100,
        "group": "grain",
        "tags": ["vegan", "vegetarian", "complete_protein"],
    },
    {
        "name": "Whole Wheat Pasta (cooked)",
        "calories": 124,
        "protein": 5.3,
        "carbs": 26,
        "fat": 0.5,
        "fiber": 3.9,
        "serving": "100g",
        "serving_g": 100,
        "group": "grain",
        "tags": ["vegan", "vegetarian", "whole_grain"],
    },
    {
        "name": "Banana",
        "calories": 89,
        "protein": 1.1,
        "carbs": 23,
        "fat": 0.3,
        "fiber": 2.6,
        "serving": "1 medium",
        "serving_g": 118,
        "group": "fruit",
        "tags": ["vegan", "vegetarian", "pre_workout"],
    },
]

# Vegetables (mostly fiber and micronutrients)
VEGETABLE_FOODS = [
    {
        "name": "Broccoli (steamed)",
        "calories": 35,
        "protein": 2.4,
        "carbs": 7,
        "fat": 0.4,
        "fiber": 3.3,
        "serving": "100g",
        "serving_g": 100,
        "group": "vegetable",
        "tags": ["vegan", "vegetarian", "nutrient_dense"],
    },
    {
        "name": "Spinach (raw)",
        "calories": 23,
        "protein": 2.9,
        "carbs": 3.6,
        "fat": 0.4,
        "fiber": 2.2,
        "serving": "100g",
        "serving_g": 100,
        "group": "vegetable",
        "tags": ["vegan", "vegetarian", "nutrient_dense"],
    },
    {
        "name": "Bell Peppers (raw)",
        "calories": 31,
        "protein": 1,
        "carbs": 6,
        "fat": 0.3,
        "fiber": 2.1,
        "serving": "100g",
        "serving_g": 100,
        "group": "vegetable",
        "tags": ["vegan", "vegetarian"],
    },
    {
        "name": "Mixed Greens Salad",
        "calories": 15,
        "protein": 1.4,
        "carbs": 2.4,
        "fat": 0.2,
        "fiber": 1.5,
        "serving": "100g",
        "serving_g": 100,
        "group": "vegetable",
        "tags": ["vegan", "vegetarian", "low_calorie"],
    },
]

# Healthy fats
FAT_FOODS = [
    {
        "name": "Almonds",
        "calories": 579,
        "protein": 21,
        "carbs": 22,
        "fat": 50,
        "fiber": 12,
        "serving": "100g",
        "serving_g": 100,
        "group": "fat",
        "tags": ["vegan", "vegetarian", "healthy_fat"],
    },
    {
        "name": "Avocado",
        "calories": 160,
        "protein": 2,
        "carbs": 9,
        "fat": 15,
        "fiber": 7,
        "serving": "100g",
        "serving_g": 100,
        "group": "fat",
        "tags": ["vegan", "vegetarian", "healthy_fat"],
    },
    {
        "name": "Olive Oil",
        "calories": 119,
        "protein": 0,
        "carbs": 0,
        "fat": 14,
        "fiber": 0,
        "serving": "1 tbsp",
        "serving_g": 14,
        "group": "fat",
        "tags": ["vegan", "vegetarian", "healthy_fat"],
    },
    {
        "name": "Peanut Butter (natural)",
        "calories": 188,
        "protein": 8,
        "carbs": 7,
        "fat": 16,
        "fiber": 2,
        "serving": "2 tbsp",
        "serving_g": 32,
        "group": "fat",
        "tags": ["vegan", "vegetarian", "healthy_fat"],
    },
]


class MealAssembler:
    """Assembles daily meal plans from food database"""

    def __init__(self):
        # Load food database (in production, this would query Supabase)
        self.foods_db = self._load_food_database()

    def _load_food_database(self) -> List[FoodItem]:
        """Load foods from database (mock for now, will query Supabase)"""
        foods = []

        # Combine all food categories
        all_foods = (
            HIGH_PROTEIN_FOODS + CARB_FOODS + VEGETABLE_FOODS + FAT_FOODS
        )

        for idx, food_data in enumerate(all_foods):
            foods.append(
                FoodItem(
                    food_id=f"food_{idx}",
                    name=food_data["name"],
                    calories=food_data["calories"],
                    protein_g=food_data["protein"],
                    carbs_g=food_data["carbs"],
                    fat_g=food_data["fat"],
                    fiber_g=food_data["fiber"],
                    serving_size=food_data["serving"],
                    serving_size_g=food_data["serving_g"],
                    food_group=food_data["group"],
                    tags=food_data["tags"],
                )
            )

        return foods

    def generate_daily_meal_plan(
        self,
        targets: MacroTargets,
        training_day: bool,
        dietary_preference: DietaryPreference = DietaryPreference.NONE,
        allergies: List[str] = None,
        day_number: int = 1,
    ) -> DailyMealPlan:
        """
        Generate a complete daily meal plan hitting macro targets.

        Args:
            targets: Daily macro targets (calories, protein, carbs, fat)
            training_day: Whether this is a training day (affects meal timing)
            dietary_preference: Vegetarian, vegan, etc.
            allergies: List of allergens to avoid
            day_number: Day number in the plan (for variety)

        Returns:
            DailyMealPlan with all meals and totals
        """
        allergies = allergies or []

        # Filter foods by dietary preference
        available_foods = self._filter_foods(dietary_preference, allergies)

        # Determine meal structure
        if training_day:
            meal_structure = [
                (MealType.BREAKFAST, 0.25),
                (MealType.PRE_WORKOUT, 0.15),
                (MealType.LUNCH, 0.25),
                (MealType.POST_WORKOUT, 0.15),
                (MealType.DINNER, 0.20),
            ]
        else:
            meal_structure = [
                (MealType.BREAKFAST, 0.30),
                (MealType.LUNCH, 0.35),
                (MealType.SNACK, 0.10),
                (MealType.DINNER, 0.25),
            ]

        # Generate each meal
        meals = []
        for meal_type, calorie_fraction in meal_structure:
            meal_targets = MacroTargets(
                calories=int(targets.calories * calorie_fraction),
                protein_g=int(targets.protein_g * calorie_fraction),
                carbs_g=int(targets.carbs_g * calorie_fraction),
                fat_g=int(targets.fat_g * calorie_fraction),
            )

            meal = self._build_meal(
                meal_type=meal_type,
                targets=meal_targets,
                available_foods=available_foods,
                day_number=day_number,
                training_day=training_day,
            )
            meals.append(meal)

        # Calculate daily totals
        daily_totals = {
            "calories": sum(m.total_calories for m in meals),
            "protein": sum(m.total_protein_g for m in meals),
            "carbs": sum(m.total_carbs_g for m in meals),
            "fat": sum(m.total_fat_g for m in meals),
            "fiber": sum(m.total_fiber_g for m in meals),
        }

        # Calculate adherence (% deviation from targets)
        adherence = {
            "calories": (daily_totals["calories"] / targets.calories - 1) * 100,
            "protein": (daily_totals["protein"] / targets.protein_g - 1) * 100,
            "carbs": (daily_totals["carbs"] / targets.carbs_g - 1) * 100,
            "fat": (daily_totals["fat"] / targets.fat_g - 1) * 100,
        }

        return DailyMealPlan(
            day_number=day_number,
            training_day=training_day,
            meals=meals,
            daily_totals=daily_totals,
            adherence_to_targets=adherence,
        )

    def _filter_foods(
        self, dietary_preference: DietaryPreference, allergies: List[str]
    ) -> List[FoodItem]:
        """Filter foods by dietary restrictions and allergies"""
        filtered = self.foods_db.copy()

        # Filter by dietary preference
        if dietary_preference == DietaryPreference.VEGAN:
            filtered = [f for f in filtered if "vegan" in f.tags]
        elif dietary_preference == DietaryPreference.VEGETARIAN:
            filtered = [f for f in filtered if "vegetarian" in f.tags]
        elif dietary_preference == DietaryPreference.PESCATARIAN:
            filtered = [
                f
                for f in filtered
                if "vegetarian" in f.tags or "pescatarian" in f.tags
            ]

        # Filter by allergies
        for allergen in allergies:
            allergen_lower = allergen.lower()
            if allergen_lower == "dairy":
                filtered = [f for f in filtered if f.food_group != "dairy"]
            elif allergen_lower == "nuts":
                filtered = [
                    f for f in filtered if "almond" not in f.name.lower() and "peanut" not in f.name.lower()
                ]
            elif allergen_lower == "shellfish":
                filtered = [
                    f for f in filtered if "shrimp" not in f.name.lower() and "crab" not in f.name.lower()
                ]

        return filtered

    def _build_meal(
        self,
        meal_type: MealType,
        targets: MacroTargets,
        available_foods: List[FoodItem],
        day_number: int,
        training_day: bool,
    ) -> Meal:
        """Build a single meal hitting macro targets"""
        components = []

        # Step 1: Add protein source (prioritize hitting protein target)
        protein_foods = [f for f in available_foods if f.food_group == "protein"]
        if protein_foods:
            protein_food = self._select_varied_food(protein_foods, day_number, meal_type)
            protein_servings = targets.protein_g / protein_food.protein_g
            components.append(self._create_component(protein_food, protein_servings))

        # Step 2: Add carb source (training days need more carbs)
        carb_foods = [f for f in available_foods if f.food_group in ["grain", "fruit"]]
        if carb_foods:
            carb_food = self._select_varied_food(carb_foods, day_number, meal_type)
            remaining_carbs = targets.carbs_g - sum(c.carbs_g for c in components)
            if remaining_carbs > 0:
                carb_servings = remaining_carbs / carb_food.carbs_g
                components.append(self._create_component(carb_food, carb_servings))

        # Step 3: Add vegetables (fiber and micronutrients)
        veg_foods = [f for f in available_foods if f.food_group == "vegetable"]
        if veg_foods and meal_type in [MealType.LUNCH, MealType.DINNER]:
            veg_food = self._select_varied_food(veg_foods, day_number, meal_type)
            components.append(self._create_component(veg_food, 1.5))  # 150g serving

        # Step 4: Add fat source to hit fat target
        fat_foods = [f for f in available_foods if f.food_group == "fat"]
        if fat_foods:
            remaining_fat = targets.fat_g - sum(c.fat_g for c in components)
            if remaining_fat > 5:  # Only add if significantly short
                fat_food = self._select_varied_food(fat_foods, day_number, meal_type)
                fat_servings = remaining_fat / fat_food.fat_g
                components.append(self._create_component(fat_food, min(fat_servings, 2.0)))

        # Calculate totals
        total_calories = sum(c.calories for c in components)
        total_protein = sum(c.protein_g for c in components)
        total_carbs = sum(c.carbs_g for c in components)
        total_fat = sum(c.fat_g for c in components)
        total_fiber = sum(
            c.food.fiber_g * c.servings for c in components
        )

        # Generate meal name and prep notes
        meal_name = self._generate_meal_name(meal_type, components)
        prep_notes = self._generate_prep_notes(components, meal_type)

        return Meal(
            meal_id=f"meal_{day_number}_{meal_type.value}",
            meal_type=meal_type,
            meal_name=meal_name,
            components=components,
            total_calories=total_calories,
            total_protein_g=total_protein,
            total_carbs_g=total_carbs,
            total_fat_g=total_fat,
            total_fiber_g=total_fiber,
            prep_notes=prep_notes,
        )

    def _select_varied_food(
        self, foods: List[FoodItem], day_number: int, meal_type: MealType
    ) -> FoodItem:
        """Select food with variety (rotate through options)"""
        if not foods:
            raise ValueError("No foods available for selection")

        # Use day number and meal type as seed for variety
        seed = day_number + hash(meal_type.value)
        index = seed % len(foods)
        return foods[index]

    def _create_component(self, food: FoodItem, servings: float) -> MealComponent:
        """Create a meal component with scaled macros"""
        # Round servings to reasonable precision
        servings = round(servings, 2)

        return MealComponent(
            food=food,
            servings=servings,
            calories=food.calories * servings,
            protein_g=food.protein_g * servings,
            carbs_g=food.carbs_g * servings,
            fat_g=food.fat_g * servings,
        )

    def _generate_meal_name(self, meal_type: MealType, components: List[MealComponent]) -> str:
        """Generate descriptive meal name"""
        if meal_type == MealType.BREAKFAST:
            return "High-Protein Breakfast"
        elif meal_type == MealType.PRE_WORKOUT:
            return "Pre-Workout Fuel"
        elif meal_type == MealType.POST_WORKOUT:
            return "Post-Workout Recovery"
        elif meal_type == MealType.LUNCH:
            protein_name = next((c.food.name for c in components if c.food.food_group == "protein"), "Balanced")
            return f"{protein_name} Bowl"
        elif meal_type == MealType.DINNER:
            protein_name = next((c.food.name for c in components if c.food.food_group == "protein"), "Balanced")
            return f"{protein_name} with Sides"
        else:
            return "Snack"

    def _generate_prep_notes(
        self, components: List[MealComponent], meal_type: MealType
    ) -> str:
        """Generate preparation instructions"""
        food_names = [c.food.name for c in components]

        if meal_type == MealType.BREAKFAST:
            return f"Prepare: {', '.join(food_names)}. Can be prepped night before."
        elif meal_type in [MealType.PRE_WORKOUT, MealType.POST_WORKOUT]:
            return f"Quick meal: {', '.join(food_names)}. Consume 60-90 min before/after training."
        else:
            return f"Combine: {', '.join(food_names)}. Season to taste."

    def generate_14_day_meal_plan(
        self,
        targets: MacroTargets,
        training_days_per_week: int,
        dietary_preference: DietaryPreference = DietaryPreference.NONE,
        allergies: List[str] = None,
    ) -> List[DailyMealPlan]:
        """
        Generate complete 14-day meal plan.

        Args:
            targets: Daily macro targets
            training_days_per_week: Number of training days (e.g., 4, 5, 6)
            dietary_preference: Dietary restrictions
            allergies: Food allergies

        Returns:
            List of 14 DailyMealPlan objects
        """
        meal_plans = []

        # Determine which days are training days
        # Example: If 4 days/week, train Mon/Tue/Thu/Fri
        training_schedule = self._create_training_schedule(training_days_per_week)

        for day in range(1, 15):  # 14 days
            day_of_week = (day - 1) % 7
            is_training_day = day_of_week in training_schedule

            daily_plan = self.generate_daily_meal_plan(
                targets=targets,
                training_day=is_training_day,
                dietary_preference=dietary_preference,
                allergies=allergies,
                day_number=day,
            )
            meal_plans.append(daily_plan)

        return meal_plans

    def _create_training_schedule(self, sessions_per_week: int) -> List[int]:
        """
        Create weekly training schedule.

        Returns list of day indices (0=Monday, 6=Sunday) that are training days.
        """
        if sessions_per_week == 2:
            return [0, 3]  # Mon, Thu
        elif sessions_per_week == 3:
            return [0, 2, 4]  # Mon, Wed, Fri
        elif sessions_per_week == 4:
            return [0, 1, 3, 4]  # Mon, Tue, Thu, Fri
        elif sessions_per_week == 5:
            return [0, 1, 2, 4, 5]  # Mon-Wed, Fri-Sat
        elif sessions_per_week == 6:
            return [0, 1, 2, 3, 4, 5]  # Mon-Sat
        else:
            return [0, 2, 4]  # Default to 3x/week


def calculate_meal_plan_stats(meal_plans: List[DailyMealPlan]) -> Dict[str, any]:
    """Calculate statistics across entire meal plan"""
    total_days = len(meal_plans)

    avg_calories = sum(mp.daily_totals["calories"] for mp in meal_plans) / total_days
    avg_protein = sum(mp.daily_totals["protein"] for mp in meal_plans) / total_days
    avg_carbs = sum(mp.daily_totals["carbs"] for mp in meal_plans) / total_days
    avg_fat = sum(mp.daily_totals["fat"] for mp in meal_plans) / total_days
    avg_fiber = sum(mp.daily_totals["fiber"] for mp in meal_plans) / total_days

    # Calculate adherence metrics
    avg_adherence = {
        "calories": sum(mp.adherence_to_targets["calories"] for mp in meal_plans) / total_days,
        "protein": sum(mp.adherence_to_targets["protein"] for mp in meal_plans) / total_days,
        "carbs": sum(mp.adherence_to_targets["carbs"] for mp in meal_plans) / total_days,
        "fat": sum(mp.adherence_to_targets["fat"] for mp in meal_plans) / total_days,
    }

    return {
        "total_days": total_days,
        "averages": {
            "calories": round(avg_calories, 1),
            "protein_g": round(avg_protein, 1),
            "carbs_g": round(avg_carbs, 1),
            "fat_g": round(avg_fat, 1),
            "fiber_g": round(avg_fiber, 1),
        },
        "adherence": {k: f"{v:+.1f}%" for k, v in avg_adherence.items()},
    }
