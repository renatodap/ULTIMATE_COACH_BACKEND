"""
Grocery List Generator

Converts meal plans into organized shopping lists with:
- Aggregated quantities across all meals
- Categorized by food group (produce, meat, dairy, etc.)
- Cost estimates per item and total
- Bulk buying recommendations
- Weekly vs biweekly shopping options
"""

from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from collections import defaultdict
from enum import Enum

from .meal_assembler import DailyMealPlan, MealComponent


class ShoppingCategory(str, Enum):
    """Grocery store categories for organization"""

    PRODUCE = "produce"  # Fresh fruits and vegetables
    MEAT_SEAFOOD = "meat_seafood"  # Proteins
    DAIRY = "dairy"  # Milk, cheese, yogurt, eggs
    GRAINS = "grains"  # Rice, pasta, bread, oats
    PANTRY = "pantry"  # Oils, nuts, spices
    FROZEN = "frozen"  # Frozen vegetables, meals


@dataclass
class GroceryItem:
    """Single item on grocery list"""

    food_name: str
    category: ShoppingCategory
    total_quantity: float  # Total grams needed
    serving_size_g: float  # Standard serving size
    servings_needed: float  # How many servings to buy
    unit: str  # Display unit (lb, kg, container, etc.)
    estimated_cost_usd: float
    cost_per_serving_usd: float
    notes: str = ""


@dataclass
class GroceryList:
    """Complete grocery list for meal plan period"""

    duration_days: int
    items_by_category: Dict[ShoppingCategory, List[GroceryItem]]
    total_items: int
    total_estimated_cost_usd: float
    cost_per_day_usd: float
    bulk_buying_opportunities: List[str]
    shopping_tips: List[str]


# Cost database (USD, typical grocery store prices as of 2024)
# In production, this could pull from real-time pricing APIs
FOOD_COSTS_USD = {
    # Proteins (per lb / 453g)
    "Chicken Breast (grilled)": {"cost_per_lb": 4.99, "bulk_available": True},
    "Salmon (baked)": {"cost_per_lb": 12.99, "bulk_available": False},
    "Lean Ground Beef (93/7)": {"cost_per_lb": 6.99, "bulk_available": True},
    "Tuna (canned in water)": {"cost_per_lb": 5.50, "bulk_available": True},
    "Eggs (whole)": {"cost_per_lb": 3.50, "bulk_available": True},
    "Tofu (extra firm)": {"cost_per_lb": 3.99, "bulk_available": False},
    # Dairy
    "Greek Yogurt (non-fat)": {"cost_per_lb": 4.50, "bulk_available": True},
    "Cottage Cheese (low-fat)": {"cost_per_lb": 3.99, "bulk_available": False},
    # Carbs
    "Brown Rice (cooked)": {"cost_per_lb": 1.99, "bulk_available": True},
    "Sweet Potato (baked)": {"cost_per_lb": 1.29, "bulk_available": False},
    "Oatmeal (cooked)": {"cost_per_lb": 1.50, "bulk_available": True},
    "Quinoa (cooked)": {"cost_per_lb": 4.99, "bulk_available": True},
    "Whole Wheat Pasta (cooked)": {"cost_per_lb": 1.99, "bulk_available": True},
    "Banana": {"cost_per_lb": 0.59, "bulk_available": False},
    # Vegetables
    "Broccoli (steamed)": {"cost_per_lb": 2.49, "bulk_available": False},
    "Spinach (raw)": {"cost_per_lb": 3.99, "bulk_available": False},
    "Bell Peppers (raw)": {"cost_per_lb": 2.99, "bulk_available": False},
    "Mixed Greens Salad": {"cost_per_lb": 4.99, "bulk_available": False},
    # Fats
    "Almonds": {"cost_per_lb": 9.99, "bulk_available": True},
    "Avocado": {"cost_per_lb": 1.99, "bulk_available": False},
    "Olive Oil": {"cost_per_lb": 12.99, "bulk_available": False},
    "Peanut Butter (natural)": {"cost_per_lb": 5.99, "bulk_available": True},
}

