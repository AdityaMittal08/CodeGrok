import os
from groq import Groq

client = Groq(api_key=os.environ["GROQ_API_KEY"])
MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-20b")

def explain_match(query: str, code_text: str, function_name: str, similarity: float) -> str:
    prompt = f"""A user searched a codebase with this natural language query:
"{query}"

The search engine returned this function as a match (similarity score: {similarity:.2f}):

Function name: {function_name}
Code:
{code_text}

Explain this code thoroughly so a developer can understand how to use and reason about it. Cover:
It should explain that why this code matches the search and what the code does and contribute. Make sure to keep it in within 5 sentences. Do not use bold letters or explanation in points. Give explanation in sentences using '->'.
Use only the code and metadata above as evidence. Do not invent callers, types, or behavior that are not shown. Refer to the function by name and use plain language suitable for someone learning this code."""

    response = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,
    )
    return response.choices[0].message.content.strip()