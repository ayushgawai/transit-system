"""
LLM API Test Script
Tests Perplexity API connectivity before implementation
"""

import time
import requests
import json

# API Keys
PERPLEXITY_API_KEY = "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"

def test_perplexity():
    """Test Perplexity API connection"""
    print("\n" + "="*60)
    print("🧪 TESTING PERPLEXITY API")
    print("="*60)
    
    try:
        url = "https://api.perplexity.ai/chat/completions"
        
        headers = {
            "Authorization": f"Bearer {PERPLEXITY_API_KEY}",
            "Content-Type": "application/json"
        }
        
        # Test 1: Simple math question
        print("\n📝 Test 1: Simple question (What is 2+2?)")
        start = time.time()
        
        payload = {
            "model": "sonar",
            "messages": [
                {"role": "user", "content": "What is 2+2? Reply with just the number."}
            ],
            "max_tokens": 10
        }
        
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        elapsed = time.time() - start
        
        if response.status_code == 200:
            data = response.json()
            answer = data["choices"][0]["message"]["content"].strip()
            model = data.get("model", "unknown")
            
            print(f"   ✅ Response: {answer}")
            print(f"   ⏱️  Time: {elapsed:.2f}s")
            print(f"   🎯 Model: {model}")
        else:
            print(f"   ❌ Error: {response.status_code}")
            print(f"   {response.text}")
            return False
        
        # Test 2: Transit-related question
        print("\n📝 Test 2: Transit context question")
        start = time.time()
        
        payload = {
            "model": "sonar",
            "messages": [
                {"role": "system", "content": "You are a transit analytics assistant. You help analyze transit data. Keep answers concise."},
                {"role": "user", "content": "If a bus route has 72% on-time performance and the target is 90%, is this good or bad? Keep answer to 1-2 sentences."}
            ],
            "max_tokens": 100
        }
        
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        elapsed = time.time() - start
        
        if response.status_code == 200:
            data = response.json()
            answer = data["choices"][0]["message"]["content"].strip()
            
            print(f"   ✅ Response: {answer}")
            print(f"   ⏱️  Time: {elapsed:.2f}s")
        else:
            print(f"   ❌ Error: {response.status_code}")
            return False
        
        # Test 3: SQL generation test
        print("\n📝 Test 3: SQL generation capability")
        start = time.time()
        
        payload = {
            "model": "sonar",
            "messages": [
                {"role": "system", "content": """You are a SQL expert for a transit database. 
Tables available:
- ANALYTICS.RELIABILITY_METRICS (ROUTE_ID, ON_TIME_PCT, RELIABILITY_SCORE, TOTAL_DEPARTURES)
- ANALYTICS.REVENUE_METRICS (ROUTE_ID, ESTIMATED_DAILY_REVENUE)
Generate only the SQL query, no explanation."""},
                {"role": "user", "content": "Show me the on-time percentage for all routes"}
            ],
            "max_tokens": 150
        }
        
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        elapsed = time.time() - start
        
        if response.status_code == 200:
            data = response.json()
            answer = data["choices"][0]["message"]["content"].strip()
            
            print(f"   ✅ Response:\n   {answer}")
            print(f"   ⏱️  Time: {elapsed:.2f}s")
        else:
            print(f"   ❌ Error: {response.status_code}")
            return False
        
        print("\n" + "="*60)
        print("✅ PERPLEXITY API TEST: PASSED")
        print("="*60)
        return True
        
    except requests.exceptions.Timeout:
        print("❌ Request timed out")
        return False
    except Exception as e:
        print(f"\n❌ PERPLEXITY API TEST: FAILED")
        print(f"   Error: {str(e)}")
        return False


def main():
    print("\n🚀 Transit System - LLM API Test")
    print("Testing Perplexity API connectivity...\n")
    
    # Test Perplexity
    perplexity_works = test_perplexity()
    
    # Summary
    print("\n" + "="*60)
    print("📊 TEST SUMMARY")
    print("="*60)
    print(f"   Perplexity API: {'✅ WORKING' if perplexity_works else '❌ FAILED'}")
    
    if perplexity_works:
        print("\n🎉 Ready to implement LLM integration!")
        print("   Using: Perplexity (llama-3.1-sonar-small-128k-online)")
        print("   Features: Fast, online search, good at SQL")
    else:
        print("\n⚠️  Need to fix API issues or try Gemini.")


if __name__ == "__main__":
    main()
