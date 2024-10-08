# Generated by Django 4.2.15 on 2024-08-21 13:45

import uuid

import django.db.models.deletion
import wagtail.blocks
import wagtail.documents.blocks
import wagtail.fields
import wagtail.images.blocks
import wagtail.snippets.blocks

from django.db import migrations, models

import tests.testapp.models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("wagtailimages", "0025_alter_image_file_alter_rendition_file"),
        ("wagtailcore", "0089_log_entry_data_json_null_to_object"),
    ]

    operations = [
        migrations.CreateModel(
            name="BlogCategory",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "translation_key",
                    models.UUIDField(default=uuid.uuid4, editable=False),
                ),
                ("name", models.CharField(max_length=255)),
                (
                    "locale",
                    models.ForeignKey(
                        editable=False,
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="+",
                        to="wagtailcore.locale",
                    ),
                ),
            ],
            options={
                "verbose_name_plural": "Blog Categories",
                "abstract": False,
                "unique_together": {("translation_key", "locale")},
            },
        ),
        migrations.CreateModel(
            name="BlogIndexPage",
            fields=[
                (
                    "page_ptr",
                    models.OneToOneField(
                        auto_created=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        parent_link=True,
                        primary_key=True,
                        serialize=False,
                        to="wagtailcore.page",
                    ),
                ),
                ("introduction", models.TextField(blank=True)),
            ],
            options={
                "abstract": False,
            },
            bases=("wagtailcore.page",),
        ),
        migrations.CreateModel(
            name="HomePage",
            fields=[
                (
                    "page_ptr",
                    models.OneToOneField(
                        auto_created=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        parent_link=True,
                        primary_key=True,
                        serialize=False,
                        to="wagtailcore.page",
                    ),
                ),
            ],
            options={
                "abstract": False,
            },
            bases=("wagtailcore.page",),
        ),
        migrations.CreateModel(
            name="BlogPostPage",
            fields=[
                (
                    "page_ptr",
                    models.OneToOneField(
                        auto_created=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        parent_link=True,
                        primary_key=True,
                        serialize=False,
                        to="wagtailcore.page",
                    ),
                ),
                ("intro", wagtail.fields.RichTextField(blank=True)),
                ("publication_date", models.DateField(blank=True, null=True)),
                (
                    "body",
                    wagtail.fields.StreamField(
                        [
                            ("heading", wagtail.blocks.CharBlock()),
                            ("paragraph", wagtail.blocks.RichTextBlock()),
                            (
                                "stream",
                                wagtail.blocks.StreamBlock(
                                    [("paragraph", wagtail.blocks.CharBlock())]
                                ),
                            ),
                            (
                                "stream_nested",
                                wagtail.blocks.StreamBlock(
                                    [
                                        (
                                            "stream",
                                            wagtail.blocks.StreamBlock(
                                                [
                                                    (
                                                        "paragraph",
                                                        wagtail.blocks.CharBlock(),
                                                    )
                                                ]
                                            ),
                                        )
                                    ]
                                ),
                            ),
                            (
                                "list",
                                wagtail.blocks.ListBlock(wagtail.blocks.CharBlock()),
                            ),
                            (
                                "list_nested",
                                wagtail.blocks.ListBlock(
                                    wagtail.blocks.ListBlock(wagtail.blocks.CharBlock())
                                ),
                            ),
                            (
                                "struct",
                                wagtail.blocks.StructBlock(
                                    [
                                        ("paragraph", wagtail.blocks.CharBlock()),
                                        (
                                            "image",
                                            wagtail.images.blocks.ImageChooserBlock(),
                                        ),
                                    ]
                                ),
                            ),
                            (
                                "image_struct",
                                wagtail.blocks.StructBlock(
                                    [
                                        (
                                            "image",
                                            wagtail.images.blocks.ImageChooserBlock(),
                                        ),
                                        (
                                            "caption",
                                            wagtail.blocks.CharBlock(required=False),
                                        ),
                                    ]
                                ),
                            ),
                            ("raw", wagtail.blocks.RawHTMLBlock()),
                            ("block_quote", wagtail.blocks.BlockQuoteBlock()),
                            ("page", wagtail.blocks.PageChooserBlock()),
                            (
                                "document",
                                wagtail.documents.blocks.DocumentChooserBlock(),
                            ),
                            (
                                "image_chooser",
                                wagtail.images.blocks.ImageChooserBlock(),
                            ),
                            (
                                "snippet",
                                wagtail.snippets.blocks.SnippetChooserBlock(
                                    tests.testapp.models.BlogCategory
                                ),
                            ),
                        ],
                        use_json_field=True,
                    ),
                ),
                (
                    "category",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="blog_posts",
                        to="testapp.blogcategory",
                    ),
                ),
                (
                    "image",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        to="wagtailimages.image",
                    ),
                ),
            ],
            options={
                "abstract": False,
            },
            bases=("wagtailcore.page",),
        ),
    ]
