import pytest

from wagtail_translate.apps import patch_needed


@pytest.mark.parametrize(
    "version, expected",
    [
        ((5, 1, 0), True),
        ((5, 2, 0), True),
        ((5, 3, 0), True),
        ((6, 1, 0), True),
        ((6, 1, 9), True),
        ((6, 2, 0), False),  # 6.2 introduces the `copy_for_translation_done` signal.
        ((6, 2, 1), False),
        ((6, 3, 0), False),
    ],
)
def test_patch_needed(version, expected):
    assert patch_needed(version) is expected
