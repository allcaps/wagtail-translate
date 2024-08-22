from django.db import models
from modelcluster.fields import ParentalKey
from treebeard.mp_tree import MP_Node
from wagtail.fields import RichTextField, StreamField
from wagtail.models import Page, TranslatableMixin


def get_translatable_fields(model):
    """
    Derives a list of translatable fields (strings) from the given model class.

    Arguments:
        model (Model class): The model class to derive translatable fields from.

    Returns:
        list: A list of stings, containing the names of translatable fields.
    """

    # Set translatable_fields on the model to override the default behaviour.
    if hasattr(model, "translatable_fields"):
        return model.translatable_fields

    # Iterate over the fields and determine which ones are translatable.
    translatable_fields = []

    for field in model._meta.get_fields():
        # Ignore automatically generated ID fields
        if isinstance(field, models.AutoField):
            continue

        # Ignore non-editable fields
        if not field.editable:
            continue

        # TODO, figure out how to handle slug fields.
        # They might be used as identifiers and probably not be translated.
        # However, a Page.slug is used in the URL, and should be translated.
        if isinstance(field, models.SlugField):
            continue

        # Ignore many to many fields (not supported yet)
        # TODO: Add support for many to many fields.
        if isinstance(field, models.ManyToManyField):
            continue

        # Ignore Treebeard fields
        if issubclass(model, MP_Node) and field.name in ["path", "depth", "numchild"]:
            continue

        # Ignore some Page fields.
        if issubclass(model, Page) and field.name in [
            "go_live_at",
            "expire_at",
            "first_published_at",
            "content_type",
            "owner",
        ]:
            continue

        # Ignore URL and email fields
        if isinstance(field, (models.URLField, models.EmailField)):
            continue

        # Ignore choice fields
        # These are usually enums and should not be translated.
        if isinstance(field, models.CharField) and field.choices:
            continue

        if isinstance(field, StreamField):
            translatable_fields.append(field)
            continue

        if isinstance(field, RichTextField):
            translatable_fields.append(field)
            continue

        # Text fields should translate
        if isinstance(field, (models.TextField, models.CharField)):
            translatable_fields.append(field)
            continue

        # Foreign keys to translatable models should be translated.
        if isinstance(field, models.ForeignKey):
            # Ignore if this is a link to a parent model
            if isinstance(field, ParentalKey):
                continue

            # Ignore parent links
            if (
                isinstance(field, models.OneToOneField)
                and field.remote_field.parent_link
            ):
                continue

            # Foreign keys to translatable models should be translated.
            if issubclass(field.related_model, TranslatableMixin) and not issubclass(
                field.related_model, Page
            ):
                translatable_fields.append(field)
            else:
                continue

    return translatable_fields
