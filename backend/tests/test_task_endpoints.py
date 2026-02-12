import requests
import json

BASE_URL = "http://localhost:8010/pat"


def test_task_analytics():
    print("\n--- Testing Task Analytics ---")
    response = requests.get(f"{BASE_URL}/tasks/analytics")
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        print(json.dumps(response.json(), indent=2))


def test_sync_tasks():
    print("\n--- Testing Task Sync (Apple Reminders) ---")
    response = requests.post(f"{BASE_URL}/tasks/sync?limit=5")
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        print(json.dumps(response.json(), indent=2))


def test_list_tasks():
    print("\n--- Testing List Tasks ---")
    response = requests.get(f"{BASE_URL}/tasks?limit=5")
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"Found {len(data.get('tasks', []))} tasks")
        return data.get("tasks", [])
    return []


if __name__ == "__main__":
    test_task_analytics()
    test_sync_tasks()
    tasks = test_list_tasks()
    test_task_analytics()  # See updated counts
