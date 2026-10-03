from django.core.management import call_command
from wagtail.models import Locale, Page, Site

from tests.testproject.demoapp.models import (
    BlogIndexPage,
    BlogPostPage,
    HomePage,
)


def test_createcontent_builds_english_demo_tree(db):
    call_command("createcontent")

    homepage = HomePage.objects.get(title="Home", locale__language_code="en")
    blog_index = BlogIndexPage.objects.child_of(homepage).get(
        slug="blog-index",
        locale__language_code="en",
    )
    blog_posts = BlogPostPage.objects.child_of(blog_index).order_by("slug")

    assert Site.objects.get(is_default_site=True).root_page.specific == homepage
    assert blog_index.title == "Blog"
    assert list(blog_posts.values_list("title", flat=True)) == [
        "A cat at the window",
        "A field guide to birds",
        "The match",
        "The match 2",
    ]

    match_post = blog_posts.get(slug="the-match")
    assert str(match_post.intro) == (
        "<p>Strike the match against the box to light the candle.</p>"
    )
    assert len(match_post.body) == 0

    match_part_two = blog_posts.get(slug="the-match-2")
    assert str(match_part_two.intro) == (
        "<p>The football match ended in a draw after both teams scored twice.</p>"
    )
    assert len(match_part_two.body) == 0

    cat_post = blog_posts.get(slug="a-cat-at-the-window")
    assert str(cat_post.body[0].value) == (
        "<p>A <em>black</em> cat sat on the windowsill.</p>"
    )

    bird_post = blog_posts.get(slug="a-field-guide-to-birds")
    bird_blocks = {block.block_type: block.value for block in bird_post.body}
    body_field = BlogPostPage._meta.get_field("body")
    assert set(bird_blocks) == set(body_field.stream_block.child_blocks)
    assert len(bird_blocks["stream"]) == 3
    assert len(bird_blocks["stream_nested"]) == 3
    assert all(len(stream.value) == 3 for stream in bird_blocks["stream_nested"])
    assert len(bird_blocks["list"]) == 3
    assert len(bird_blocks["list_nested"]) == 3
    assert all(len(items) == 3 for items in bird_blocks["list_nested"])

    created_pages = [homepage, blog_index, *blog_posts]
    assert {page.locale.language_code for page in created_pages} == {"en"}
    assert (
        Page.objects.filter(
            translation_key__in=[page.translation_key for page in created_pages]
        ).count()
        == 6
    )


def test_createcontent_removes_existing_pages_before_rebuilding(db):
    call_command("createcontent")

    root_page = Page.get_first_root_node()
    french_locale, _ = Locale.objects.get_or_create(language_code="fr")
    old_french_homepage = HomePage(
        title="Ancien accueil",
        slug="ancien-accueil",
        locale=french_locale,
    )
    root_page.add_child(instance=old_french_homepage)

    call_command("createcontent")

    homepage = HomePage.objects.get(title="Home", locale__language_code="en")
    blog_index = BlogIndexPage.objects.child_of(homepage).get(slug="blog-index")

    assert root_page.get_children().count() == 1
    assert not Page.objects.filter(title="Ancien accueil").exists()
    assert set(
        Page.objects.exclude(pk=root_page.pk).values_list(
            "locale__language_code", flat=True
        )
    ) == {"en"}
    assert (
        BlogPostPage.objects.child_of(blog_index)
        .filter(
            slug__in=[
                "the-match",
                "the-match-2",
                "a-cat-at-the-window",
                "a-field-guide-to-birds",
            ]
        )
        .count()
        == 4
    )
