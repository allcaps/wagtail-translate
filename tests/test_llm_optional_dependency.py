import os
import subprocess
import sys
import textwrap


def test_missing_llm_extra_has_clear_import_error():
    script = textwrap.dedent(
        """
        import importlib.abc
        import sys

        import django

        django.setup()

        class BlockPydanticImports(importlib.abc.MetaPathFinder):
            def find_spec(self, fullname, path, target=None):
                if fullname == "pydantic" or fullname.startswith("pydantic_ai"):
                    raise ModuleNotFoundError(fullname)
                return None

        sys.meta_path.insert(0, BlockPydanticImports())

        try:
            import wagtail_translate.translators.pydantic_ai
        except ImportError as exc:
            assert "wagtail-translate[llm]" in str(exc)
        else:
            raise AssertionError("Expected the optional dependency import to fail")
        """
    )
    environment = os.environ.copy()
    environment["DJANGO_SETTINGS_MODULE"] = "tests.testproject.settings"

    subprocess.run(
        [sys.executable, "-c", script],  # noqa: S603 - test-controlled input
        check=True,
        env=environment,
        capture_output=True,
        text=True,
    )