# Category mapping for grocery store organization
FOOD_TO_CATEGORY = {
    "Chicken Breast (grilled)": ShoppingCategory.MEAT_SEAFOOD,
    "Salmon (baked)": ShoppingCategory.MEAT_SEAFOOD,
    "Lean Ground Beef (93/7)": ShoppingCategory.MEAT_SEAFOOD,
    "Tuna (canned in water)": ShoppingCategory.PANTRY,
    "Eggs (whole)": ShoppingCategory.DAIRY,
    "Tofu (extra firm)": ShoppingCategory.PRODUCE,
    "Greek Yogurt (non-fat)": ShoppingCategory.DAIRY,
    "Cottage Cheese (low-fat)": ShoppingCategory.DAIRY,
    "Brown Rice (cooked)": ShoppingCategory.GRAINS,
    "Sweet Potato (baked)": ShoppingCategory.PRODUCE,
    "Oatmeal (cooked)": ShoppingCategory.GRAINS,
    "Quinoa (cooked)": ShoppingCategory.GRAINS,
    "Whole Wheat Pasta (cooked)": ShoppingCategory.GRAINS,
    "Banana": ShoppingCategory.PRODUCE,
    "Broccoli (steamed)": ShoppingCategory.PRODUCE,
    "Spinach (raw)": ShoppingCategory.PRODUCE,
    "Bell Peppers (raw)": ShoppingCategory.PRODUCE,
    "Mixed Greens Salad": ShoppingCategory.PRODUCE,
    "Almonds": ShoppingCategory.PANTRY,
    "Avocado": ShoppingCategory.PRODUCE,
    "Olive Oil": ShoppingCategory.PANTRY,
    "Peanut Butter (natural)": ShoppingCategory.PANTRY,
}


