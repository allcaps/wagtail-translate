import pytest
from django.utils.crypto import get_random_string
from wagtail.models import Page, Site

from testproject.home.models import HomePage, BlogIndexPage, BlogPostPage


class TestFieldBlockTypes:

    @pytest.fixture
    def page(self):
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

        self.home = home

        self.blog_index = BlogIndexPage(title="Blog", slug="blog")
        self.home.add_child(instance=self.blog_index)

        self.blog_post = BlogPostPage(title="Blog post", slug="blog-post")
        self.blog_index.add_child(instance=self.blog_post)

    def test_translate_text(self):
        self.blog_post.body = [
            {'paragraph': 'This is a paragraph.'},
        ]
        self.home.copy_for_translation()

    def test_translate_richtext(self):
        pass


    def test_translate_raw_html(self):
        pass


    def test_translate_struct(self):
        pass


    def test_translate_block_quote(self):
        pass


    def test_translate_chooser(self):
        pass


    def test_translate_page_chooser(self):
        pass
