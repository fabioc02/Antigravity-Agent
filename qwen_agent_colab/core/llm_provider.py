import os
import json
import urllib.request

class NativeLLMProvider:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3.6-flash:generateContent?key={self.api_key}"

    def generate_content(self, messages: list, tools: list = None) -> dict:
        payload = {
            "contents": messages,
        }
        if tools:
            payload["tools"] = [{"function_declarations": tools}]
            
        req = urllib.request.Request(
            self.url,
            data=json.dumps(payload).encode('utf-8'),
            headers={'Content-Type': 'application/json'}
        )
        try:
            with urllib.request.urlopen(req) as f:
                return json.loads(f.read().decode('utf-8'))
        except Exception as e:
            if hasattr(e, 'read'):
                print("API ERROR:", e.read().decode('utf-8'))
            return {"error": str(e)}
