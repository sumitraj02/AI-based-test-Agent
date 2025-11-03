#!/usr/bin/env python3

import os
import sys
import requests
import subprocess
import re

"""
Open Source LLM-Powered API Testing Agent

This script uses OpenRouter (https://openrouter.ai/) to dynamically:
  1. Generate a Test Plan (plan command)
  2. Generate Python test code (generate command)
  3. Accept and process user feedback (feedback command)
  4. Run generated tests using pytest (run command)

Instructions:
  python api_tester.py plan
  python api_tester.py generate
  python api_tester.py run
  python api_tester.py feedback "Your feedback"

Requires:
  - pip install requests pytest
  - export OPENROUTER_API_KEY="YOUR_OPENROUTER_KEY"
  - (Optional) export TEST_API_URL="https://your-real-api"
"""

# -----------------------------------------------------------------------------
#  call_openrouter: Sends a prompt to an LLM via OpenRouter
# -----------------------------------------------------------------------------
def call_openrouter(prompt: str) -> str:
    openrouter_key = os.getenv("OPENROUTER_API_KEY")
    if not openrouter_key:
        return (
            "ERROR: The environment variable OPENROUTER_API_KEY is not set.\n"
            "Please export OPENROUTER_API_KEY=<your_key> and try again."
        )

    endpoint = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {openrouter_key}",
        "X-Title": "LLM-based API Testing",
    }
    data = {
        "model": "openai/gpt-4o-mini",  # Adjust if needed (anthropic/claude-3.5, etc.)
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are an AI that generates or updates an API test plan or code "
                    "based on user instructions. Reply with well-structured text or code. "
                    "Do NOT include extra commentary outside code blocks."
                ),
            },
            {
                "role": "user",
                "content": prompt,
            },
        ],
        "stream": False,
        # TIP: Set temperature=0.0 for minimal randomness (repeatable outputs)
        "temperature": 0.0,
    }

    try:
        response = requests.post(endpoint, headers=headers, json=data, timeout=60)
        if response.status_code == 200:
            result_json = response.json()
            if "choices" in result_json and result_json["choices"]:
                return result_json["choices"][0]["message"]["content"].strip()
            else:
                return (
                    "ERROR: No 'choices' returned by the LLM. "
                    f"Response content:\n{result_json}"
                )
        else:
            return (
                f"ERROR: OpenRouter responded with status {response.status_code}:\n"
                f"{response.text}"
            )
    except requests.exceptions.RequestException as e:
        return f"ERROR: Request to OpenRouter failed: {e}"

# -----------------------------------------------------------------------------
#  extract_code_from_response
# -----------------------------------------------------------------------------
def extract_code_from_response(llm_response: str) -> str:
    """
    Pulls out the first code block in triple backticks.
    If no code block is found, returns the entire string.
    """
    pattern = r"```(?:python)?\s*(.*?)\s*```"
    match = re.search(pattern, llm_response, re.DOTALL)
    if match:
        return match.group(1).strip()
    return llm_response.strip()

# -----------------------------------------------------------------------------
#  Template for final test file
# -----------------------------------------------------------------------------
TEST_TEMPLATE = """
import os
import requests
import pytest

BASE_URL = os.getenv('TEST_API_URL', 'http://localhost:8000')

{test_functions}
"""

# -----------------------------------------------------------------------------
#  PROMPTS
# -----------------------------------------------------------------------------
PLAN_PROMPT = (
    "Generate a test plan for a fictional REST API with categories like "
    "authorization, boundary, and error handling. Include a few scenarios each."
)

