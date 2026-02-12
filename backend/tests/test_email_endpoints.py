import requests
import json
import uuid

BASE_URL = "http://localhost:8010/pat"


def test_email_analytics():
    print("\n--- Testing Email Analytics ---")
    response = requests.get(f"{BASE_URL}/emails/analytics")
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        print(json.dumps(response.json(), indent=2))
    else:
        print(response.text)


def test_list_emails():
    print("\n--- Testing List Emails ---")
    response = requests.get(f"{BASE_URL}/emails?limit=5")
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"Found {len(data.get('emails', []))} emails")
        return data.get("emails", [])
    else:
        print(response.text)
        return []


def test_send_email():
    print("\n--- Testing Send Email (Apple Mail) ---")
    # This will actually open Mail and send if successful
    params = {
        "recipient": "erickson.adam.m@gmail.com",
        "subject": "PAT API Test Message",
        "body": "This is a test message from the PAT Core API automated tests.",
    }
    response = requests.post(f"{BASE_URL}/emails/send", params=params)
    print(f"Status: {response.status_code}")
    print(response.json())


def test_email_actions(email_id):
    print(f"\n--- Testing Email Actions for ID: {email_id} ---")

    # Mark as read
    print("Marking as read...")
    response = requests.post(f"{BASE_URL}/emails/{email_id}/read")
    print(f"Read Status: {response.status_code}")

    # Classify
    print("Classifying...")
    response = requests.post(f"{BASE_URL}/emails/{email_id}/classify")
    print(f"Classify Status: {response.status_code}")
    if response.status_code == 200:
        print(json.dumps(response.json(), indent=2))

    # Summarize
    print("Summarizing...")
    response = requests.post(f"{BASE_URL}/emails/{email_id}/summarize")
    print(f"Summarize Status: {response.status_code}")
    if response.status_code == 200:
        print(json.dumps(response.json(), indent=2))


if __name__ == "__main__":
    test_email_analytics()
    emails = test_list_emails()

    if emails:
        test_email_actions(emails[0]["id"])
    else:
        print("No emails found to test actions on.")

    # test_send_email() # Uncomment to actually send an email
