import re
import subprocess


def get_output(*args):
    p = subprocess.Popen(
        args,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    out, err = p.communicate()
    if p.returncode != 0:
        return [l.strip() for l in err.decode().split("\n") if len(l)]
    return [l.strip() for l in out.decode().split("\n") if len(l)]


def compare_outputs(actual, expected):
    assert len(expected) == len(actual)
    for index, line in enumerate(actual):
        assert re.match(fr'{expected[index]}', line)
