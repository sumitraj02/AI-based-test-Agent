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

Prerequisites:
  - pip install requests pytest
  - export OPENROUTER_API_KEY="YOUR_OPENROUTER_KEY"
  - (Optional) export TEST_API_URL="https://your-real-api-domain"

Usage:
  python api_tester.py plan
  python api_tester.py generate
  python api_tester.py run
  python api_tester.py feedback "Your feedback"

NOTE: To ensure code uses /api/... in your routes, we've modified the
generation prompt below so that the LLM returns tests calling /api/endpoint
instead of /endpoint.
"""

# -----------------------------------------------------------------------------
#  Utility function: call_openrouter
#  Sends a prompt to an LLM via OpenRouter and returns its response as a string.
# -----------------------------------------------------------------------------
def call_openrouter(prompt: str) -> str:
    """
    Sends the prompt to OpenRouter, using an API key from OPENROUTER_API_KEY.
    Returns the LLM's text completion, or an error message if something fails.
    """
    openrouter_key = os.getenv("OPENROUTER_API_KEY")
    if not openrouter_key:
        return (
            "ERROR: The environment variable OPENROUTER_API_KEY is not set.\n"
            "Please export OPENROUTER_API_KEY=<your_key> and try again."
        )

    # If you prefer a different model from OpenRouter, update this "model":
    endpoint = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {openrouter_key}",
        "X-Title": "LLM-based API Testing",
    }
    data = {
        "model": "openai/gpt-4o-mini",  # or "openai/gpt-4o-mini", etc.
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
        "temperature": 0.7,
    }

    try:
        response = requests.post(endpoint, headers=headers, json=data, timeout=60)
        if response.status_code == 200:
            result_json = response.json()
            if "choices" in result_json and result_json["choices"]:
                content = result_json["choices"][0]["message"]["content"]
                return content.strip()
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
#  Helper: Extract Python code from an LLM response
#  We look for the first triple-backtick code block. If none is found, use entire string.
# -----------------------------------------------------------------------------
def extract_code_from_response(llm_response: str) -> str:
    """
    Pulls out the first code block found in triple backticks.
    If no code block is found, returns the entire string.
    """
    pattern = r"```(?:python)?\s*(.*?)\s*```"
    match = re.search(pattern, llm_response, re.DOTALL)
    if match:
        return match.group(1).strip()
    return llm_response.strip()


# -----------------------------------------------------------------------------
#  Prompt text helpers
#  NOTE: We instruct the LLM to use /api/... paths for all endpoints.
# -----------------------------------------------------------------------------
PLAN_PROMPT = (
    "Generate a comprehensive test plan for a fictional RESTful API. "
    "It should include categories such as authorization tests, boundary tests, "
    "error handling tests, plus any additional relevant categories. Include at "
    "least a few example scenarios in each category."
)

GENERATION_PROMPT = (
    "Generate a Python test script using pytest to test a fictional RESTful API. "
    "Assume the API routes have a prefix of '/api'. For example, use '/api/endpoint', "
    "'/api/nonexistent', or '/api/secure-endpoint'. "
    "Use an environment variable named TEST_API_URL as the base URL. If it's not set, "
    "default to 'http://localhost:8000'. Return only valid Python code without extra commentary. "
    "In your code, do something like:\n"
    "BASE_URL = os.getenv('TEST_API_URL', 'http://localhost:8000')\n"
    "Then, for a boundary test: requests.get(f\"{BASE_URL}/api/endpoint?param=100\").\n"
)


# -----------------------------------------------------------------------------
#  Command: plan
# -----------------------------------------------------------------------------
def generate_plan():
    """Generate a test plan via LLM and print it out."""
    print("\n----- Fetching a Test Plan from the LLM -----\n")
    plan = call_openrouter(PLAN_PROMPT)
    print(plan)
    print("\n----- End of Test Plan -----\n")


# -----------------------------------------------------------------------------
#  Command: generate
# -----------------------------------------------------------------------------
def generate_test_code():
    """
    Requests code generation from the LLM, strips out extra text, and
    writes only the valid Python code to `generated_tests.py`.
    Ensures the code references /api/... routes by default.
    """
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
#  Command: run
# -----------------------------------------------------------------------------
def run_tests():
    """Runs the generated tests with pytest."""
    print("\n----- Running the generated tests with pytest -----\n")
    code = subprocess.call(["pytest", "generated_tests.py", "-v"])
    if code == 0:
        print("\nAll tests passed successfully!")
    else:
        print(f"\nSome tests failed with exit code {code}. See above for details.")


# -----------------------------------------------------------------------------
#  Command: feedback
# -----------------------------------------------------------------------------
def handle_feedback(user_feedback: str):
    """
    Takes user feedback, sends it to the LLM, and prints the LLM's response.
    Could be extended to parse the response and update generated test code automatically.
    """
    print("\n----- Processing feedback with LLM -----\n")

    prompt_text = (
        "We have some existing test code for an API under '/api/...'. "
        "The user provided feedback:\n\n"
        f"'{user_feedback}'\n\n"
        "Given this feedback, produce updated or new test code. "
        "Remember to keep using '/api/' in the routes and to return only Python code "
        "wrapped in triple backticks if you propose any code changes."
    )

    response = call_openrouter(prompt_text)
    print(response)
    print("\n----- End of Feedback Response -----\n")


# -----------------------------------------------------------------------------
#  Main CLI entry point
# -----------------------------------------------------------------------------
def main():
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python api_tester.py plan")
        print("  python api_tester.py generate")
        print("  python api_tester.py run")
        print('  python api_tester.py feedback "Your feedback text"')
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
            print('Please provide your feedback in quotes, e.g.:\n  python api_tester.py feedback "Add a boundary test."')
            sys.exit(1)
        user_feedback = " ".join(sys.argv[2:])
        handle_feedback(user_feedback)
    else:
        print(f"Unknown command: {command}")
        print("Valid commands: plan, generate, run, feedback")
        sys.exit(1)


if __name__ == "__main__":
    main()
