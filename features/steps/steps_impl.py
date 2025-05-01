import subprocess
import shlex
from behave import given, when, then

@given('un repositorio con packfile "fixtures/pack-corrupt.git"')
def step_given_repo(context):
    context.repo_path = "fixtures/pack-corrupt.git"

@when('ejecuto "guardian scan {repo}"')
def step_when_exec_scan(context, repo):
    cmd = f"python -m guardian.cli scan {repo}"
    context.result = subprocess.run(shlex.split(cmd), capture_output=True, text=True)

@then('el exit code es 2')
def step_then_exit_code(context):
    assert context.result.returncode == 2, f"Exit code fue {context.result.returncode}"

@then('la salida contiene "Invalid CRC at offset"')
def step_then_output_contains(context):
    assert "Invalid CRC at offset" in context.result.stdout
