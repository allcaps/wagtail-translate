from wagtail.snippets.models import register_snippet
from wagtail.snippets.views.chooser import SnippetChooserViewSet
from wagtail.snippets.views.snippets import SnippetViewSet

from .models import BlogCategory


class BlogCategoryChooserViewSet(SnippetChooserViewSet):
    form_fields = ("name",)


class BlogCategoryViewSet(SnippetViewSet):
    model = BlogCategory
    chooser_viewset_class = BlogCategoryChooserViewSet


register_snippet(BlogCategoryViewSet)
