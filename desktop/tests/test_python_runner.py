import json
import os
from pathlib import Path
import subprocess
import sys


RUNNER = Path(__file__).resolve().parents[1] / 'python_runner.py'


def invoke(*arguments, cwd=None):
    return subprocess.run([sys.executable, str(RUNNER), *arguments], cwd=cwd,
                          capture_output=True, text=True, encoding='utf-8',
                          timeout=10, env={**os.environ, 'PYTHONIOENCODING': 'utf-8'})


def test_python_code_with_unicode_arguments():
    result = invoke('-c', 'import sys,json; print(json.dumps(sys.argv,ensure_ascii=False))', 'ação')
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout) == ['-c', 'ação']


def test_script_can_import_sibling(tmp_path):
    (tmp_path / 'helper.py').write_text('value = "SCRIPT_OK"', encoding='utf-8')
    script = tmp_path / 'run.py'
    script.write_text('from helper import value; print(value)', encoding='utf-8')
    result = invoke(str(script), cwd=tmp_path)
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == 'SCRIPT_OK'


def test_module_can_run_from_working_directory(tmp_path):
    (tmp_path / 'local_module.py').write_text('print("MODULE_OK")', encoding='utf-8')
    result = invoke('-m', 'local_module', cwd=tmp_path)
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == 'MODULE_OK'


def test_runner_propagates_failures():
    result = invoke('-c', 'raise SystemExit(7)')
    assert result.returncode == 7


def test_missing_code_is_an_error():
    assert invoke('-c').returncode != 0
