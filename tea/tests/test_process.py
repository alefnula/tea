import os
import re
import sys
import time
import pytest
from tea.process import (
    Process,
    ExecutableNotFound,
    execute,
    execute_no_demux,
    execute_and_report as er,
)


WRITER = """
import sys
import time

sys.{out}.write("foo")
sys.{out}.flush()
time.sleep(1)
sys.{out}.write("bar")
"""

WRITE_BOTH = """
import sys

sys.stdout.write("foo")
sys.stdout.flush()
sys.stderr.write("bar")
sys.stderr.flush()
"""

PRINT_VAR = """
import os

print(os.environ.get("{var}", ""))
"""


@pytest.fixture
def process():
    return Process(["sleep", "1"])


def test_start(process):
    assert not process.is_running
    process.start()
    assert process.is_running
    process.wait()
    assert not process.is_running


def test_kill(process):
    assert not process.is_running
    start = time.time()
    process.start()
    assert process.is_running
    process.kill()
    assert not process.is_running
    end = time.time()
    assert end - start < 2


def test_write():
    p = Process(
        [sys.executable, "-c", """a = input(); print('Said: ' + a)"""],
    )
    p.start()
    p.write("my hello text")
    p.wait()
    assert re.match(r"^Said: my hello text\s*$", p.read())
    assert re.match(r"^$", p.eread())


def test_read():
    p = Process([sys.executable, "-c", WRITER.format(out="stdout")])
    p.start()
    time.sleep(0.5)
    assert p.read() == "foo"
    assert p.eread() == ""
    p.wait()
    assert p.read() == "bar"
    assert p.eread() == ""


def test_eread():
    p = Process([sys.executable, "-c", WRITER.format(out="stderr")])
    p.start()
    time.sleep(0.5)
    assert p.read() == ""
    assert p.eread() == "foo"
    p.wait()
    assert p.read() == ""
    assert p.eread() == "bar"


def test_stdout(tmpdir):
    stdout = tmpdir.mkdir("__tests__").join("std.out")
    p = Process(
        [sys.executable, "-c", WRITER.format(out="stdout")],
        stdout=stdout.strpath,
    )
    p.start()
    p.wait()
    assert p.read() == "foobar"
    assert stdout.open("r", encoding="utf-8").read() == "foobar"


def test_stderr(tmpdir):
    stderr = tmpdir.mkdir("__tests__").join("std.err")
    p = Process(
        [sys.executable, "-c", WRITER.format(out="stderr")],
        stderr=stderr.strpath,
    )
    p.start()
    p.wait()
    assert p.eread() == "foobar"
    assert stderr.open("r", encoding="utf-8").read() == "foobar"


def test_environment():
    p = Process(
        [sys.executable, "-c", PRINT_VAR.format(var="MY_VAR")],
        env={"MY_VAR": "My value"},
    )
    p.start()
    p.wait()
    assert p.exit_code == 0
    assert re.match(r"^My value\s*$", p.read())
    assert re.match(r"^$", p.eread())


def test_override_environment():
    status, output, error = execute(
        [sys.executable, "-c", PRINT_VAR.format(var="PATH")],
        env={"PATH": "PATH"},
    )
    assert status == 0
    assert re.match(r"^PATH\s*$", output)
    assert re.match(r"^$", error)
    os.environ["FOO"] = "foo"
    status, output, error = execute(
        [sys.executable, "-c", PRINT_VAR.format(var="FOO")]
    )
    assert status == 0
    assert re.match(r"^foo\s*$", output)
    assert re.match(r"^$", error)
    status, output, error = execute(
        [sys.executable, "-c", PRINT_VAR.format(var="FOO")], env={"FOO": "bar"}
    )
    assert status == 0
    assert re.match(r"^bar\s*$", output)
    assert re.match(r"^$", error)


def test_working_dir():
    working_dir = sys.exec_prefix.strip(os.pathsep)
    p = Process(
        [sys.executable, "-c", """import os; print(os.getcwd())"""],
        working_dir=working_dir,
    )
    p.start()
    p.wait()
    assert p.read().strip() == working_dir


def test_execute_with_error():
    status, output, error = execute(
        [sys.executable, "-c", "import sys; sys.exit(2)"]
    )
    assert status == 2
    assert re.match(r"^$", output)
    assert re.match(r"^$", error)


def test_execute_with_success():
    status, output, error = execute(["echo", "Hello world"])
    assert status == 0
    assert re.match(r"^Hello world\s*$", output)
    assert re.match(r"^$", error)


def test_execute_demux():
    status, output, error = execute([sys.executable, "-c", WRITE_BOTH])
    assert status == 0
    assert output == "foo"
    assert error == "bar"


def test_execute_no_demux():
    status, output = execute_no_demux([sys.executable, "-c", WRITE_BOTH])
    assert status == 0
    assert output == "foobar"


def test_execute_and_report():
    assert er([sys.executable, "-c", "import sys; sys.exit(0)"])
    assert not er([sys.executable, "-c", "import sys; sys.exit(1)"])
    assert not er([sys.executable, "-c", "import sys; sys.exit(-1)"])
    assert not er([sys.executable, "-c", "import sys; sys.exit(2)"])


def test_not_existing_command():
    pytest.raises(ExecutableNotFound, lambda: execute("non_existing_command"))
