"""Nox configuration for Mako."""

from __future__ import annotations

import sys

import nox

nox.needs_version = ">=2025.10.16"

if True:
    sys.path.insert(0, ".")
    from tools.toxnox import tox_parameters
    from tools.toxnox import apply_pytest_opts


PYTHON_VERSIONS = [
    "3.10",
    "3.11",
    "3.12",
    "3.13",
    "3.14",
    "3.14t",
    "3.15",
]

pyproject = nox.project.load_toml("pyproject.toml")

nox.options.sessions = ["tests"]
nox.options.tags = ["py-tests"]


@nox.session()
@tox_parameters(["python"], [PYTHON_VERSIONS], base_tag="tests")
def tests(session: nox.Session) -> None:
    """Run the main test suite."""

    session.install(".")
    session.install(*nox.project.dependency_groups(pyproject, "tests"))

    posargs = apply_pytest_opts(session, "mako", [])
    session.run("python", "-m", "pytest", *posargs)


@nox.session(name="coverage")
def coverage(session: nox.Session) -> None:
    """Run tests with coverage."""

    session.install("-e", ".")
    session.install(*nox.project.dependency_groups(pyproject, "tests"))
    session.install(*nox.project.dependency_groups(pyproject, "coverage"))

    posargs = apply_pytest_opts(session, "mako", ["mako"], coverage=True)
    session.run("python", "-m", "pytest", *posargs)


@nox.session(name="pep8")
def lint(session: nox.Session) -> None:
    """Run linting and formatting checks."""

    session.install(*nox.project.dependency_groups(pyproject, "lint"))

    session.run(
        "flake8p",
        "./mako/",
        "./test/",
        "./examples/",
        "setup.py",
        "noxfile.py",
    )
    session.run("black", "--check", ".")


@nox.session(name="pep484")
def mypy_check(session: nox.Session) -> None:
    """Run mypy type checking - not yet implemented."""

    session.run(
        "python",
        "-c",
        "print('pep484 is not yet implemented for this project')",
    )
