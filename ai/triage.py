import os
from openai import OpenAI

def analyze_failure(log_file):
    """Analyze failure logs using OpenAI API."""
    with open(log_file, "r") as f:
        content = f.read()

    # Get OpenAI API key from environment
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return {
            "summary": "OpenAI API key not configured",
            "type": "configuration_error",
            "suggested_fix": "Set OPENAI_API_KEY environment variable"
        }

    try:
        client = OpenAI(api_key=api_key)

        prompt = f"""Analyze this build/deployment failure log and provide:
1. A brief summary of what went wrong
2. The type of error (dependency_error, config_error, runtime_error, etc.)
3. A suggested fix

Log content:
{content}

Respond in JSON format with keys: summary, type, suggested_fix"""

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a DevOps expert analyzing failure logs."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3
        )

        # Parse the response
        result = response.choices[0].message.content

        # Try to extract JSON if it's wrapped in markdown
        import json
        if "```json" in result:
            result = result.split("```json")[1].split("```")[0].strip()
        elif "```" in result:
            result = result.split("```")[1].split("```")[0].strip()

        return json.loads(result)

    except Exception as e:
        return {
            "summary": f"Error calling OpenAI API: {str(e)}",
            "type": "api_error",
            "suggested_fix": "Check your OpenAI API key and network connection"
        }
