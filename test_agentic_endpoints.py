"""
Quick Test - Verify agentic endpoints are accessible
Run this to check if the integration is working
"""

import requests
import json

BASE_URL = "http://127.0.0.1:8000/agents"

def test_agentic_query():
    """Test the agentic query endpoint."""
    print("\n1. Testing /agentic/query/ endpoint...")
    
    try:
        response = requests.post(
            f"{BASE_URL}/agentic/query/",
            json={
                "query": "Calculate premium for 35 year old",
                "conversation_history": []
            }
        )
        
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"   ✅ Intent: {result['intent_classification']['intent']}")
            print(f"   ✅ Confidence: {result['intent_classification']['confidence']}")
            print(f"   ✅ Tasks: {len(result['tasks'])}")
            print(f"   ✅ Agents: {result['agentic_metadata']['agents_involved']}")
        else:
            print(f"   ❌ Error: {response.text}")
            
    except Exception as e:
        print(f"   ❌ Exception: {e}")


def test_agentic_stats():
    """Test the statistics endpoint."""
    print("\n2. Testing /agentic/stats/ endpoint...")
    
    try:
        response = requests.get(f"{BASE_URL}/agentic/stats/")
        
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            stats = result['statistics']
            print(f"   ✅ Classifications: {stats['classifier'].get('total_classifications', 0)}")
            print(f"   ✅ Learning evidence: {result.get('learning_evidence', {})}")
        else:
            print(f"   ❌ Error: {response.text}")
            
    except Exception as e:
        print(f"   ❌ Exception: {e}")


def test_compare_systems():
    """Test the system comparison endpoint."""
    print("\n3. Testing /agentic/compare/ endpoint...")
    
    try:
        response = requests.post(
            f"{BASE_URL}/agentic/compare/",
            json={
                "query": "Calculate premium and compare with ActivFit",
                "conversation_history": []
            }
        )
        
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            comparison = result['comparison']
            print(f"   ✅ Keyword-based intent: {comparison['keyword_based']['intent']}")
            print(f"   ✅ Agentic intent: {comparison['agentic']['intent']}")
            print(f"   ✅ Agentic confidence: {comparison['agentic']['confidence']}")
            print(f"   ✅ Advantages: {len(comparison['advantages_of_agentic'])} listed")
        else:
            print(f"   ❌ Error: {response.text}")
            
    except Exception as e:
        print(f"   ❌ Exception: {e}")


def test_evaluation():
    """Test the evaluation endpoint."""
    print("\n4. Testing /agentic/evaluate/ endpoint...")
    
    try:
        response = requests.post(f"{BASE_URL}/agentic/evaluate/")
        
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"   ✅ Overall status: {result['overall_status']}")
            print(f"   ✅ Certification evidence: {len(result['certification_evidence'])} requirements")
            
            # Show requirement statuses
            for req_name, req_data in result['certification_evidence'].items():
                print(f"      - {req_name}: {req_data['status']}")
        else:
            print(f"   ❌ Error: {response.text}")
            
    except Exception as e:
        print(f"   ❌ Exception: {e}")


if __name__ == "__main__":
    print("=" * 60)
    print("Testing Agentic System Endpoints")
    print("=" * 60)
    print("\nMake sure Django server is running:")
    print("  python backend/manage.py runserver")
    print()
    
    test_agentic_query()
    test_agentic_stats()
    test_compare_systems()
    test_evaluation()
    
    print("\n" + "=" * 60)
    print("Test Complete!")
    print("=" * 60)
