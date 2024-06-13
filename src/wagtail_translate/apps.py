from django.apps import AppConfig


class WagtailTranslateAppConfig(AppConfig):
    label = "wagtail_translate"
    name = "wagtail_translate"
    verbose_name = "Wagtail Translate"

    def ready(self):

        from wagtail.signals import copy_for_translation_done
        from wagtail_translate.translators.deepl import DeepLTranslator
        from django.dispatch import receiver
        from wagtail.models import Page, TranslatableMixin

        @receiver(copy_for_translation_done)
        def actual_translation(sender, source_obj, target_obj, **kwargs):
            """
            Perform actual translation.

            Wagtail triggers the copy_for_translation_done signal,
            and this signal handler translates the contents.

            The source_obj must be a subclass of TranslatableMixin.

            Integrators are expected to define their own signal receiver.
            This receiver allows easy customization of behaviors:

            - A custom Translator class can be specified.
            - Pages can be saved as drafts (to be reviewed)
            or published (directly visible to the public).
            - Custom workflows can be triggered.
            - Data can be post-processed.
            - And more ...
            """

            print("Translating", source_obj, "to", target_obj)

            if not issubclass(target_obj.__class__, TranslatableMixin):
                raise Exception(
                    "Object must be a subclass of TranslatableMixin. "
                    f"Got {type(target_obj)}."
                )

            # Get the source and target language codes
            source_language_code = source_obj.locale.language_code
            target_language_code = target_obj.locale.language_code

            # Initialize the translator, and translate.
            translator = DeepLTranslator(source_language_code, target_language_code)
            translated_obj = translator.translate_obj(source_obj, target_obj)

            # Differentiate between regular Django model and Wagtail Page.
            # - Page instances have `save_revision` and `publish` methods.
            # - Regular Django model (aka Wagtail Snippet) need to be saved.
            if isinstance(translated_obj, Page):
                # Calling `publish` is optional,
                # and will publish the translated page.
                # Without, the page will be in draft mode.
                translated_obj.save_revision().publish()
            else:
                translated_obj.save()