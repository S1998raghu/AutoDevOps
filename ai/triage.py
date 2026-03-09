import json
import os


async def analyze_failure(log_content):
    """Analyze failure logs using Claude.

    Authentication modes:
    - CLI (local): Uses Claude Agent SDK — no API key needed, authenticates via Claude Code CLI.
    - Kubernetes (Docker): Requires ANTHROPIC_API_KEY env var — uses Anthropic API directly.
    """
    if isinstance(log_content, str) and log_content.endswith('.log'):
        with open(log_content, "r") as f:
            content = f.read()
    else:
        content = log_content

    prompt = f"""Analyze this build/deployment failure log and provide:
1. A brief summary of what went wrong
2. The type of error (dependency_error, config_error, runtime_error, etc.)
3. A suggested fix

Log content:
{content}

Respond in JSON format only with keys: summary, type, suggested_fix"""

    api_key = os.getenv("ANTHROPIC_API_KEY")

    if api_key:
        return _analyze_with_api(prompt, api_key)
    else:
        return await _analyze_with_sdk(prompt)


def _analyze_with_api(prompt, api_key):
    """Use Anthropic API directly — required when running inside Kubernetes."""
    import anthropic

    client = anthropic.Anthropic(api_key=api_key)
    try:
        response = client.messages.create(
            model="claude-opus-4-6",
            max_tokens=1024,
            system="You are a DevOps expert analyzing failure logs. Always respond with valid JSON only.",
            messages=[{"role": "user", "content": prompt}]
        )
        result_text = response.content[0].text
        result_text = _strip_markdown(result_text)
        return json.loads(result_text)
    except Exception as e:
        return {
            "summary": f"Error calling Anthropic API: {str(e)}",
            "type": "api_error",
            "suggested_fix": "Check that ANTHROPIC_API_KEY is set correctly in the Kubernetes deployment"
        }


async def _analyze_with_sdk(prompt):
    """Use Claude Agent SDK — works locally via Claude Code CLI auth (no API key needed)."""
    from claude_agent_sdk import query, ClaudeAgentOptions, ResultMessage

    try:
        result_text = None
        async for message in query(
            prompt=prompt,
            options=ClaudeAgentOptions(
                allowed_tools=[],
                system_prompt="You are a DevOps expert analyzing failure logs. Always respond with valid JSON only."
            )
        ):
            if isinstance(message, ResultMessage):
                result_text = message.result

        if not result_text:
            return {
                "summary": "No response from Claude",
                "type": "api_error",
                "suggested_fix": "Check that Claude Code CLI is authenticated (run: claude)"
            }

        result_text = _strip_markdown(result_text)
        return json.loads(result_text)

    except Exception as e:
        return {
            "summary": f"Error calling Claude Agent SDK: {str(e)}",
            "type": "api_error",
            "suggested_fix": "Ensure Claude Code CLI is installed and authenticated (run: claude)"
        }


def _strip_markdown(text):
    """Strip markdown code fences from JSON responses."""
    if "```json" in text:
        return text.split("```json")[1].split("```")[0].strip()
    elif "```" in text:
        return text.split("```")[1].split("```")[0].strip()
    return text.strip()
