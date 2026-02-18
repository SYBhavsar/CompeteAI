---
service: sentiment_analysis
default_model: gpt-3.5-turbo
default_provider: openai
temperature: 0.1
max_tokens: 10
---

# System
Analyze the sentiment of the following content. Respond with only one word: 'positive', 'negative', or 'neutral'.

# User
{content}
