#!/usr/bin/env python3
"""
Test Mode - Triggers dummy events for overlay testing
"""
import requests
import time
import sys

def trigger_test_mode():
    url = "http://127.0.0.1:5001/test_mode"
    
    try:
        print("🧪 Triggering test mode...")
        response = requests.post(url)
        if response.status_code == 200:
            print("✅ Test mode triggered successfully!")
            print("📹 Check the surveillance feed for overlays")
        else:
            print(f"❌ Failed: {response.status_code}")
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to surveillance server.")
        print("   Make sure lan_surveillance.py is running on port 5001")
        print("   Run: python lan_surveillance.py")
        sys.exit(1)

def simulate_motion():
    url = "http://127.0.0.1:5001/api/status"
    
    print("\n🎯 Simulating motion detection...")
    try:
        response = requests.get(url)
        data = response.json()
        print(f"   Detection active: {data.get('detection_active', False)}")
    except:
        pass

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "motion":
        simulate_motion()
    else:
        trigger_test_mode()
