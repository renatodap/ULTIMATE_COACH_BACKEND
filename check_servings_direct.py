"""
Direct database check for servings.
"""

from app.services.supabase_service import supabase_service

print("Checking database for banana servings...")
print()

# Get all banana foods
foods_response = supabase_service.client.table("foods").select("id, name").ilike("name", "%banana%").execute()

print(f"Found {len(foods_response.data)} foods with 'banana' in name:")
for food in foods_response.data:
    print(f"- {food['name']} (ID: {food['id']})")
print()

if foods_response.data:
    banana_id = foods_response.data[0]['id']

    # Get servings for first banana
    servings_response = supabase_service.client.table("food_servings").select("*").eq("food_id", banana_id).execute()

    print(f"Servings for {foods_response.data[0]['name']}:")
    if servings_response.data:
        for serving in servings_response.data:
            print(f"- {serving['serving_size']} {serving['serving_unit']}", end="")
            if serving.get('serving_label'):
                print(f" ({serving['serving_label']})", end="")
            print(f" = {serving['grams_per_serving']}g")
    else:
        print("NO SERVINGS FOUND!")
        print()
        print("This means migration 007_seed_common_foods.sql has not been run.")
        print("Or the servings were deleted.")
    print()

    # Test the RPC function directly
    print("Testing RPC function directly...")
    rpc_response = supabase_service.client.rpc(
        "search_foods_safe",
        {
            "search_query": "banana",
            "result_limit": 5,
            "user_id_filter": None
        }
    ).execute()

    print(f"RPC Response type: {type(rpc_response.data)}")
    print(f"RPC Response keys: {rpc_response.data.keys() if isinstance(rpc_response.data, dict) else 'not a dict'}")

    if isinstance(rpc_response.data, dict) and "foods" in rpc_response.data:
        foods = rpc_response.data["foods"]
        print(f"RPC returned {len(foods)} foods")
        if foods:
            first_food = foods[0]
            print(f"First food: {first_food.get('name')}")
            print(f"First food servings: {len(first_food.get('servings', []))} servings")
            if first_food.get('servings'):
                for s in first_food['servings']:
                    print(f"  - {s.get('serving_size')} {s.get('serving_unit')} = {s.get('grams_per_serving')}g")
else:
    print("No banana found in database!")
    print("Migration 007_seed_common_foods.sql needs to be run.")
