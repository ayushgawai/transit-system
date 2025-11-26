"""
Perplexity API Client
Handles communication with Perplexity LLM API
"""

import os
import requests
from typing import List, Dict, Optional

class PerplexityClient:
    """Client for Perplexity API"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("PERPLEXITY_API_KEY")
        if not self.api_key:
            raise ValueError("PERPLEXITY_API_KEY not provided")
        
        self.base_url = "https://api.perplexity.ai/chat/completions"
        self.model = "sonar"  # Perplexity's main model
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
    
    def chat(
        self, 
        messages: List[Dict[str, str]], 
        max_tokens: int = 500,
        temperature: float = 0.2
    ) -> Dict:
        """
        Send a chat request to Perplexity API
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            max_tokens: Maximum tokens in response
            temperature: Response randomness (0=focused, 1=creative)
        
        Returns:
            Dict with 'content' (response text) and 'success' (bool)
        """
        try:
            payload = {
                "model": self.model,
                "messages": messages,
                "max_tokens": max_tokens,
                "temperature": temperature
            }
            
            response = requests.post(
                self.base_url,
                headers=self.headers,
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                content = data["choices"][0]["message"]["content"]
                return {
                    "success": True,
                    "content": content,
                    "model": data.get("model", self.model)
                }
            else:
                return {
                    "success": False,
                    "content": f"API Error: {response.status_code}",
                    "error": response.text
                }
                
        except requests.exceptions.Timeout:
            return {
                "success": False,
                "content": "Request timed out. Please try again.",
                "error": "timeout"
            }
        except Exception as e:
            return {
                "success": False,
                "content": f"An error occurred: {str(e)}",
                "error": str(e)
            }
    
    def is_available(self) -> bool:
        """Check if the API is reachable"""
        try:
            result = self.chat(
                messages=[{"role": "user", "content": "ping"}],
                max_tokens=5
            )
            return result["success"]
        except:
            return False

