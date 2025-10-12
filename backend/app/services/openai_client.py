import os
from typing import Optional
from openai import OpenAI


class OpenAIClient:
    """OpenAI API client for content processing"""
    
    def __init__(self):
        self.client = OpenAI(
            api_key=os.getenv("OPENAI_API_KEY")
        )
    
    def summarize_content(self, content: str) -> Optional[str]:
        """Summarize content using OpenAI"""
        try:
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a competitive intelligence analyst. Summarize the following content in 2-3 sentences, focusing on key business insights."
                    },
                    {
                        "role": "user",
                        "content": content
                    }
                ],
                max_tokens=150,
                temperature=0.3
            )
            return response.choices[0].message.content
        except Exception:
            return None
    
    def extract_insights(self, content: str) -> Optional[str]:
        """Extract key insights from content"""
        try:
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a competitive intelligence analyst. Extract the most important business insights from the following content. Focus on strategic information, product updates, market positioning, or competitive advantages."
                    },
                    {
                        "role": "user",
                        "content": content
                    }
                ],
                max_tokens=200,
                temperature=0.3
            )
            return response.choices[0].message.content
        except Exception:
            return None
    
    def analyze_sentiment(self, content: str) -> Optional[str]:
        """Analyze sentiment of content"""
        try:
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {
                        "role": "system",
                        "content": "Analyze the sentiment of the following content. Respond with only one word: 'positive', 'negative', or 'neutral'."
                    },
                    {
                        "role": "user",
                        "content": content
                    }
                ],
                max_tokens=10,
                temperature=0.1
            )
            return response.choices[0].message.content.strip().lower()
        except Exception:
            return None