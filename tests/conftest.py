import pytest

from django.utils.crypto import get_random_string
from wagtail.models import Page, Site

from .factories import ImageFactory
from .testapp.models import BlogCategory, BlogIndexPage, BlogPostPage, HomePage


@pytest.fixture(autouse=True)
def temporary_media_dir(settings, tmp_path: pytest.TempdirFactory):
    settings.MEDIA_ROOT = tmp_path / "media"


@pytest.fixture
def pages(db):
    home = HomePage.objects.first()
    if not home:
        root = Page.get_first_root_node()
        home = HomePage(title="Home", slug=f"home-{get_random_string(length=32)}")
        root.add_child(instance=home)
        site = Site.objects.first()
        old_home = site.root_page
        site.root_page = home
        site.save()
        old_home.delete()
        home.slug = "home"
        home.save()

    blog_index = BlogIndexPage(title="Blog", slug="blog")
    home.add_child(instance=blog_index)

    category, _ = BlogCategory.objects.get_or_create(
        name="Category", locale=home.locale
    )

    blog_post = BlogPostPage(title="Blog post", category=category, image=ImageFactory())
    blog_index.add_child(instance=blog_post)
    return home, blog_index, blog_post
