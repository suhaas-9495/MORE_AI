import subprocess
import tempfile
import os
import re


def extract_code_block(text: str) -> str:
    """Pulls the first python code block out of an LLM response."""
    match = re.search(r"```python\n(.*?)```", text, re.DOTALL)
    if match:
        return match.group(1).strip()
    match = re.search(r"```\n(.*?)```", text, re.DOTALL)
    return match.group(1).strip() if match else text.strip()


def run_generated_tests(code: str, test_code: str) -> dict:
    """
    Writes generated code + tests to temp files and actually runs pytest.
    This is real execution, not just LLM-judged — gives ground truth pass/fail.
    Returns: {"passed": bool, "output": str, "exit_code": int}
    """
    clean_code = extract_code_block(code)
    clean_tests = extract_code_block(test_code)

    with tempfile.TemporaryDirectory() as tmpdir:
        code_path = os.path.join(tmpdir, "solution.py")
        test_path = os.path.join(tmpdir, "test_solution.py")

        with open(code_path, "w", encoding="utf-8") as f:
            f.write(clean_code)

        # ensure test file can import the solution module
        test_content = f"import sys\nsys.path.insert(0, r'{tmpdir}')\nfrom solution import *\n\n{clean_tests}"
        with open(test_path, "w", encoding="utf-8") as f:
            f.write(test_content)

        try:
            result = subprocess.run(
                ["pytest", test_path, "-v", "--tb=short"],
                capture_output=True,
                text=True,
                timeout=30,          # prevent infinite loops / hangs — reliability requirement
                cwd=tmpdir,
            )
            return {
                "passed": result.returncode == 0,
                "output": result.stdout[-2000:] + result.stderr[-500:],
                "exit_code": result.returncode,
            }
        except subprocess.TimeoutExpired:
            return {
                "passed": False,
                "output": "Test execution timed out after 30s — possible infinite loop in generated code.",
                "exit_code": -1,
            }
        except Exception as e:
            return {"passed": False, "output": f"Test runner error: {str(e)}", "exit_code": -2}