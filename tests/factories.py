import factory
import wagtail_factories

from django.core.files.base import ContentFile
from factory.django import DjangoModelFactory
from wagtail.images import get_image_model_string
from wagtail.models import Locale, Page

from tests.testapp.models import BlogPostPage


class LocaleFactory(factory.django.DjangoModelFactory):
    language_code = "fr"

    class Meta:
        model = Locale
        django_get_or_create = ("language_code",)


class ImageFactory(DjangoModelFactory):
    title = "Some image"
    file = factory.LazyAttribute(
        lambda _: ContentFile(factory.django.ImageField()._make_data({}), "example.jpg")
    )

    class Meta:
        model = get_image_model_string()
        django_get_or_create = ("title",)


class BlogPostPageFactory(wagtail_factories.PageFactory):
    title = factory.Sequence(lambda n: f"Page {n}")

    class Meta:
        model = BlogPostPage

    @factory.lazy_attribute
    def parent(self):
        return Page.get_first_root_node()
