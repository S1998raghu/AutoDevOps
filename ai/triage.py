import json
from claude_agent_sdk import query, ClaudeAgentOptions, ResultMessage


async def analyze_failure(log_content):
    """Analyze failure logs using Claude Agent SDK (no API key required).

    Args:
        log_content: Can be either a file path (str ending with .log) or log content (str)
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

    result_text = None
    try:
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
                "suggested_fix": "Check that Claude Code CLI is authenticated"
            }

        if "```json" in result_text:
            result_text = result_text.split("```json")[1].split("```")[0].strip()
        elif "```" in result_text:
            result_text = result_text.split("```")[1].split("```")[0].strip()

        return json.loads(result_text)

    except Exception as e:
        return {
            "summary": f"Error calling Claude Agent SDK: {str(e)}",
            "type": "api_error",
            "suggested_fix": "Ensure Claude Code CLI is installed and authenticated"
        }
