#!/usr/bin/env python3
"""
Test script to simulate the complete ML recommendation flow
From sensor anomaly to operator action
"""

import requests
import json
import time
import random
from datetime import datetime

# Configuration
IGNITION_WEBHOOK = "http://localhost:8088/system/webdev/databricks/webhooks/recommendations"
LAKEBASE_URL = "jdbc:postgresql://workspace.cloud.databricks.com/lakebase"

def simulate_ml_recommendation():
    """
    Simulate an ML recommendation being generated
    This would normally come from Databricks ML pipeline
    """

    # Generate test recommendation
    recommendation = {
        "recommendation_id": f"test_{int(time.time())}_{random.randint(1000, 9999)}",
        "equipment_id": random.choice(["CRUSHER_01", "HAUL_TRUCK_02", "CONVEYOR_03"]),
        "action_code": random.choice([
            "REDUCE_SPEED_60",
            "SCHEDULE_MAINTENANCE",
            "INCREASE_COOLING",
            "CHECK_VIBRATION"
        ]),
        "confidence": round(random.uniform(0.65, 0.95), 2),
        "urgency": random.randint(2, 5),
        "time_to_failure": round(random.uniform(2, 48), 1),
        "parts_list": ["BEARING_SKF_22220", "SEAL_45X65X10"] if random.random() > 0.5 else [],
        "severity": random.choice(["medium", "high", "critical"]),
        "timestamp": datetime.now().isoformat()
    }

    print(f"\n{'='*60}")
    print("📊 ML RECOMMENDATION GENERATED")
    print(f"{'='*60}")
    print(f"ID: {recommendation['recommendation_id']}")
    print(f"Equipment: {recommendation['equipment_id']}")
    print(f"Action: {recommendation['action_code']}")
    print(f"Confidence: {recommendation['confidence']:.0%}")
    print(f"Urgency: {recommendation['urgency']}/5")
    print(f"Time to Failure: {recommendation['time_to_failure']} hours")

    return recommendation

