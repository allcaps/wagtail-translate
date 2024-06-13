from wagtail.models import Locale


def test_translate_title(pages):
    home, blog_index, blog_post = pages
    locale = Locale.objects.create(language_code="fr")
    translation = home.copy_for_translation(locale=locale)
    assert translation.title == "Ubzr"  # ROT13 of "Home"
