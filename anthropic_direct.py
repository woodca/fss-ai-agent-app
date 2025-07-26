import requests
import json

class AnthropicDirect:
    """Direct API calls to Anthropic without SDK to avoid proxy issues"""
    
    def __init__(self, api_key):
        self.api_key = api_key
        self.base_url = "https://api.anthropic.com/v1/messages"
        self.headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json"
        }
    
    def create_message(self, model, max_tokens, temperature, system, messages):
        """Create a message using direct API call"""
        data = {
            "model": model,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "system": system,
            "messages": messages
        }
        
        try:
            response = requests.post(
                self.base_url,
                headers=self.headers,
                json=data,
                timeout=30
            )
            response.raise_for_status()
            
            # Return in same format as SDK
            result = response.json()
            # Wrap content to match SDK response format
            class Content:
                def __init__(self, text):
                    self.text = text
            
            class Response:
                def __init__(self, content_text):
                    self.content = [Content(content_text)]
            
            return Response(result['content'][0]['text'])
            
        except Exception as e:
            print(f"Direct API error: {e}")
            raise