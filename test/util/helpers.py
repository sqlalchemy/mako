import contextlib
import pathlib
import re
import time
from unittest import mock

from test.util.fixtures import module_base


def flatten_result(result):
    return re.sub(r"[\s\r\n]+", " ", result).strip()


def result_lines(result):
    return [
        x.strip()
        for x in re.split(r"\r?\n", re.sub(r" +", " ", result))
        if x.strip() != ""
    ]


def replace_file_with_dir(pathspec):
    path = pathlib.Path(pathspec)
    path.unlink(missing_ok=True)
    path.mkdir(exist_ok=True)
    return path


def file_with_template_code(filespec):
    with open(filespec, "w") as f:
        f.write(
            """
i am an artificial template just for you
"""
        )
    return filespec


@contextlib.contextmanager
def rewind_compile_time(hours=1):
    rewound = time.time() - (hours * 3_600)
    with mock.patch("mako.codegen.time") as codegen_time:
        codegen_time.time.return_value = rewound
        yield


def teardown():
    import shutil

    shutil.rmtree(module_base, True)
