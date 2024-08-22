"""
Wagtail 6.3 introduces the copy_for_translation_done signal for models (snippets).
Wagtail Translate will patch older versions of Wagtail.

The `CopyForTranslationAction.execute` method is patched.
The new method sends the `copy_for_translation_done` signal.
"""

import logging

from wagtail.actions.copy_for_translation import CopyForTranslationAction


logger = logging.getLogger(__name__)


def new_execute(self, skip_permission_checks=False):
    self.check(skip_permission_checks=skip_permission_checks)

    translated_object = self._copy_for_translation(
        self.object, self.locale, self.exclude_fields
    )

    # Depending on the Wagtail version,
    # the signal may be defined in Wagtail or in Wagtail Translate.
    try:
        from wagtail.signals import copy_for_translation_done
    except ImportError:
        from wagtail_translate.signals import copy_for_translation_done

    # Send signal
    copy_for_translation_done.send(
        sender=self.__class__,
        source_obj=self.object,
        target_obj=translated_object,
    )

    return translated_object


logger.warning(
    "Monkeypatching wagtail.actions.copy_for_translation.CopyForTranslationAction.execute, send copy_for_translation_done signal"
)
CopyForTranslationAction.execute = new_execute
