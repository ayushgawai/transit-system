"""
Test LLM chat functionality
"""
import requests
import json

BASE_URL = "http://localhost:8000"

def test_llm_question(question):
    """Test LLM with a question"""
    try:
        response = requests.post(
            f"{BASE_URL}/api/chat",
            json={"message": question},
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            return True, result.get('response', 'No response')
        else:
            return False, f"HTTP {response.status_code}: {response.text[:200]}"
    except Exception as e:
        return False, str(e)

def main():
    print("=" * 80)
    print("LLM CHAT FUNCTIONALITY TESTING")
    print("=" * 80)
    print()
    
    questions = [
        "Which routes have the highest delays?",
        "What's the on-time performance for each route?",
        "Which routes need attention?",
        "What's the average delay for BART?",
        "How many routes does VTA have?",
        "Show me route utilization",
        "What's the reliability score?",
    ]
    
    results = []
    for question in questions:
        print(f"Q: {question}")
        print("A: ", end="")
        success, response = test_llm_question(question)
        
        if success:
            # Check if response is varied (not the same generic message)
            if len(response) > 50 and "I checked the transit data" not in response[:100]:
                print(response[:200] + "..." if len(response) > 200 else response)
                print("✅ PASS (varied response)")
                results.append((question, True, "Varied response"))
            else:
                print(response)
                print("⚠️  WARNING (generic response)")
                results.append((question, False, "Generic response"))
        else:
            print(f"❌ FAIL: {response}")
            results.append((question, False, response))
        print()
    
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    passed = sum(1 for _, success, _ in results if success)
    total = len(results)
    print(f"Passed: {passed}/{total}")
    
    if passed < total:
        print("\nFailed questions:")
        for question, success, error in results:
            if not success:
                print(f"  ❌ {question}: {error}")
    
    return passed == total

if __name__ == "__main__":
    main()

