from __future__ import annotations

from unittest.mock import patch

from deptry.compat import metadata
from deptry.dependency import Dependency


def test_simple_dependency() -> None:
    dependency = Dependency("click")
    assert dependency.name == "click"
    assert dependency.top_levels == {"click"}


def test_create_default_top_level_if_metadata_not_found() -> None:
    dependency = Dependency("Foo-bar")
    assert dependency.name == "Foo-bar"
    assert dependency.top_levels == {"foo_bar"}


def test_read_top_level_from_top_level_txt() -> None:
    """
    Read the top-levels.txt file
    """

    class MockDistribution:
        def __init__(self) -> None:
            pass

        def read_text(self, file_name: str) -> str:
            return "foo\nbar"

    with patch("deptry.dependency.metadata.distribution") as mock:
        mock.return_value = MockDistribution()
        dependency = Dependency("Foo-bar")

    assert dependency.name == "Foo-bar"
    assert dependency.top_levels == {"foo", "bar"}


def test_read_top_level_from_record() -> None:
    """
    Verify that if top-level.txt not found, an attempt is made to extract top-level module names from
    the metadata RECORD file.
    """

    class MockDistribution:
        def __init__(self) -> None:
            pass

        def read_text(self, file_name: str) -> str | None:
            if file_name == "RECORD":
                return """\
../../../bin/black,sha256=<HASH>,247
__pycache__/_black_version.cpython-311.pyc,,
_black_version.py,sha256=<HASH>,19
black/trans.cpython-39-darwin.so,sha256=<HASH>
black/trans.py,sha256=<HASH>
blackd/__init__.py,sha256=<HASH>
blackd/__main__.py,sha256=<HASH>
                """
            return None

    with patch("deptry.dependency.metadata.distribution") as mock:
        mock.return_value = MockDistribution()
        dependency = Dependency("Foo-bar")

    assert dependency.name == "Foo-bar"
    assert dependency.top_levels == {"_black_version", "black", "blackd"}


def test_read_top_level_from_predefined() -> None:
    """
    Verify that if there are predefined top-level module names it takes
    precedence over other lookup methods.
    """
    with patch("deptry.dependency.metadata.distribution") as mock:
        dependency = Dependency("Foo-bar", module_names=["foo"])

    assert dependency.name == "Foo-bar"
    assert dependency.top_levels == {"foo"}
    mock.return_value.read_text.assert_not_called()


def test_not_predefined_and_not_installed() -> None:
    """
    Use the fallback option of translating the package name.
    """

    with patch("deptry.dependency.metadata.distribution") as mock:
        mock.side_effect = metadata.PackageNotFoundError
        dependency = Dependency("Foo-bar")

    assert dependency.name == "Foo-bar"
    assert dependency.top_levels == {"foo_bar"}