class GroceryListGenerator:
    """Generates organized shopping lists from meal plans"""

    def __init__(self):
        self.cost_db = FOOD_COSTS_USD
        self.category_map = FOOD_TO_CATEGORY

    def generate_grocery_list(
        self, meal_plans: List[DailyMealPlan], bulk_buying: bool = True
    ) -> GroceryList:
        """
        Generate complete grocery list from meal plans.

        Args:
            meal_plans: List of daily meal plans (typically 7 or 14 days)
            bulk_buying: Whether to suggest bulk buying for cost savings

        Returns:
            GroceryList with organized items and cost estimates
        """
        duration_days = len(meal_plans)

        # Step 1: Aggregate all food quantities
        food_quantities = self._aggregate_food_quantities(meal_plans)

        # Step 2: Convert to grocery items with costs
        grocery_items = self._create_grocery_items(food_quantities)

        # Step 3: Categorize items
        items_by_category = self._categorize_items(grocery_items)

        # Step 4: Calculate totals
        total_cost = sum(item.estimated_cost_usd for item in grocery_items)
        cost_per_day = total_cost / duration_days

        # Step 5: Generate bulk buying opportunities
        bulk_opportunities = (
            self._identify_bulk_opportunities(grocery_items) if bulk_buying else []
        )

        # Step 6: Generate shopping tips
        shopping_tips = self._generate_shopping_tips(
            grocery_items, duration_days, total_cost
        )

        return GroceryList(
            duration_days=duration_days,
            items_by_category=items_by_category,
            total_items=len(grocery_items),
            total_estimated_cost_usd=round(total_cost, 2),
            cost_per_day_usd=round(cost_per_day, 2),
            bulk_buying_opportunities=bulk_opportunities,
            shopping_tips=shopping_tips,
        )

    def _aggregate_food_quantities(
        self, meal_plans: List[DailyMealPlan]
    ) -> Dict[str, Tuple[float, float]]:
        """
        Aggregate food quantities across all meal plans.

        Returns:
            Dict[food_name, (total_grams, serving_size_g)]
        """
        food_totals = defaultdict(lambda: {"total_grams": 0.0, "serving_size_g": 0.0})

        for daily_plan in meal_plans:
            for meal in daily_plan.meals:
                for component in meal.components:
                    food_name = component.food.name
                    quantity_grams = component.servings * component.food.serving_size_g

                    food_totals[food_name]["total_grams"] += quantity_grams
                    # Use the most common serving size
                    if food_totals[food_name]["serving_size_g"] == 0:
                        food_totals[food_name]["serving_size_g"] = (
                            component.food.serving_size_g
                        )

        return {
            name: (data["total_grams"], data["serving_size_g"])
            for name, data in food_totals.items()
        }

    def _create_grocery_items(
        self, food_quantities: Dict[str, Tuple[float, float]]
    ) -> List[GroceryItem]:
        """Convert aggregated quantities to grocery items with costs"""
        grocery_items = []

        for food_name, (total_grams, serving_size_g) in food_quantities.items():
            # Get cost info
            cost_info = self.cost_db.get(
                food_name, {"cost_per_lb": 5.00, "bulk_available": False}
            )
            cost_per_lb = cost_info["cost_per_lb"]

            # Convert grams to pounds for cost calculation
            total_lbs = total_grams / 453.592

            # Calculate costs
            estimated_cost = total_lbs * cost_per_lb
            servings_needed = total_grams / serving_size_g
            cost_per_serving = estimated_cost / servings_needed if servings_needed > 0 else 0

            # Determine display unit
            unit, display_quantity = self._determine_display_unit(total_grams, food_name)

            # Get category
            category = self.category_map.get(food_name, ShoppingCategory.PANTRY)

            # Generate notes
            notes = self._generate_item_notes(
                food_name, total_lbs, cost_info["bulk_available"]
            )

            grocery_items.append(
                GroceryItem(
                    food_name=food_name,
                    category=category,
                    total_quantity=total_grams,
                    serving_size_g=serving_size_g,
                    servings_needed=servings_needed,
                    unit=unit,
                    estimated_cost_usd=round(estimated_cost, 2),
                    cost_per_serving_usd=round(cost_per_serving, 2),
                    notes=notes,
                )
            )

        return sorted(grocery_items, key=lambda x: x.estimated_cost_usd, reverse=True)

    def _determine_display_unit(self, total_grams: float, food_name: str) -> Tuple[str, float]:
        """Determine best display unit for shopping list"""
        # Convert to lbs
        total_lbs = total_grams / 453.592

        # Special cases
        if "egg" in food_name.lower():
            num_eggs = total_grams / 50  # ~50g per egg
            return ("eggs", round(num_eggs))
        elif "yogurt" in food_name.lower():
            containers = total_grams / 170  # 170g containers
            return ("containers", round(containers))
        elif "banana" in food_name.lower():
            bananas = total_grams / 118  # ~118g per banana
            return ("bananas", round(bananas))
        elif "avocado" in food_name.lower():
            avocados = total_grams / 150  # ~150g per avocado
            return ("avocados", round(avocados))
        elif "oil" in food_name.lower():
            oz = total_grams / 28.35
            return ("fl oz", round(oz))

        # Default to lbs for most items
        if total_lbs < 1:
            return ("oz", round(total_grams / 28.35, 1))
        else:
            return ("lbs", round(total_lbs, 1))

    def _generate_item_notes(
        self, food_name: str, total_lbs: float, bulk_available: bool
    ) -> str:
        """Generate helpful notes for grocery item"""
        notes = []

        if bulk_available and total_lbs > 3:
            notes.append("Consider buying in bulk to save 15-20%")

        if "fresh" in food_name.lower() or any(
            veg in food_name.lower() for veg in ["lettuce", "spinach", "berries"]
        ):
            notes.append("Buy fresh, use within 3-5 days")

        if "frozen" in food_name.lower():
            notes.append("Frozen - longer shelf life")

        return " | ".join(notes) if notes else ""

    def _categorize_items(
        self, grocery_items: List[GroceryItem]
    ) -> Dict[ShoppingCategory, List[GroceryItem]]:
        """Group items by shopping category"""
        categorized = defaultdict(list)

        for item in grocery_items:
            categorized[item.category].append(item)

        # Sort items within each category by name
        for category in categorized:
            categorized[category].sort(key=lambda x: x.food_name)

        return dict(categorized)

    def _identify_bulk_opportunities(
        self, grocery_items: List[GroceryItem]
    ) -> List[str]:
        """Identify items worth buying in bulk"""
        opportunities = []

        for item in grocery_items:
            cost_info = self.cost_db.get(item.food_name, {"bulk_available": False})

            if cost_info["bulk_available"] and item.estimated_cost_usd > 15:
                # High-cost item that's available in bulk
                potential_savings = item.estimated_cost_usd * 0.18  # 18% average bulk savings
                opportunities.append(
                    f"{item.food_name}: Save ~${potential_savings:.2f} by buying family/bulk size"
                )

        return opportunities

    def _generate_shopping_tips(
        self, grocery_items: List[GroceryItem], duration_days: int, total_cost: float
    ) -> List[str]:
        """Generate helpful shopping tips"""
        tips = []

        # Budget tip
        weekly_cost = (total_cost / duration_days) * 7
        tips.append(f"Budget: ~${weekly_cost:.2f}/week for meal plan adherence")

        # Shopping frequency
        if duration_days >= 14:
            tips.append(
                "Split into 2 weekly shops: Buy fresh produce weekly, pantry items biweekly"
            )
        else:
            tips.append("Single weekly shop - prioritize fresh items first in the week")

        # Cost optimization
        high_cost_items = [item for item in grocery_items if item.estimated_cost_usd > 20]
        if high_cost_items:
            tips.append(
                f"Highest cost items: {', '.join(i.food_name for i in high_cost_items[:3])}"
            )

        # Meal prep tip
        tips.append(
            "Meal prep suggestion: Cook grains and proteins in bulk on Sunday for the week"
        )

        # Seasonal produce
        tips.append(
            "Buy seasonal produce for better prices (farmers markets often 20-30% cheaper)"
        )

        return tips

    def export_to_text(self, grocery_list: GroceryList) -> str:
        """Export grocery list to readable text format"""
        lines = []
        lines.append("=" * 60)
        lines.append(f"GROCERY LIST - {grocery_list.duration_days} Day Meal Plan")
        lines.append("=" * 60)
        lines.append("")

        # Items by category
        category_names = {
            ShoppingCategory.PRODUCE: "PRODUCE (Fruits & Vegetables)",
            ShoppingCategory.MEAT_SEAFOOD: "MEAT & SEAFOOD",
            ShoppingCategory.DAIRY: "DAIRY & EGGS",
            ShoppingCategory.GRAINS: "GRAINS & BREADS",
            ShoppingCategory.PANTRY: "PANTRY ITEMS",
            ShoppingCategory.FROZEN: "FROZEN FOODS",
        }

        for category, items in grocery_list.items_by_category.items():
            lines.append(category_names.get(category, category.value.upper()))
            lines.append("-" * 60)

            for item in items:
                lines.append(
                    f"  [ ] {item.food_name} - {item.unit} (${item.estimated_cost_usd:.2f})"
                )
                if item.notes:
                    lines.append(f"      Note: {item.notes}")

            lines.append("")

        # Summary
        lines.append("=" * 60)
        lines.append("SUMMARY")
        lines.append("=" * 60)
        lines.append(f"Total Items: {grocery_list.total_items}")
        lines.append(f"Total Estimated Cost: ${grocery_list.total_estimated_cost_usd:.2f}")
        lines.append(
            f"Cost per Day: ${grocery_list.cost_per_day_usd:.2f}"
        )
        lines.append("")

        # Bulk opportunities
        if grocery_list.bulk_buying_opportunities:
            lines.append("BULK BUYING OPPORTUNITIES")
            lines.append("-" * 60)
            for opportunity in grocery_list.bulk_buying_opportunities:
                lines.append(f"  • {opportunity}")
            lines.append("")

        # Shopping tips
        if grocery_list.shopping_tips:
            lines.append("SHOPPING TIPS")
            lines.append("-" * 60)
            for tip in grocery_list.shopping_tips:
                lines.append(f"  • {tip}")
            lines.append("")

        return "\n".join(lines)

    def export_to_markdown(self, grocery_list: GroceryList) -> str:
        """Export grocery list to markdown format"""
        lines = []
        lines.append(f"# Grocery List - {grocery_list.duration_days} Day Meal Plan\n")

        # Items by category
        category_names = {
            ShoppingCategory.PRODUCE: "Produce (Fruits & Vegetables)",
            ShoppingCategory.MEAT_SEAFOOD: "Meat & Seafood",
            ShoppingCategory.DAIRY: "Dairy & Eggs",
            ShoppingCategory.GRAINS: "Grains & Breads",
            ShoppingCategory.PANTRY: "Pantry Items",
            ShoppingCategory.FROZEN: "Frozen Foods",
        }

        for category, items in grocery_list.items_by_category.items():
            lines.append(f"## {category_names.get(category, category.value.title())}\n")

            for item in items:
                lines.append(
                    f"- [ ] **{item.food_name}** - {item.unit} (${item.estimated_cost_usd:.2f})"
                )
                if item.notes:
                    lines.append(f"  - *{item.notes}*")

            lines.append("")

        # Summary
        lines.append("## Summary\n")
        lines.append(f"- **Total Items:** {grocery_list.total_items}")
        lines.append(
            f"- **Total Estimated Cost:** ${grocery_list.total_estimated_cost_usd:.2f}"
        )
        lines.append(f"- **Cost per Day:** ${grocery_list.cost_per_day_usd:.2f}\n")

        # Bulk opportunities
        if grocery_list.bulk_buying_opportunities:
            lines.append("## Bulk Buying Opportunities\n")
            for opportunity in grocery_list.bulk_buying_opportunities:
                lines.append(f"- {opportunity}")
            lines.append("")

        # Shopping tips
        if grocery_list.shopping_tips:
            lines.append("## Shopping Tips\n")
            for tip in grocery_list.shopping_tips:
                lines.append(f"- {tip}")
            lines.append("")

        return "\n".join(lines)