# NOTE: Double braces around {{test_functions}} to avoid f-string substitution
GENERATION_PROMPT = f"""
Below is a skeleton of our test file using pytest. Fill in the 'test_functions'
placeholder with tests for the following real API behavior from main.py:

1) GET /api/endpoint?param=max => 200, JSON {{ "result": "success" }}
2) GET /api/endpoint?param=min => 200, JSON {{ "result": "success" }}
3) If param != 'max'/'min':
   - no Authorization header => 401
   - 'Bearer invalid-api-key' => 403
   - otherwise => 404
4) GET /api/nonexistent => 404
5) GET /api/error => 500

We want these exact tests:
- test_endpoint_with_max
- test_endpoint_with_min
- test_endpoint_no_auth
- test_endpoint_invalid_api_key
- test_endpoint_random_auth_key
- test_nonexistent_endpoint
- test_error_endpoint

Skeleton:
```python
{TEST_TEMPLATE}
```

Requirements:
1. Use '/api/' prefix for all routes.
2. Only return valid Python code, wrapped in triple backticks (no extra commentary).
3. Keep 'BASE_URL' from env or default http://localhost:8000.
4. Provide all tests in place of {{test_functions}}.
5. Each test asserts the correct status code (and JSON if needed).
6. The final output should be a complete Python file that can run under pytest.
"""

# -----------------------------------------------------------------------------
#  plan
# -----------------------------------------------------------------------------
def generate_plan():
    print("\n----- Fetching a Test Plan from the LLM -----\n")
    plan = call_openrouter(PLAN_PROMPT)
    print(plan)
    print("\n----- End of Test Plan -----\n")

# -----------------------------------------------------------------------------
#  generate
# -----------------------------------------------------------------------------
def generate_test_code():
    print("\n----- Requesting Test Code from the LLM -----\n")
    raw_response = call_openrouter(GENERATION_PROMPT)
    if raw_response.startswith("ERROR:"):
        print(raw_response)
        print("\nGeneration aborted.")
        return

    python_code = extract_code_from_response(raw_response)

    output_file = "generated_tests.py"
    try:
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(python_code)
        print(f"Successfully generated test code in '{output_file}'\n")
        print("----- You may now run the tests with: python api_tester.py run -----\n")
    except OSError as e:
        print(f"ERROR: Could not write to {output_file}: {e}")

# -----------------------------------------------------------------------------
#  run
# -----------------------------------------------------------------------------
def run_tests():
    print("\n----- Running the generated tests with pytest -----\n")
    code = subprocess.call(["pytest", "generated_tests.py", "-v"])
    if code == 0:
        print("\nAll tests passed successfully!")
    else:
        print(f"\nSome tests failed with exit code {code}. See above for details.")

# -----------------------------------------------------------------------------
#  feedback
# -----------------------------------------------------------------------------
def handle_feedback(user_feedback: str):
    print("\n----- Processing feedback with LLM -----\n")

    # You can reuse the skeleton if you want to keep consistent formatting
    prompt_text = f"""
We have the above logic for '/api/endpoint', '/api/nonexistent', and '/api/error'.
User feedback: '{user_feedback}'

Please update or expand the test code using the same approach. 
The skeleton is:
```python
{TEST_TEMPLATE}
```
Insert your changes in {{test_functions}}, produce valid Python code in triple backticks.
"""

    response = call_openrouter(prompt_text)
    print(response)
    print("\n----- End of Feedback Response -----\n")

# -----------------------------------------------------------------------------
#  Main
# -----------------------------------------------------------------------------
def main():
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python api_tester.py plan")
        print("  python api_tester.py generate")
        print("  python api_tester.py run")
        print('  python api_tester.py feedback "Your feedback"')
        sys.exit(1)

    command = sys.argv[1].lower()

    if command == "plan":
        generate_plan()
    elif command == "generate":
        generate_test_code()
    elif command == "run":
        run_tests()
    elif command == "feedback":
        if len(sys.argv) < 3:
            print('Please provide your feedback in quotes, for example:\n'
                  '  python api_tester.py feedback "Add a boundary test."')
            sys.exit(1)
        user_feedback = " ".join(sys.argv[2:])
        handle_feedback(user_feedback)
    else:
        print(f"Unknown command: {command}")
        print("Valid commands: plan, generate, run, feedback")
        sys.exit(1)

if __name__ == "__main__":
    main()