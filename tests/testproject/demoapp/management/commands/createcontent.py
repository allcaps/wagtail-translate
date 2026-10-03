import base64

from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand
from django.db import transaction
from wagtail.documents import get_document_model
from wagtail.images import get_image_model
from wagtail.models import Locale, Page, Site
from wagtail.rich_text import RichText

from tests.testproject.demoapp.models import (
    BlogCategory,
    BlogIndexPage,
    BlogPostPage,
    HomePage,
)

BLOG_POSTS = (
    {
        "title": "The match",
        "slug": "the-match",
        "intro": "<p>Strike the match against the box to light the candle.</p>",
        "body": (),
    },
    {
        "title": "The match 2",
        "slug": "the-match-2",
        "intro": (
            "<p>The football match ended in a draw after both teams scored twice.</p>"
        ),
        "body": (),
    },
    {
        "title": "A cat at the window",
        "slug": "a-cat-at-the-window",
        "intro": "",
        "body": "<p>A <em>black</em> cat sat on the windowsill.</p>",
    },
)

BIRD_IMAGE_DATA = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8A"
    "AQUBAScY42YAAAAASUVORK5CYII="
)


class Command(BaseCommand):
    help = "Create English demo pages that exercise document-level translation."

    @transaction.atomic
    def handle(self, *args, **options):
        english_locale, _ = Locale.objects.get_or_create(language_code="en")
        root_page = Page.get_first_root_node()

        Site.objects.all().delete()
        for existing_page in root_page.get_children().specific():
            existing_page.delete()

        homepage = self.create_homepage(root_page, english_locale)
        Site.objects.create(
            hostname="localhost",
            root_page=homepage,
            is_default_site=True,
            site_name="Wagtail Translate demo",
        )
        blog_index = self.create_blog_index(homepage, english_locale)
        self.create_blog_posts(blog_index, english_locale)
        bird_image, bird_document, bird_category = self.get_or_create_bird_assets(
            english_locale
        )
        self.create_bird_post(
            blog_index=blog_index,
            english_locale=english_locale,
            homepage=homepage,
            bird_image=bird_image,
            bird_document=bird_document,
            bird_category=bird_category,
        )

        self.stdout.write(
            self.style.SUCCESS(
                "Reset the page tree and created an English homepage, a blog "
                "index, and 4 blog posts."
            )
        )

    def create_homepage(self, root_page, english_locale):
        homepage = HomePage(
            title="Home",
            slug="home",
            locale=english_locale,
        )
        root_page.add_child(instance=homepage)
        homepage.save_revision().publish()
        return homepage

    def create_blog_index(self, homepage, english_locale):
        blog_index = BlogIndexPage(
            title="Blog",
            slug="blog-index",
            locale=english_locale,
            introduction=(
                "Examples that demonstrate why an LLM needs the complete document "
                "when translating ambiguous words and inline HTML."
            ),
        )
        homepage.add_child(instance=blog_index)
        blog_index.save_revision().publish()
        return blog_index

    def create_blog_posts(self, blog_index, english_locale):
        for post_content in BLOG_POSTS:
            blog_post = BlogPostPage(
                title=post_content["title"],
                slug=post_content["slug"],
                locale=english_locale,
                intro=post_content["intro"],
                body=(
                    [("paragraph", RichText(post_content["body"]))]
                    if post_content["body"]
                    else []
                ),
            )
            blog_index.add_child(instance=blog_post)
            blog_post.save_revision().publish()

    def get_or_create_bird_assets(self, english_locale):
        image_model = get_image_model()
        bird_image = image_model.objects.filter(title="Bird silhouette demo").first()
        if bird_image is None:
            bird_image = image_model(
                title="Bird silhouette demo",
                file=ContentFile(BIRD_IMAGE_DATA, name="bird-silhouette.png"),
            )
            bird_image.save()

        document_model = get_document_model()
        bird_document = document_model.objects.filter(
            title="Birdwatching field notes"
        ).first()
        if bird_document is None:
            bird_document = document_model(
                title="Birdwatching field notes",
                file=ContentFile(
                    b"Look, listen, record the habitat, and leave no trace.\n",
                    name="birdwatching-field-notes.txt",
                ),
            )
            bird_document.save()

        bird_category = BlogCategory.objects.filter(
            locale=english_locale,
            name="Birds",
        ).first()
        if bird_category is None:
            bird_category = BlogCategory.objects.create(
                locale=english_locale,
                name="Birds",
            )

        return bird_image, bird_document, bird_category

    def create_bird_post(
        self,
        *,
        blog_index,
        english_locale,
        homepage,
        bird_image,
        bird_document,
        bird_category,
    ):
        bird_post = BlogPostPage(
            title="A field guide to birds",
            slug="a-field-guide-to-birds",
            locale=english_locale,
            category=bird_category,
            intro=(
                "<p>A tour of every StreamField block, filled with birds from "
                "gardens, forests, and wetlands.</p>"
            ),
            image=bird_image,
        )
        blog_index.add_child(instance=bird_post)
        bird_post.body = [
            ("heading", "Birds in many habitats"),
            (
                "paragraph",
                RichText(
                    "<p>Birds bring <strong>colour</strong>, movement, and song "
                    "to every landscape.</p>"
                ),
            ),
            (
                "stream",
                [
                    ("paragraph", "A robin sings at dawn."),
                    ("paragraph", "A swallow circles above the meadow."),
                    ("paragraph", "A heron waits beside the water."),
                ],
            ),
            (
                "stream_nested",
                [
                    (
                        "stream",
                        [
                            ("paragraph", "Robin"),
                            ("paragraph", "Blackbird"),
                            ("paragraph", "Wren"),
                        ],
                    ),
                    (
                        "stream",
                        [
                            ("paragraph", "Jay"),
                            ("paragraph", "Woodpecker"),
                            ("paragraph", "Owl"),
                        ],
                    ),
                    (
                        "stream",
                        [
                            ("paragraph", "Heron"),
                            ("paragraph", "Kingfisher"),
                            ("paragraph", "Grebe"),
                        ],
                    ),
                ],
            ),
            ("list", ["Robin", "Blackbird", "Wren"]),
            (
                "list_nested",
                [
                    ["Robin", "Blackbird", "Wren"],
                    ["Jay", "Woodpecker", "Owl"],
                    ["Heron", "Kingfisher", "Grebe"],
                ],
            ),
            (
                "struct",
                {
                    "paragraph": "A kingfisher flashes blue above the river.",
                    "image": bird_image,
                },
            ),
            (
                "image_struct",
                {
                    "image": bird_image,
                    "caption": "A small bird resting between flights.",
                },
            ),
            (
                "raw",
                (
                    '<aside data-habitat="wetland"><p>Reeds shelter nesting '
                    "birds.</p></aside>"
                ),
            ),
            (
                "block_quote",
                "A patient observer notices a different bird every day.",
            ),
            ("page", homepage),
            ("document", bird_document),
            (
                "image_chooser",
                {
                    "image": bird_image,
                    "decorative": False,
                    "alt_text": "A bird perched on a slender branch.",
                },
            ),
            ("snippet", bird_category),
        ]
        bird_post.save_revision().publish()