def send_webhook_to_ignition(recommendation):
    """
    Send webhook to Ignition WebDev module
    Simulates Databricks → Ignition notification
    """

    print(f"\n🚀 Sending webhook to Ignition...")
    print(f"   URL: {IGNITION_WEBHOOK}")

    try:
        response = requests.post(
            IGNITION_WEBHOOK,
            json=recommendation,
            headers={
                'Content-Type': 'application/json',
                'X-Source': 'ML-Pipeline-Test'
            },
            timeout=5
        )

        if response.status_code == 200:
            print(f"   ✅ Webhook delivered successfully")
            print(f"   Response: {response.json()}")
            return True
        else:
            print(f"   ❌ Webhook failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False

    except requests.exceptions.ConnectionError:
        print(f"   ❌ Cannot connect to Ignition - Is it running on port 8088?")
        return False
    except requests.exceptions.Timeout:
        print(f"   ⚠️ Webhook timeout - Ignition may be slow")
        return False
    except Exception as e:
        print(f"   ❌ Error: {str(e)}")
        return False

def test_complete_flow():
    """
    Test the complete flow from ML to operator screen
    """

    print("\n" + "="*60)
    print("🔄 TESTING COMPLETE ML RECOMMENDATION FLOW")
    print("="*60)

    # Track timing
    start_time = time.time()
    timestamps = {}

    # Step 1: Generate ML recommendation
    print("\n1️⃣ ML MODEL GENERATES RECOMMENDATION")
    timestamps['ml_generated'] = time.time()
    recommendation = simulate_ml_recommendation()

    # Step 2: Simulate write to Lakebase (normally done by Databricks)
    print("\n2️⃣ WRITING TO LAKEBASE")
    time.sleep(1)  # Simulate write time
    timestamps['lakebase_written'] = time.time()
    print(f"   ✅ Written to lakebase.agentic_hmi.ml_recommendations")

    # Step 3: Send webhook to Ignition
    print("\n3️⃣ WEBHOOK NOTIFICATION TO IGNITION")
    timestamps['webhook_sent'] = time.time()
    webhook_success = send_webhook_to_ignition(recommendation)
    timestamps['webhook_received'] = time.time()

    if webhook_success:
        # Step 4: Verify in Ignition
        print("\n4️⃣ VERIFYING IN IGNITION")
        print(f"   📱 Check Perspective dashboard at http://localhost:8088/perspective")
        print(f"   📊 Recommendation should appear in table")
        print(f"   🔔 Critical alerts show popup (urgency >= 4)")

        # Calculate latencies
        print("\n" + "="*60)
        print("⏱️ LATENCY BREAKDOWN")
        print("="*60)

        ml_to_lakebase = timestamps['lakebase_written'] - timestamps['ml_generated']
        lakebase_to_webhook = timestamps['webhook_sent'] - timestamps['lakebase_written']
        webhook_delivery = timestamps['webhook_received'] - timestamps['webhook_sent']
        total_time = timestamps['webhook_received'] - timestamps['ml_generated']

        print(f"ML → Lakebase:        {ml_to_lakebase:.2f} seconds")
        print(f"Lakebase → Webhook:   {lakebase_to_webhook:.2f} seconds")
        print(f"Webhook Delivery:     {webhook_delivery:.2f} seconds")
        print(f"{'─'*30}")
        print(f"TOTAL E2E:           {total_time:.2f} seconds")

        # Show expected operator actions
        print("\n" + "="*60)
        print("👤 OPERATOR ACTIONS AVAILABLE")
        print("="*60)
        print("1. APPROVE - Execute the recommended action")
        print("2. DEFER - Postpone decision (15min, 1hr, next shift)")
        print("3. REJECT - Decline with reason (feeds back to ML)")
        print("4. ASK AI - Get detailed explanation from Genie")

    else:
        print("\n❌ Flow test failed - Check Ignition connection")

def test_critical_alert():
    """
    Test critical alert that should trigger immediate popup
    """

    print("\n" + "="*60)
    print("🚨 TESTING CRITICAL ALERT")
    print("="*60)

    critical_recommendation = {
        "recommendation_id": f"critical_{int(time.time())}",
        "equipment_id": "CRUSHER_01",
        "action_code": "EMERGENCY_STOP",
        "confidence": 0.92,
        "urgency": 5,  # Critical
        "time_to_failure": 0.5,  # 30 minutes
        "parts_list": [],
        "severity": "critical",
        "timestamp": datetime.now().isoformat()
    }

    print(f"Sending CRITICAL recommendation (urgency=5)")
    send_webhook_to_ignition(critical_recommendation)
    print("\n⚠️ This should trigger:")
    print("   - Immediate popup in Perspective")
    print("   - Alert sound")
    print("   - Red flash on screen")

def test_batch_recommendations():
    """
    Test sending multiple recommendations rapidly
    """

    print("\n" + "="*60)
    print("📦 TESTING BATCH RECOMMENDATIONS")
    print("="*60)

    recommendations = []
    for i in range(5):
        rec = simulate_ml_recommendation()
        recommendations.append(rec)
        send_webhook_to_ignition(rec)
        time.sleep(0.5)  # Small delay between webhooks

    print(f"\n✅ Sent {len(recommendations)} recommendations")
    print("Check Perspective dashboard for all items")

def main():
    """
    Run all tests
    """

    print("""
╔════════════════════════════════════════════════════════════╗
║     ML RECOMMENDATION SYSTEM - END-TO-END TEST SUITE      ║
╚════════════════════════════════════════════════════════════╝
    """)

    # Check if Ignition is reachable
    print("Checking Ignition connection...")
    try:
        response = requests.get("http://localhost:8088/system/webdev/databricks/webhooks/test", timeout=2)
        if response.status_code == 200:
            print("✅ Ignition WebDev module is responding")
        else:
            print("⚠️ Ignition responding but webhook endpoint not found")
    except:
        print("❌ Cannot reach Ignition - Make sure it's running on port 8088")
        print("   Run: docker-compose up -d")
        return

    while True:
        print("\nSelect test to run:")
        print("1. Complete flow test (single recommendation)")
        print("2. Critical alert test")
        print("3. Batch recommendations test")
        print("4. Continuous simulation (every 30s)")
        print("0. Exit")

        choice = input("\nEnter choice: ")

        if choice == "1":
            test_complete_flow()
        elif choice == "2":
            test_critical_alert()
        elif choice == "3":
            test_batch_recommendations()
        elif choice == "4":
            print("\nStarting continuous simulation (Ctrl+C to stop)")
            try:
                while True:
                    test_complete_flow()
                    print("\n⏰ Waiting 30 seconds for next simulation...")
                    time.sleep(30)
            except KeyboardInterrupt:
                print("\nSimulation stopped")
        elif choice == "0":
            break
        else:
            print("Invalid choice")

    print("\n✨ Test suite complete")

if __name__ == "__main__":
    main()