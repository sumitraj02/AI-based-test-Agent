import subprocess

def plan_tool(input_text: str) -> str:
    """
    Calls `python api_tester.py plan` and returns the console output.
    """
    try:
        result = subprocess.check_output(["python", "api_tester.py", "plan"])
        return result.decode("utf-8")
    except subprocess.CalledProcessError as e:
        return f"Error running plan_tool: {str(e)}"


def generate_tool(input_text: str) -> str:
    """
    Calls `python api_tester.py generate` and returns the console output.
    """
    try:
        result = subprocess.check_output(["python", "api_tester.py", "generate"])
        return result.decode("utf-8")
    except subprocess.CalledProcessError as e:
        return f"Error running generate_tool: {str(e)}"


def run_tool(input_text: str) -> str:
    """
    Calls `python api_tester.py run` and returns the console output.
    """
    try:
        result = subprocess.check_output(["python", "api_tester.py", "run"])
        return result.decode("utf-8")
    except subprocess.CalledProcessError as e:
        return f"Error running run_tool: {str(e)}"


def feedback_tool(user_feedback: str) -> str:
    """
    Calls `python api_tester.py feedback "<user_feedback>"` and returns the console output.
    """
    try:
        result = subprocess.check_output(["python", "api_tester.py", "feedback", user_feedback])
        return result.decode("utf-8")
    except subprocess.CalledProcessError as e:
        return f"Error running feedback_tool: {str(e)}"
