from __future__ import annotations

import json
import re
import shlex
import subprocess
import sys
from dataclasses import dataclass
from typing import Any, Final


DEFAULT_TIMEOUT_SECONDS = 900
MAX_SETTLE_SECONDS = 600
APPROVED_TEST_HOSTS: Final[frozenset[str]] = frozenset({
    "j1-autotrader3",
    "j1-autotrader4",
})
REMOTE_AUTOTRADER_REPO: Final[str] = "/home/visotech/autotrader"
REMOTE_AUTOTRADER_CONTAINER: Final[str] = "autotrader"
AUTOTRADER_MONGO_CONFIG_PATH: Final[str] = "/home/visotech/myconfig/system.cfg"
CUSTOMER_PORTAL_AUTOMATION_PATH: Final[str] = (
    "/home/tis/repos/autotrader_ado_7/synthetic_orders/clean_spark_spread_order/scripts/"
    "customer_portal_automation.py"
)
BRANCH_NAME_PATTERN: Final[re.Pattern[str]] = re.compile(r"[A-Za-z0-9][A-Za-z0-9._/-]{0,255}")
SAFE_IDENTIFIER_PATTERN: Final[re.Pattern[str]] = re.compile(r"[A-Za-z0-9_.:-]+")
READ_ONLY_MONGOSH_PATTERN: Final[re.Pattern[str]] = re.compile(
    r"\b(getDBNames|connectionStatus|find|findOne|countDocuments|aggregate|distinct|stats|serverStatus)\b",
    re.IGNORECASE,
)
DANGEROUS_MONGOSH_PATTERN: Final[re.Pattern[str]] = re.compile(
    r"\b(insert|update|delete|remove|drop|create(?:User|Role)|grantRolesToUser|revokeRolesFromUser|"
    r"shutdownServer|renameCollection|setProfilingLevel)\b",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class ExecutionRequest:
    operation: str
    payload: dict[str, Any]
    timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS


def _parse_execution_request(llm_json_output: str) -> ExecutionRequest:
    try:
        args_dict: dict[str, Any] = json.loads(llm_json_output)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid tool arguments. Details:\n{exc}") from exc

    operation = args_dict.get("operation")
    if not isinstance(operation, str) or not operation.strip():
        raise ValueError("Invalid tool arguments. Details:\noperation must be a non-empty string")

    timeout_seconds = args_dict.get("timeout_seconds", DEFAULT_TIMEOUT_SECONDS)
    if not isinstance(timeout_seconds, int) or timeout_seconds <= 0 or timeout_seconds > DEFAULT_TIMEOUT_SECONDS:
        raise ValueError(
            f"Invalid tool arguments. Details:\ntimeout_seconds must be an integer between 1 and {DEFAULT_TIMEOUT_SECONDS}"
        )

    return ExecutionRequest(operation=operation, payload=args_dict, timeout_seconds=timeout_seconds)


def _require_string(payload: dict[str, Any], key: str) -> str:
    value = payload.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"Invalid tool arguments. Details:\n{key} must be a non-empty string")
    return value


def _require_string_list(payload: dict[str, Any], key: str) -> list[str]:
    value = payload.get(key)
    if not isinstance(value, list) or not value or not all(isinstance(item, str) and item for item in value):
        raise ValueError(f"Invalid tool arguments. Details:\n{key} must be a non-empty list of strings")
    return value


def _validate_target_server(target_server: str) -> str:
    if target_server not in APPROVED_TEST_HOSTS:
        approved_hosts = ", ".join(sorted(APPROVED_TEST_HOSTS))
        raise ValueError(
            "Invalid tool arguments. Details:\n"
            f"target_server must be one of the approved test hosts: {approved_hosts}"
        )
    return target_server


def _validate_branch_name(branch_name: str) -> str:
    if not BRANCH_NAME_PATTERN.fullmatch(branch_name) or ".." in branch_name or branch_name.endswith("/"):
        raise ValueError(
            "Invalid tool arguments. Details:\nbranch_name contains unsupported characters or path traversal"
        )
    return branch_name


