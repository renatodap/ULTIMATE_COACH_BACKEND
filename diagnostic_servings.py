"""
Diagnostic script to check if servings data exists in database.

Run this to diagnose why frontend doesn't show serving button.
"""

import asyncio
from app.services.nutrition_service import nutrition_service
from uuid import uuid4

async def main():
    print("=" * 60)
    print("SERVINGS DIAGNOSTIC")
    print("=" * 60)
    print()

    # Search for banana
    print("1. Searching for 'banana'...")
    try:
        foods = await nutrition_service.search_foods(
            query="banana",
            limit=5,
            user_id=uuid4()  # Dummy user ID
        )

        print(f"   ✓ Found {len(foods)} results")
        print()

        if foods:
            for i, food in enumerate(foods, 1):
                print(f"   Result {i}:")
                print(f"   - ID: {food.id}")
                print(f"   - Name: {food.name}")
                print(f"   - Calories per 100g: {food.calories_per_100g}")
                print(f"   - Servings: {len(food.servings)} found")

                if food.servings:
                    for j, serving in enumerate(food.servings, 1):
                        print(f"      {j}. {serving.serving_size} {serving.serving_unit}", end="")
                        if serving.serving_label:
                            print(f" ({serving.serving_label})", end="")
                        print(f" = {serving.grams_per_serving}g")
                else:
                    print("      ⚠️ NO SERVINGS FOUND!")
                print()
        else:
            print("   ❌ No foods found for 'banana'")

    except Exception as e:
        print(f"   ❌ Error: {e}")
        import traceback
        traceback.print_exc()

    print()
    print("=" * 60)
    print("DIAGNOSIS COMPLETE")
    print("=" * 60)
    print()
    print("Expected results:")
    print("- Should find 'Banana, Raw' in results")
    print("- Should have 3 servings:")
    print("  1. 1 banana (medium) = 118g")
    print("  2. 1 oz = 28.35g")
    print("  3. 100 g = 100g")
    print()
    print("If servings are missing:")
    print("1. Check if migrations have been run (especially 007_seed_common_foods.sql)")
    print("2. Check Railway/database logs for RPC errors")
    print("3. Try running: SELECT * FROM food_servings WHERE food_id IN (SELECT id FROM foods WHERE name ILIKE '%banana%');")

if __name__ == "__main__":
    asyncio.run(main())
