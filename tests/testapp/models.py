from django.db import models
from wagtail import blocks
from wagtail.admin.panels import FieldPanel
from wagtail.documents.blocks import DocumentChooserBlock
from wagtail.fields import RichTextField, StreamField
from wagtail.images.blocks import ImageChooserBlock
from wagtail.models import Page, TranslatableMixin
from wagtail.snippets.blocks import SnippetChooserBlock
from wagtail.snippets.models import register_snippet


class HomePage(Page):
    pass


class ImageBlock(blocks.StructBlock):
    image = ImageChooserBlock()
    caption = blocks.CharBlock(required=False)

    class Meta:
        icon = "image"


class BlogIndexPage(Page):
    introduction = models.TextField(blank=True)

    content_panels = Page.content_panels + [
        FieldPanel("introduction"),
    ]


@register_snippet
class BlogCategory(TranslatableMixin):
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name

    class Meta(TranslatableMixin.Meta):
        verbose_name_plural = "Blog Categories"


class BlogPostPage(Page):
    category = models.ForeignKey(
        BlogCategory,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="blog_posts",
    )
    intro = RichTextField(blank=True)
    publication_date = models.DateField(null=True, blank=True)
    image = models.ForeignKey(
        "wagtailimages.Image", on_delete=models.SET_NULL, null=True, blank=True
    )

    body = StreamField(
        [
            ("heading", blocks.CharBlock()),
            ("paragraph", blocks.RichTextBlock()),
            ("stream", blocks.StreamBlock([("paragraph", blocks.CharBlock())])),
            (
                "stream_nested",
                blocks.StreamBlock(
                    [
                        (
                            "stream",
                            blocks.StreamBlock([("paragraph", blocks.CharBlock())]),
                        )
                    ]
                ),
            ),
            ("list", blocks.ListBlock(blocks.CharBlock())),
            ("list_nested", blocks.ListBlock(blocks.ListBlock(blocks.CharBlock()))),
            (
                "struct",
                blocks.StructBlock(
                    [("paragraph", blocks.CharBlock()), ("image", ImageChooserBlock())]
                ),
            ),
            # TODO: Add support for nested StructBlocks.
            #  Not sure why anyone would want to nest StructBlocks, but it is possible.
            #  ("struct_nested", blocks.StructBlock([("struct", blocks.StructBlock([("paragraph", blocks.CharBlock()), ("image", ImageChooserBlock())]))])),
            ("image_struct", ImageBlock()),
            ("raw", blocks.RawHTMLBlock()),
            ("block_quote", blocks.BlockQuoteBlock()),
            ("page", blocks.PageChooserBlock()),
            ("document", DocumentChooserBlock()),
            ("image_chooser", ImageChooserBlock()),
            ("snippet", SnippetChooserBlock(BlogCategory)),
        ],
        use_json_field=True,
    )

    content_panels = Page.content_panels + [
        FieldPanel("category"),
        FieldPanel("intro"),
        FieldPanel("publication_date"),
        FieldPanel("image"),
        FieldPanel("body"),
    ]