def _run_subprocess(argv: list[str], *, timeout_seconds: int) -> str:
    try:
        result = subprocess.run(
            argv,
            shell=False,
            capture_output=True,
            text=True,
            check=True,
            timeout=timeout_seconds,
        )
        return f"SUCCESS:\n{result.stdout}"
    except subprocess.TimeoutExpired:
        return f"System Error: Execution timed out after {timeout_seconds} seconds."
    except subprocess.CalledProcessError as exc:
        return f"Command Failed. Exit Code: {exc.returncode}\nError Log: {exc.stderr}"
    except Exception as exc:
        return f"System Error: {exc}"


def _run_remote_shell(target_server: str, remote_command: str, *, timeout_seconds: int) -> str:
    return _run_subprocess(["ssh", f"root@{target_server}", remote_command], timeout_seconds=timeout_seconds)


def _handle_remote_git_deploy(request: ExecutionRequest) -> str:
    target_server = _validate_target_server(_require_string(request.payload, "target_server"))
    branch_name = _validate_branch_name(_require_string(request.payload, "branch_name"))
    origin_ref = f"origin/{branch_name}"
    remote_command = (
        f"cd {shlex.quote(REMOTE_AUTOTRADER_REPO)}"
        " && git stash"
        " && git fetch --all"
        f" && git checkout {shlex.quote(branch_name)}"
        f" && git reset --hard {shlex.quote(origin_ref)}"
        " && git stash pop"
    )
    return _run_remote_shell(target_server, remote_command, timeout_seconds=request.timeout_seconds)


def _handle_remote_docker_restart(request: ExecutionRequest) -> str:
    target_server = _validate_target_server(_require_string(request.payload, "target_server"))
    settle_seconds = request.payload.get("settle_seconds", 0)
    if not isinstance(settle_seconds, int) or settle_seconds < 0 or settle_seconds > MAX_SETTLE_SECONDS:
        raise ValueError(
            f"Invalid tool arguments. Details:\nsettle_seconds must be an integer between 0 and {MAX_SETTLE_SECONDS}"
        )

    remote_command = f"docker restart {shlex.quote(REMOTE_AUTOTRADER_CONTAINER)}"
    if settle_seconds:
        remote_command = f"{remote_command} && sleep {settle_seconds}"
    return _run_remote_shell(target_server, remote_command, timeout_seconds=request.timeout_seconds)


def _handle_run_customer_portal_automation(request: ExecutionRequest) -> str:
    return _run_subprocess([sys.executable, CUSTOMER_PORTAL_AUTOMATION_PATH], timeout_seconds=request.timeout_seconds)


def _validate_identifier(value: str, *, field_name: str) -> None:
    if not SAFE_IDENTIFIER_PATTERN.fullmatch(value):
        raise ValueError(f"Invalid tool arguments. Details:\n{field_name} contains unsupported characters")


def _validate_mongosh_eval(eval_script: str) -> None:
    if not eval_script.strip():
        raise ValueError("Invalid tool arguments. Details:\n--eval must be a non-empty string")
    if DANGEROUS_MONGOSH_PATTERN.search(eval_script):
        raise ValueError("Invalid tool arguments. Details:\nmongosh --eval contains write-oriented commands")
    if not READ_ONLY_MONGOSH_PATTERN.search(eval_script):
        raise ValueError(
            "Invalid tool arguments. Details:\nmongosh --eval must contain an approved read-only probe"
        )


