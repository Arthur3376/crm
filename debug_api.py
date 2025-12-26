#!/usr/bin/env python3
"""
Debug specific API issues
"""

import requests
import json

def debug_lead_creation():
    """Debug lead creation issue"""
    base_url = "https://leadsync-16.preview.emergentagent.com"
    
    # Login first
    login_response = requests.post(f"{base_url}/api/auth/login", json={
        "email": "admin@leadflow.com",
        "password": "admin123"
    })
    
    if login_response.status_code != 200:
        print(f"Login failed: {login_response.status_code} - {login_response.text}")
        return
    
    token = login_response.json()['token']
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }
    
    # Try to create lead
    lead_data = {
        "full_name": "Test Lead API",
        "email": "testlead@example.com",
        "phone": "+521234567890",
        "career_interest": "Ingeniería",
        "source": "manual",
        "source_detail": "API Test"
    }
    
    print("Attempting to create lead...")
    response = requests.post(f"{base_url}/api/leads", json=lead_data, headers=headers)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.text}")
    
    # Try to create webhook
    webhook_data = {
        "name": "Test Webhook",
        "url": "https://example.com/webhook",
        "events": ["lead.created"],
        "is_active": True
    }
    
    print("\nAttempting to create webhook...")
    response = requests.post(f"{base_url}/api/webhooks", json=webhook_data, headers=headers)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.text}")

if __name__ == "__main__":
    debug_lead_creation()