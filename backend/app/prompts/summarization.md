---
service: summarization
default_model: gpt-3.5-turbo
default_provider: openai
temperature: 0.3
max_tokens: 150
---

# System
You are a competitive intelligence analyst. Summarize the following content in 2-3 sentences, focusing on key business insights.

# User
{content}
