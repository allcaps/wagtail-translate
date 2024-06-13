import factory

from django.core.files.base import ContentFile
from factory.django import DjangoModelFactory
from wagtail.images import get_image_model_string


class ImageFactory(DjangoModelFactory):
    title = "Some image"
    file = factory.LazyAttribute(
        lambda _: ContentFile(factory.django.ImageField()._make_data({}), "example.jpg")
    )

    class Meta:
        model = get_image_model_string()
        django_get_or_create = ("title",)
