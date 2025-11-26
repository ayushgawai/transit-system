"""
Test LLM Integration for Transit Ops Dashboard
Tests the Perplexity API connection and chat handler
"""

import sys
import os

# Add api to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'api'))

import yaml

# Load secrets
secrets_path = os.path.join(os.path.dirname(__file__), '..', 'secrets.yaml')
with open(secrets_path, 'r') as f:
    secrets = yaml.safe_load(f)

# Set environment variables
for key, value in secrets.items():
    if value:
        os.environ[key] = str(value)

import snowflake.connector
from llm.perplexity_client import PerplexityClient
from llm.chat_handler import ChatHandler

PERPLEXITY_API_KEY = "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"


def test_perplexity_client():
    """Test basic Perplexity API connectivity"""
    print("\n" + "="*60)
    print("TEST 1: Perplexity API Connection")
    print("="*60)
    
    client = PerplexityClient(api_key=PERPLEXITY_API_KEY)
    result = client.chat([
        {"role": "user", "content": "What is 2+2? Reply with just the number."}
    ], max_tokens=10)
    
    if result["success"]:
        print(f"✅ API Connected!")
        print(f"   Response: {result['content']}")
        return True
    else:
        print(f"❌ API Failed: {result.get('error')}")
        return False


def test_chat_handler_without_db():
    """Test chat handler without database connection"""
    print("\n" + "="*60)
    print("TEST 2: Chat Handler (No DB)")
    print("="*60)
    
    handler = ChatHandler(api_key=PERPLEXITY_API_KEY, snowflake_conn=None)
    
    # Test transit-related question
    result = handler.process_message("What is on-time performance in transit?")
    if result["success"]:
        print(f"✅ Transit question handled!")
        print(f"   Response (first 200 chars): {result['response'][:200]}...")
    else:
        print(f"❌ Failed: {result.get('response')}")
        return False
    
    # Test off-topic question
    result = handler.process_message("What's the weather like?")
    if "transit" in result["response"].lower():
        print(f"✅ Off-topic redirected!")
        print(f"   Response: {result['response'][:150]}...")
    else:
        print(f"⚠️ Off-topic not fully redirected")
    
    return True


def test_chat_handler_with_db():
    """Test chat handler with Snowflake connection"""
    print("\n" + "="*60)
    print("TEST 3: Chat Handler (With Snowflake)")
    print("="*60)
    
    try:
        conn = snowflake.connector.connect(
            account=os.getenv('SNOWFLAKE_ACCOUNT'),
            user=os.getenv('SNOWFLAKE_USER'),
            password=os.getenv('SNOWFLAKE_PASSWORD'),
            warehouse='HORNET_QUERY_WH',
            database='USER_DB_HORNET',
            role='TRAINING_ROLE'
        )
        print("✅ Snowflake connected!")
        
        handler = ChatHandler(api_key=PERPLEXITY_API_KEY, snowflake_conn=conn)
        
        # Test with real data question
        result = handler.process_message("Show me the on-time performance for each route")
        print(f"\n📊 Question: 'Show me the on-time performance for each route'")
        print(f"   Response (first 300 chars): {result['response'][:300]}...")
        
        if result.get("data"):
            print(f"   Data rows returned: {len(result['data'])}")
        
        if result.get("sql"):
            print(f"   SQL generated: {result['sql'][:100]}...")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_severity_indicators():
    """Test severity analysis in responses"""
    print("\n" + "="*60)
    print("TEST 4: Severity Indicators")
    print("="*60)
    
    handler = ChatHandler(api_key=PERPLEXITY_API_KEY, snowflake_conn=None)
    
    result = handler.process_message("A route has 95% on-time performance. Is that good?")
    response = result["response"]
    
    has_green = "🟢" in response
    has_yellow = "🟡" in response  
    has_red = "🔴" in response
    
    print(f"Response mentions 95% OTP analysis:")
    print(f"   Has 🟢 (good): {has_green}")
    print(f"   Has 🟡 (warning): {has_yellow}")
    print(f"   Has 🔴 (critical): {has_red}")
    print(f"\n   Full response: {response[:300]}...")
    
    return True


def main():
    print("\n" + "="*60)
    print("TRANSIT OPS DASHBOARD - LLM INTEGRATION TESTS")
    print("Developed by Ayush Gawai | SJSU ADS Capstone")
    print("="*60)
    
    tests = [
        ("Perplexity API Connection", test_perplexity_client),
        ("Chat Handler (No DB)", test_chat_handler_without_db),
        ("Chat Handler (With Snowflake)", test_chat_handler_with_db),
        ("Severity Indicators", test_severity_indicators),
    ]
    
    results = []
    for name, test_func in tests:
        try:
            passed = test_func()
            results.append((name, "PASSED" if passed else "FAILED"))
        except Exception as e:
            print(f"❌ Exception: {e}")
            results.append((name, "ERROR"))
    
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    for name, status in results:
        emoji = "✅" if status == "PASSED" else "❌"
        print(f"{emoji} {name}: {status}")
    
    passed = sum(1 for _, s in results if s == "PASSED")
    print(f"\n{passed}/{len(results)} tests passed")
    
    return all(s == "PASSED" for _, s in results)


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

