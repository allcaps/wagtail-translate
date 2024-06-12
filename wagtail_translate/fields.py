from django.db import models
from modelcluster.fields import ParentalKey, ParentalManyToManyField
from modelcluster.models import ClusterableModel, get_all_child_relations
from treebeard.mp_tree import MP_Node
from wagtail.fields import RichTextField, StreamField
from wagtail.models import COMMENTS_RELATION_NAME, Page, TranslatableMixin


def get_translatable_fields(model):
    """
    Derives a list of translatable fields from the given model class.

    Arguments:
        model (Model class): The model class to derive translatable fields from.

    Returns:
        list[TranslatableField or SynchronizedField]:
            A list of TranslatableField and SynchronizedFields that were derived from the model.
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
        # These are usually used for enums and should not be translated.
        if isinstance(field, models.CharField) and field.choices:
            continue

        if isinstance(field, StreamField):
            translatable_fields.append(field)
            continue

        if isinstance(field, RichTextField):
            translatable_fields.append(field)
            continue

        # Text fields should translate
        if isinstance(
            field, (models.TextField, models.CharField)
        ):
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

            # Foreign keys to translatable models should be translatable.
            # With the exception of pages that are special because we can localize them at runtime easily.
            # TODO: Perhaps we need a special type for pages where it links to the translation if availabe,
            # but falls back to the source if it isn't translated yet?
            # Note: This exact same decision was made for page chooser blocks in segments/extract.py
            if issubclass(field.related_model, TranslatableMixin) and not issubclass(
                field.related_model, Page
            ):
                continue
                # TODO, implement related Translatable support
                # translatable_fields.append(field)
            else:
                continue

        # TODO
        # # Fields that support extracting segments are translatable
        # elif hasattr(field, "get_translatable_segments"):
        #     translatable_fields.append(TranslatableField(field))
        #
        # else:
        #     # Everything else is synchronised
        #     translatable_fields.append(SynchronizedField(field))

    # Add child relations for clusterable models
    # if issubclass(model, ClusterableModel):
    #     for child_relation in get_all_child_relations(model):
    #         # Ignore comments
    #         if (
    #             issubclass(model, Page)
    #             and child_relation.name == COMMENTS_RELATION_NAME
    #         ):
    #             continue
    #
    #         if issubclass(child_relation.related_model, TranslatableMixin):
    #             translatable_fields.append(child_relation.name)
    #         else:
    #             continue

    # Combine with any overrides defined on the model
    # override_translatable_fields = getattr(model, "override_translatable_fields", [])
    #
    # if override_translatable_fields:
    #     override_translatable_fields = {
    #         field.field_name: field for field in override_translatable_fields
    #     }
    #
    #     combined_translatable_fields = []
    #     for field in translatable_fields:
    #         if field.field_name in override_translatable_fields:
    #             combined_translatable_fields.append(
    #                 override_translatable_fields.pop(field.field_name)
    #             )
    #         else:
    #             combined_translatable_fields.append(field)
    #
    #     if override_translatable_fields:
    #         combined_translatable_fields.extend(override_translatable_fields.values())
    #
    #     return combined_translatable_fields
    #
    # else:

    return translatable_fields
