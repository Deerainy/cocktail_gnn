import requests
import json

BASE_URL = "http://127.0.0.1:8000"

def test_api():
    print("Testing API endpoints...")
    
    # Test 1: Get all recipes
    print("\n1. Testing GET /api/recipes")
    try:
        response = requests.get(f"{BASE_URL}/api/recipes")
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Found {len(data['data'])} recipes")
            if data['data']:
                first_recipe_id = data['data'][0]['recipe_id']
                print(f"First recipe ID: {first_recipe_id}")
                
                # Test 2: Get combo adjust overview
                print(f"\n2. Testing GET /api/recipes/{first_recipe_id}/combo-adjust/overview")
                response = requests.get(f"{BASE_URL}/api/recipes/{first_recipe_id}/combo-adjust/overview")
                print(f"Status: {response.status_code}")
                if response.status_code == 200:
                    data = response.json()
                    print(f"Overview data keys: {data['data'].keys()}")
                    print(f"Total plans: {data['data']['total_plans']}")
                    print(f"Accepted plans: {data['data']['accepted_plans']}")
                    
                    # Test 3: Get combo adjust plans
                    print(f"\n3. Testing GET /api/recipes/{first_recipe_id}/combo-adjust/plans")
                    response = requests.get(f"{BASE_URL}/api/recipes/{first_recipe_id}/combo-adjust/plans")
                    print(f"Status: {response.status_code}")
                    if response.status_code == 200:
                        data = response.json()
                        print(f"Found {len(data['data'])} plans")
                        if data['data']:
                            first_plan_id = data['data'][0]['plan_id']
                            print(f"First plan ID: {first_plan_id}")
                            
                            # Test 4: Get plan detail
                            print(f"\n4. Testing GET /api/combo-adjust/plans/{first_plan_id}")
                            response = requests.get(f"{BASE_URL}/api/combo-adjust/plans/{first_plan_id}")
                            print(f"Status: {response.status_code}")
                            if response.status_code == 200:
                                data = response.json()
                                print(f"Plan data keys: {data['data'].keys()}")
                                print(f"Judgement: {data['data']['judgement']}")
                                print(f"Stages: {data['data']['stages']}")
                                print(f"Steps count: {len(data['data']['steps'])}")
                else:
                    print(f"Error: {response.json()}")
        else:
            print(f"Error: {response.json()}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_api()