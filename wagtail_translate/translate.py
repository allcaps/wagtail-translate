import codecs

from bs4 import BeautifulSoup, NavigableString
from wagtail import blocks
from wagtail.fields import RichTextField, StreamField

from wagtail.rich_text import RichText

from .fields import get_translatable_fields


def lstrip_keep(text: str) -> (str, str):
    """
    Like lstrip, but also returns the whitespace that was stripped off
    """
    text_length = len(text)
    new_text = text.lstrip()
    prefix = text[0 : (text_length - len(new_text))]
    return new_text, prefix


def rstrip_keep(text: str) -> (str, str):
    """
    Like rstrip, but also returns the whitespace that was stripped off
    """
    text_length = len(text)
    new_text = text.rstrip()
    if text_length != len(new_text):
        suffix = text[-(text_length - len(new_text)) :]
    else:
        suffix = ""
    return new_text, suffix


class BlockItem:
    """Block item, helper class to pass block and value around."""

    def __init__(self, block, value):
        self.block = block
        self.value = value


class Translator:
    source_language_code: str
    target_language_code: str

    def __init__(self, source_language_code: str, target_language_code: str) -> None:
        self.source_language_code = source_language_code
        self.target_language_code = target_language_code

    def translate(self, source_string: str) -> str:
        """
        Translate, a function that does the actual translation.
        This will be replaced by a call to a translation service.

        ROT13 is its own inverse. Because there are 26 letters (2×13) in the
        Latin alphabet, applying ROT13 to a piece of text twice will give the
        original text.
        """
        # Rot13 does not need the language codes,
        # but a real translation service would.
        self.source_language_code  # noqa
        self.target_language_code  # noqa

        return codecs.encode(source_string, 'rot13')

    def translate_html_string(self, string: str) -> str:
        """
        Translate HTML string,

        Translates the string and preserves the left and right whitespace.

        HTML collapses whitespace, however left and right whitespace needs
        to be preserved, as it may be significant. For example, the whitespace
        in the following strings are significant:

            <p><strong>Hello</strong> World</p>
            <p><strong>Hello </strong>World</p>
        """
        string, left_whitespace = lstrip_keep(string)
        string, right_whitespace = rstrip_keep(string)
        translation = self.translate(string)
        return f"{left_whitespace}{translation}{right_whitespace}"

    def translate_attributes(self, soup):
        """
        Translate attributes, title and alt.
        """
        for tag in soup.find_all():
            if tag.has_attr('title'):
                tag['title'] = self.translate(tag['title'])
            if tag.has_attr('alt'):
                tag['alt'] = self.translate(tag['alt'])

    def translate_html(self, html: str) -> str:
        """
        Translate HTML,

        - Recursively walks the HTML tree, and translates the strings
        - Preserves whitespace
        - Translates attributes, alt and title

        Unfortunately, this is not a perfect solution, as it translates
        string segments one by one, and does not take into account the overall
        context of the string. For example, the following string:

            <p><strong>Hello</strong> World</p>

        Will be translated in two parts, "Hello" and "World",
        and ideally would be translated as "Hello World".

        I expect the loss off context be a hindrance to the translation service.
        Not sure how to solve this problem. Passing the whole HTML has the risk
        of translating tags and attributes which is undesirable.
        """
        soup = BeautifulSoup(html, "html.parser")

        def walk(soup):
            for child in soup.children:
                if isinstance(child, NavigableString):
                    # Translate navigable strings
                    child.string.replace_with(
                        self.translate_html_string(child.string)
                    )
                else:
                    # Recursively walk the tree
                    walk(child)

        walk(soup)

        self.translate_attributes(soup)
        return str(soup)

    def translate_struct_block(self, item):
        """
        Translate StructBlock,

        Iterates over the child blocks, and calls translate_block on them.
        Uses a helper class `BlockItem` to pass the block and value around.
        """
        for block_type, block in item.block.child_blocks.items():
            block_item = BlockItem(block=block, value=item.value[block_type])
            self.translate_block(block_item)
            item.value[block_type] = block_item.value

    def translate_stream_block(self, item):
        """Translate StreamBlock,

        Slightly redundant, as it only calls translate_blocks with the value.
        But, this keeps the same structure for all iterable block types.
        It allows for customization by overriding this method.
        """
        self.translate_blocks(item.value)

    def translate_list_block(self, item):
        """Translate ListBlock,

        Iterates over the values, and calls translate_block on them.
        Uses a helper class `BlockItem` to pass the block and value around.
        """
        for idx, value in enumerate(item.value):
            block_item = BlockItem(block=item.block.child_block, value=value)
            self.translate_block(block_item)
            item.value[idx] = block_item.value

    def translate_block(self, item) -> None:
        """
        Translate block,

        Receives a block, discovers its type, and translates its value.
        Sets the value on the block.

        Skips the block if it is not translatable. For example, a URLBlock.

        Returns None.
        """
        if isinstance(item.block, (blocks.CharBlock, blocks.TextBlock)):
            item.value = self.translate(item.value)
        elif isinstance(item.block, blocks.RichTextBlock):
            item.value = RichText(self.translate_html(str(item.value)))
        elif isinstance(item.block, blocks.RawHTMLBlock):
            item.value = self.translate_html(item.value)
        elif isinstance(item.block, blocks.StructBlock):
            item.value = self.translate_struct_block(item)
        elif isinstance(item.block, blocks.BlockQuoteBlock):
            item.value = self.translate(item.value)
        elif isinstance(item.block, blocks.ChooserBlock):
            ...  # TODO, implement
        elif isinstance(item.block, blocks.PageChooserBlock):
            ...  # TODO, implement

        # And to recurse, we need to handle iterables.
        elif isinstance(item.block, blocks.StructBlock):
            self.translate_struct_block(item)
        elif isinstance(item.block, blocks.StreamBlock):
            self.translate_stream_block(item)
        elif isinstance(item.block, blocks.ListBlock):
            self.translate_list_block(item)

        else:
            # All other blocks are skipped. Like:
            # URLBlock, BooleanBlock, DateBlock, TimeBlock, DateTimeBlock,
            # ChoiceBlock, MultipleChoiceBlock, EmailBlock, IntegerBlock,
            # FloatBlock, DecimalBlock, RegexBlock, StaticBlock,
            ...

    def translate_blocks(self, items):
        """
        Translate blocks, iterate over the items.

        Expects the item to be an object with block and value attributes.
        Where `block` is any of the wagtail blocks, and `value` the value
        of that block.

        Recurse if the block is an iterable (Streamblock, Listblock, or
        StuctBlock). Recurse takes a de-tour, as it calls a specific
        method for each iterable block type. These specific methods will
        iterate and prepare the data, and call translate_block, which will
        call this method if the block is an iterable block.

        The whole structure is slightly convoluted, but each iterable block
        has its own needs, and this way of working allows to tailor to the needs
        of each block type.

        A method per block type also allows for fine-grained customizations
        by overriding these methods.
        """
        for item in items:
            if isinstance(item.block, blocks.StructBlock):
                self.translate_struct_block(item)
            elif isinstance(item.block, blocks.StreamBlock):
                self.translate_stream_block(item)
            elif isinstance(item.block, blocks.ListBlock):
                self.translate_list_block(item)
            else:
                self.translate_block(item)

        return items

    def translate_obj(self, source_obj, target_obj):
        """
        Translate object,

        Translate a source_obj (model instance).
        Returns the target_obj.

        Note, does not save the target_obj. This is intentional,
        as it allows for greater flexibility.
        """
        for field in get_translatable_fields(target_obj.__class__):
            src = getattr(source_obj, field.name)
            if isinstance(field, RichTextField):
                translation = self.translate_html(src)
            elif isinstance(field, StreamField):
                translation = self.translate_blocks(src)
            else:
                translation = self.translate(src)
            setattr(target_obj, field.name, translation)

        return target_obj
