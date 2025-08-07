#!/usr/bin/env python3
"""
Test script for the chat endpoint
"""
import requests
import json
from datetime import datetime

def test_chat_endpoint():
    """Test the chat endpoint with a sample message"""
    
    # Sample chat request
    chat_request = {
        "messages": [
            {
                "id": "1",
                "type": "assistant",
                "content": "Hello! I'm MendAI, your AI healthcare assistant. How can I help you today?",
                "timestamp": datetime.now().isoformat(),
                "attachments": None,
                "analysis_results": None
            },
            {
                "id": "2",
                "type": "user",
                "content": "Can you analyze the patient's CT scan?",
                "timestamp": datetime.now().isoformat(),
                "attachments": [
                    {
                        "id": "file-1",
                        "type": "image",
                        "name": "CT_scan.jpg",
                        "url": None
                    }
                ],
                "analysis_results": None
            }
        ],
        "patient_id": "john_doe"
    }
    
    try:
        # Send request to the chat endpoint
        response = requests.post(
            "http://0.0.0.0:8000/v0/chat",
            headers={"Content-Type": "application/json"},
            data=json.dumps(chat_request)
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Response Headers: {response.headers}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Chat endpoint is working!")
            print(f"Response: {json.dumps(result, indent=2)}")
        else:
            print(f"❌ Error: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to the backend. Make sure the engine service is running on localhost:8000")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

if __name__ == "__main__":
    test_chat_endpoint() 