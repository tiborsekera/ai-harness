import subprocess
import shlex
import json
import re
import sys
from typing import Optional, Literal
from pydantic import BaseModel, Field, ValidationError, field_validator

FORBIDDEN_SHELL_TOKENS = (
    '|',
    ';',
    '&',
    '$',
    '>',
    '<',
    '`',
    '\n',
    'sudo',
    'rm',
    'mv',
    'cp',
    'tee',
    'chmod',
    'chown',
    'wget',
    'curl',
    'nc',
    'netcat',
)

# 1. Define the strict Schema (The Contract with the LLM)
class LogSearchRequest(BaseModel):
    server: str = Field(..., description="Target server name")
    connection_type: Literal["teleport", "direct"] = Field(..., description="Connection method")
    target_path: str = Field(..., description="Full path to the remote log file")
    search_pattern: str = Field(..., description="Primary pattern to grep")
    filter_condition: Optional[str] = Field(None, description="Optional awk condition")

    # 2. Defense-in-Depth: Ban shell operators from the search strings
    @field_validator('search_pattern', 'filter_condition')
    def block_shell_metacharacters(cls, v):
        if v is None:
            return v

        for token in FORBIDDEN_SHELL_TOKENS:
            pattern = re.escape(token)
            if token.isalpha():
                pattern = rf"\b{pattern}\b"

            if re.search(pattern, v, flags=re.IGNORECASE):
                raise ValueError(f"Security Policy Violation: Forbidden shell token '{token}' found in input.")
        return v


def execute_remote_log_search(llm_json_output: str) -> str:
    """
    The tool exposed to the Agentic Workflow.
    Expects a JSON string matching the LogSearchRequest schema.
    """
    try:
        # Step A: Parse and validate the LLM's JSON against our Pydantic schema
        args_dict = json.loads(llm_json_output)
        request = LogSearchRequest(**args_dict)
    except (json.JSONDecodeError, ValidationError) as e:
        # Return validation errors back to the LLM so it can self-correct
        return f"System Error: Invalid tool arguments. You must provide valid JSON. Details:\n{str(e)}"

    # Step B: Securely quote all inputs to prevent escaping the remote shell context.
    # shlex.quote() wraps strings in single quotes and safely escapes existing quotes.
    safe_path = shlex.quote(request.target_path)
    safe_pattern = shlex.quote(request.search_pattern)
    
    # Step C: Hardcode the read-only remote pipeline structure.
    # The LLM cannot inject arbitrary commands because it only controls the variables.
    remote_pipeline = f"zstdcat {safe_path} | grep -iE {safe_pattern}"
    
    if request.filter_condition:
        safe_filter = shlex.quote(request.filter_condition)
        remote_pipeline += f" | awk {safe_filter}"

    # Step D: Construct the local subprocess command array.
    if request.connection_type == "teleport":
        cmd = ["tsh", "ssh", f"vt@{request.server}", remote_pipeline]
    else:
        cmd = ["ssh", f"root@{request.server}", remote_pipeline]

    # Step E: Execute safely locally (shell=False is the default when passing a list)
    try:
        # Always enforce timeouts on LLM-driven actions to prevent hanging resources
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True,
            timeout=60 
         )
        return result.stdout

    except subprocess.TimeoutExpired:
        return "System Error: Remote execution timed out after 60 seconds."
    except subprocess.CalledProcessError as e:
        # Return standard error to the LLM so it knows if a file was missing, etc.
        return f"Command Failed. Exit Code: {e.returncode}\nError Log: {e.stderr}"
    except Exception as e:
        return f"System Error during orchestration: {str(e)}"

# Make the file executable via command line for the generic 'execute' tool
if __name__ == "__main__":
    if len(sys.argv) > 1:
        # Pass the first command-line argument (the JSON string) to the function
        print(execute_remote_log_search(sys.argv[1]))
    else:
        print("System Error: Missing JSON payload argument. Usage: python execute_remote_log_search.py '<json_payload>'")
