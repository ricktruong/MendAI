#!/usr/bin/env python3
"""
Quick Chat Feature Test
Tests the chat endpoint with a real patient ID
"""

import requests
import json
from datetime import datetime

# Configuration
ENGINE_URL = "http://localhost:8000"
PATIENT_ID = "a40640b3-b1a1-51ba-bf33-10eb05b37177"  # Known working patient ID

# Test message
TEST_MESSAGE = "What are the patient's main medical conditions?"

def test_chat():
    print("=" * 60)
    print("MendAI Chat Feature - Quick Test")
    print("=" * 60)
    print()
    
    # Prepare chat request
    chat_request = {
        "messages": [
            {
                "id": "test-1",
                "type": "user",
                "content": TEST_MESSAGE,
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }
        ],
        "patient_id": PATIENT_ID,
        "session_id": f"test-session-{int(datetime.now().timestamp())}"
    }
    
    print(f"📤 Sending request to: {ENGINE_URL}/api/v0/chat")
    print(f"👤 Patient ID: {PATIENT_ID}")
    print(f"💬 Message: {TEST_MESSAGE}")
    print()
    
    try:
        # Send chat request
        response = requests.post(
            f"{ENGINE_URL}/api/v0/chat",
            json=chat_request,
            timeout=60
        )
        
        print(f"📥 Response Status: {response.status_code}")
        print()
        
        if response.status_code == 200:
            data = response.json()
            
            print("✅ SUCCESS!")
            print()
            print(f"🆔 Session ID: {data.get('session_id', 'N/A')}")
            print(f"📊 Total Messages: {len(data.get('messages', []))}")
            print()
            
            # Show the AI response
            messages = data.get('messages', [])
            if len(messages) >= 2:
                ai_message = messages[-1]
                print("🤖 AI Response:")
                print("-" * 60)
                print(ai_message.get('content', 'No content'))
                print("-" * 60)
            
            return True
        else:
            print(f"❌ FAILED!")
            print(f"Status Code: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ ERROR: Cannot connect to engine service")
        print("Make sure the service is running: http://localhost:8000")
        return False
    except requests.exceptions.Timeout:
        print("⏰ ERROR: Request timed out")
        print("The AI service might be taking too long to respond")
        return False
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        return False

if __name__ == "__main__":
    success = test_chat()
    print()
    print("=" * 60)
    if success:
        print("✅ Test completed successfully!")
        print()
        print("Next steps:")
        print("  1. Open browser: http://localhost:5173")
        print("  2. Navigate to Patient List")
        print("  3. Select a patient")
        print("  4. Go to Chat tab")
        print("  5. Start chatting!")
    else:
        print("❌ Test failed. Please check the error messages above.")
        print()
        print("Debugging tips:")
        print("  • Check if all services are running")
        print("  • Review logs: tail -f /tmp/engine.log")
        print("  • Test endpoints individually with curl")
    print("=" * 60)
