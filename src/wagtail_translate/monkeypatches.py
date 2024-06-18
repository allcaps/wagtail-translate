"""
Ideally, Wagtail would fire a copy_for_translation_done signal.

For now, we monkeypatch the `CopyPageForTranslationAction.walk` and
`CopyPageForTranslationAction.execute` methods
to register the copy_for_translation_done signals.
"""

import logging

import wagtail

from wagtail.actions.copy_for_translation import CopyPageForTranslationAction


logger = logging.getLogger(__name__)


def new_walk(self, current_page):
    for child_page in current_page.get_children():
        translated_page = self._copy_for_translation(
            child_page,
            self.locale,
            self.copy_parents,
            self.alias,
            self.exclude_fields,
        )

        # Send signal
        from wagtail_translate.signals import copy_for_translation_done

        copy_for_translation_done.send(
            sender=self.__class__,
            source_obj=child_page.specific,
            target_obj=translated_page,
        )

        self.walk(child_page)


def new_execute(self, skip_permission_checks=False):
    self.check(skip_permission_checks=skip_permission_checks)

    translated_page = self._copy_for_translation(
        self.page, self.locale, self.copy_parents, self.alias, self.exclude_fields
    )

    # Send signal
    from wagtail_translate.signals import copy_for_translation_done

    copy_for_translation_done.send(
        sender=self.__class__, source_obj=self.page, target_obj=translated_page
    )

    if self.include_subtree:
        self.walk(self.page)

    return translated_page


# Wagtail 6.2 introduces the `copy_for_translation_done` signal.
# Only apply the monkeypatch if Wagtail < 6.2.
if wagtail.VERSION[0] < 6 or (wagtail.VERSION[0] == 6 and wagtail.VERSION[1] < 2):
    logger.warning(
        "Monkeypatching wagtail.actions.copy_for_translation.CopyPageForTranslationAction.walk, send copy_for_translation_done signal"
    )
    logger.warning(
        "Monkeypatching wagtail.actions.copy_for_translation.CopyPageForTranslationAction.execute, send copy_for_translation_done signal"
    )
    CopyPageForTranslationAction.walk = new_walk
    CopyPageForTranslationAction.execute = new_execute