def _validate_mongosh_exec(argv: list[str]) -> None:
    index = 0
    eval_value: str | None = None
    value_flags = {
        "--authenticationDatabase",
        "--host",
        "--password",
        "--port",
        "--username",
    }
    standalone_flags = {"--norc", "--quiet", "--tls"}
    database_name_seen = False

    while index < len(argv):
        token = argv[index]
        if token == "--eval":
            if eval_value is not None or index + 1 >= len(argv):
                raise ValueError("Invalid tool arguments. Details:\nmongosh --eval must appear exactly once with a value")
            eval_value = argv[index + 1]
            index += 2
            continue
        if token in value_flags:
            if index + 1 >= len(argv):
                raise ValueError(f"Invalid tool arguments. Details:\n{token} requires a value")
            index += 2
            continue
        if token in standalone_flags:
            index += 1
            continue
        if token.startswith("--"):
            raise ValueError(f"Invalid tool arguments. Details:\nUnsupported mongosh option: {token}")
        if database_name_seen:
            raise ValueError("Invalid tool arguments. Details:\nOnly one positional database name is allowed")
        database_name_seen = True
        index += 1

    if eval_value is None:
        raise ValueError("Invalid tool arguments. Details:\nmongosh --eval is required for read-only discovery")
    _validate_mongosh_eval(eval_value)


def _validate_remote_readonly_argv(argv: list[str]) -> None:
    command = argv[0]
    if command == "docker":
        if len(argv) < 2:
            raise ValueError("Invalid tool arguments. Details:\ndocker command requires a subcommand")

        subcommand = argv[1]
        if subcommand in {"inspect", "port", "ps"}:
            return
        if subcommand != "exec" or len(argv) < 5:
            raise ValueError("Invalid tool arguments. Details:\nUnsupported docker read-only command")

        container_name = argv[2]
        _validate_identifier(container_name, field_name="container name")
        exec_program = argv[3]
        exec_args = argv[4:]
        if exec_program == "mongod":
            if exec_args != ["--version"]:
                raise ValueError("Invalid tool arguments. Details:\nmongod exec is limited to --version")
            return
        if exec_program != "mongosh":
            raise ValueError("Invalid tool arguments. Details:\ndocker exec is limited to mongod or mongosh")
        _validate_mongosh_exec(exec_args)
        return

    if command == "sed":
        if argv != ["sed", "-n", "/^\\[autotrader_mongo\\]/,/^\\[/p", AUTOTRADER_MONGO_CONFIG_PATH]:
            raise ValueError("Invalid tool arguments. Details:\nsed access is limited to the autotrader_mongo config section")
        return

    raise ValueError("Invalid tool arguments. Details:\nremote_readonly_command only permits approved docker and sed probes")


def _handle_remote_readonly_command(request: ExecutionRequest) -> str:
    target_server = _validate_target_server(_require_string(request.payload, "target_server"))
    argv = _require_string_list(request.payload, "argv")
    _validate_remote_readonly_argv(argv)
    remote_command = shlex.join(argv)
    return _run_remote_shell(target_server, remote_command, timeout_seconds=request.timeout_seconds)


def _dispatch_request(request: ExecutionRequest) -> str:
    if request.operation == "remote_git_deploy":
        return _handle_remote_git_deploy(request)
    if request.operation == "remote_docker_restart":
        return _handle_remote_docker_restart(request)
    if request.operation == "run_customer_portal_automation":
        return _handle_run_customer_portal_automation(request)
    if request.operation == "remote_readonly_command":
        return _handle_remote_readonly_command(request)
    raise ValueError(
        "Invalid tool arguments. Details:\n"
        "operation must be one of remote_git_deploy, remote_docker_restart, run_customer_portal_automation, "
        "or remote_readonly_command"
    )


def execute_structured_command(llm_json_output: str) -> str:
    try:
        request = _parse_execution_request(llm_json_output)
        return _dispatch_request(request)
    except ValueError as exc:
        return f"System Error: {exc}"


def main(argv: list[str] | None = None) -> int:
    args = sys.argv if argv is None else argv
    if len(args) > 1:
        print(execute_structured_command(args[1]))
    else:
        print("System Error: Missing JSON payload argument.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
