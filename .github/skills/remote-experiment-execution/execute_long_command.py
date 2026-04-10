from __future__ import annotations

from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path


def _load_shared_helper():
    helper_path = Path(__file__).with_name("execute_structured_command.py")
    module_spec = spec_from_file_location("execute_structured_command", helper_path)
    if module_spec is None or module_spec.loader is None:
        raise ImportError(f"Unable to load shared helper from {helper_path}")

    module = module_from_spec(module_spec)
    module_spec.loader.exec_module(module)
    return module


_SHARED_HELPER = _load_shared_helper()


def execute_long_command(llm_json_output: str) -> str:
    return _SHARED_HELPER.execute_structured_command(llm_json_output)


if __name__ == "__main__":
    raise SystemExit(_SHARED_HELPER.main())
