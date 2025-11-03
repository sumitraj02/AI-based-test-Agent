import os
from langchain.agents import Tool, initialize_agent, AgentType
from langchain.chat_models import ChatOpenAI

# Import our tool functions
from agent_tools import plan_tool, generate_tool, run_tool, feedback_tool

# ─────────────────────────────────────────────────────────────────────────────
# 1) New function: safe_run_tests
#    This function runs the tests once, checks if they failed, and if so:
#    - gives feedback (the captured output),
#    - regenerates tests, and
#    - runs tests again (only once).
# ─────────────────────────────────────────────────────────────────────────────
def safe_run_tests(input_text: str) -> str:
    """
    Runs the tests once using run_tool. If there's a failure, it attempts
    one reflection pass by calling the feedback_tool and generate_tool, then
    runs again. This only happens once to avoid infinite loops.
    """
    # First run
    print("----- SafeRun: First Attempt -----")
    first_run_output = run_tool("Run tests")
    if "failed" not in first_run_output.lower():
        return "All tests passed on first attempt.\n\n" + first_run_output

    # If tests failed, do a single reflection cycle
    print("----- SafeRun: Tests Failed, Attempting Single Reflection -----")
    # Provide minimal feedback to the LLM, or more detailed. For example:
    feedback_prompt = (
        "Some tests failed. Here is the run output:\n\n"
        f"{first_run_output}\n\n"
        "Please fix these failures and regenerate the tests accordingly."
    )
    feedback_output = feedback_tool(feedback_prompt)

    # Attempt to regenerate
    generate_output = generate_tool("Regenerate tests after failures")

    # Second run
    print("----- SafeRun: Second Attempt After Regeneration -----")
    second_run_output = run_tool("Run tests again")
    if "failed" not in second_run_output.lower():
        return "Tests passed on second attempt after reflection.\n\n" + second_run_output
    else:
        return (
            "Tests still failed after one reflection attempt.\n\n"
            "First run output:\n" + first_run_output + "\n\n"
            "Feedback response:\n" + feedback_output + "\n\n"
            "Regeneration output:\n" + generate_output + "\n\n"
            "Second run output:\n" + second_run_output
        )


# ─────────────────────────────────────────────────────────────────────────────
# 2) Create a new Tool that wraps safe_run_tests
# ─────────────────────────────────────────────────────────────────────────────
safe_run_tool = Tool(
    name="SafeRun",
    func=safe_run_tests,
    description=(
        "Run the tests with a single reflection pass if they fail. "
        "Stops after one attempt to fix."
    ),
)

# -----------------------------------------------------------------------------
# Initialize the LLM
# -----------------------------------------------------------------------------
llm = ChatOpenAI(
    temperature=0.0,  # to reduce randomness
    openai_api_key=os.getenv("OPENROUTER_API_KEY"),
    openai_api_base="https://openrouter.ai/api/v1",
    model_name="anthropic/claude-2"  # Example model; adjust as needed
)

# -----------------------------------------------------------------------------
# Existing Tools
# -----------------------------------------------------------------------------
tools = [
    Tool(
        name="Plan",
        func=plan_tool,
        description="Generate a test plan using `api_tester.py plan`."
    ),
    Tool(
        name="Generate",
        func=generate_tool,
        description="Generate or update Python test code for the API using `api_tester.py generate`."
    ),
    Tool(
        name="Run",
        func=run_tool,
        description="Run pytest on the generated tests using `api_tester.py run`."
    ),
    Tool(
        name="Feedback",
        func=feedback_tool,
        description="Provide user feedback using `api_tester.py feedback <feedback>`."
    ),
    safe_run_tool  # <-- Our new 'SafeRun' tool
]

agent = initialize_agent(
    tools=tools,
    llm=llm,
    agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
    verbose=True
)

def chat_with_agent(user_input: str) -> str:
    return agent.run(user_input)

if __name__ == "__main__":
    print("AI Testing Agent is running. Type 'quit' or 'exit' to stop.")
    while True:
        user_input = input("\nUser: ")
        if user_input.lower() in ["quit", "exit"]:
            break
        
        response = chat_with_agent(user_input)
        print(f"\nAgent: {response}")
