import copy
from abc import ABC, abstractmethod
from collections import Counter
from dataclasses import dataclass, field
from typing import Literal

from bs4 import (
    BeautifulSoup,
    Comment,
    Declaration,
    Doctype,
    NavigableString,
    ProcessingInstruction,
    Tag,
)
from django.db.models import ForeignKey
from wagtail import blocks
from wagtail.fields import RichTextField, StreamField
from wagtail.images.blocks import ImageBlock
from wagtail.models import TranslatableMixin
from wagtail.rich_text import RichText

from ..fields import get_translatable_fields
from .exceptions import DocumentTranslationValidationError

FieldKind = Literal["text", "rich_text", "stream"]
BlockKind = Literal["text", "rich_text", "raw_html", "container"]


@dataclass(frozen=True)
class FieldBinding:
    field_name: str
    kind: FieldKind


@dataclass(frozen=True)
class BlockPathStep:
    kind: Literal["stream", "list", "struct"]
    key: int | str


@dataclass(frozen=True)
class BlockBinding:
    field_ref: str
    path: tuple[BlockPathStep, ...]
    block_type: str
    kind: BlockKind


@dataclass(frozen=True)
class AttributeBinding:
    tag_name: str
    attributes: dict[str, str | list[str]]


@dataclass(frozen=True)
class OpaqueBinding:
    html: str
    node_type: str


@dataclass
class DecomposedDocument:
    html: str
    fields: dict[str, FieldBinding] = field(default_factory=dict)
    blocks: dict[str, BlockBinding] = field(default_factory=dict)
    attributes: dict[str, AttributeBinding] = field(default_factory=dict)
    opaque_nodes: dict[str, OpaqueBinding] = field(default_factory=dict)


def _rich_text_source(value) -> str:
    if isinstance(value, RichText):
        return value.source
    return str(value)


class HTMLDocumentCodec:
    """Convert a Wagtail object to protected HTML and back again."""

    def __init__(
        self,
        *,
        opaque_html_tags: frozenset[str],
        translatable_html_attributes: frozenset[str],
    ) -> None:
        self.opaque_html_tags = opaque_html_tags
        self.translatable_html_attributes = translatable_html_attributes
        self._field_index = 0
        self._block_index = 0
        self._attribute_index = 0
        self._opaque_index = 0

    def decompose(self, source_obj) -> DecomposedDocument:
        self._field_index = 0
        self._block_index = 0
        self._attribute_index = 0
        self._opaque_index = 0

        document = DecomposedDocument(html="")
        output = BeautifulSoup("", "html.parser")
        root = output.new_tag("main")
        output.append(root)

        for model_field in get_translatable_fields(source_obj.__class__):
            if isinstance(model_field, ForeignKey):
                continue

            value = getattr(source_obj, model_field.name)
            field_ref = f"f{self._field_index}"

            if isinstance(model_field, StreamField):
                wrapper = output.new_tag("div", id=field_ref)
                for index, child in enumerate(value):
                    child_tag = self._decompose_block(
                        output,
                        child.block,
                        child.value,
                        field_ref,
                        (BlockPathStep("stream", index),),
                        child.block_type,
                        document,
                    )
                    if child_tag is not None:
                        wrapper.append(child_tag)
                if not wrapper.contents:
                    continue
                self._field_index += 1
                document.fields[field_ref] = FieldBinding(model_field.name, "stream")
                root.append(wrapper)
                continue

            if isinstance(model_field, RichTextField):
                wrapper = output.new_tag("div", id=field_ref)
                has_content = self._append_html(
                    output, wrapper, _rich_text_source(value), document
                )
                if not has_content:
                    continue
                self._field_index += 1
                document.fields[field_ref] = FieldBinding(model_field.name, "rich_text")
                root.append(wrapper)
                continue

            text = "" if value is None else str(value)
            if not text:
                continue
            self._field_index += 1
            tag_name = "h1" if model_field.name == "title" else "p"
            wrapper = output.new_tag(tag_name, id=field_ref)
            wrapper.append(NavigableString(text))
            document.fields[field_ref] = FieldBinding(model_field.name, "text")
            root.append(wrapper)

        document.html = str(root)
        return document

    def validate(self, document: DecomposedDocument, translated_html: str) -> None:
        source = self._parse_document(document.html)
        translated = self._parse_document(translated_html)

        expected_refs = self._reference_counts(source)
        returned_refs = self._reference_counts(translated)
        duplicates = sorted(ref for ref, count in returned_refs.items() if count > 1)
        if duplicates:
            raise DocumentTranslationValidationError(
                f"Duplicate HTML references: {', '.join(duplicates)}"
            )
        missing = sorted(set(expected_refs) - set(returned_refs))
        if missing:
            raise DocumentTranslationValidationError(
                f"Missing HTML references: {', '.join(missing)}"
            )
        unknown = sorted(set(returned_refs) - set(expected_refs))
        if unknown:
            raise DocumentTranslationValidationError(
                f"Unknown HTML references: {', '.join(unknown)}"
            )

        self._validate_element(source, translated)

    def rehydrate(
        self,
        document: DecomposedDocument,
        translated_html: str,
        source_obj,
        target_obj,
        translate_related_object,
    ):
        self.validate(document, translated_html)
        translated = self._parse_document(translated_html)
        self._restore_preserved_content(translated, document)

        block_bindings = {
            (binding.field_ref, binding.path): ref
            for ref, binding in document.blocks.items()
        }
        translated_fields = {}

        for model_field in get_translatable_fields(source_obj.__class__):
            source_value = getattr(source_obj, model_field.name)

            if isinstance(model_field, ForeignKey):
                translated_fields[model_field.name] = translate_related_object(
                    source_value
                )
                continue

            field_ref = next(
                (
                    ref
                    for ref, binding in document.fields.items()
                    if binding.field_name == model_field.name
                ),
                None,
            )
            if isinstance(model_field, StreamField):
                copied_value = copy.deepcopy(source_value)
                if field_ref is not None:
                    for index, child in enumerate(copied_value):
                        child.value = self._rehydrate_block(
                            child.block,
                            child.value,
                            field_ref,
                            (BlockPathStep("stream", index),),
                            block_bindings,
                            translated,
                            translate_related_object,
                        )
                else:
                    copied_value = self._translate_chooser_blocks(
                        model_field.stream_block,
                        copied_value,
                        translate_related_object,
                    )
                translated_fields[model_field.name] = copied_value
                continue

            if field_ref is None:
                translated_fields[model_field.name] = source_value
                continue

            wrapper = translated.find(id=field_ref)
            if isinstance(model_field, RichTextField):
                translated_fields[model_field.name] = wrapper.decode_contents()
            else:
                translated_fields[model_field.name] = wrapper.get_text()

        for field_name, value in translated_fields.items():
            setattr(target_obj, field_name, value)
        return target_obj

    def _next_block_ref(self) -> str:
        ref = f"b{self._block_index}"
        self._block_index += 1
        return ref

    def _next_attribute_ref(self) -> str:
        ref = f"a{self._attribute_index}"
        self._attribute_index += 1
        return ref

    def _next_opaque_ref(self) -> str:
        ref = f"x{self._opaque_index}"
        self._opaque_index += 1
        return ref

    def _append_html(
        self,
        output: BeautifulSoup,
        parent: Tag,
        html: str,
        document: DecomposedDocument,
    ) -> bool:
        source = BeautifulSoup(html, "html.parser")
        has_content = False
        for child in source.contents:
            cloned, child_has_content = self._clone_html_node(output, child, document)
            parent.append(cloned)
            has_content = has_content or child_has_content
        return has_content

    def _clone_html_node(
        self,
        output: BeautifulSoup,
        node,
        document: DecomposedDocument,
    ) -> tuple[Tag | NavigableString, bool]:
        special_types = (Comment, Declaration, Doctype, ProcessingInstruction)
        if isinstance(node, special_types):
            ref = self._next_opaque_ref()
            document.opaque_nodes[ref] = OpaqueBinding(
                html=str(node),
                node_type=type(node).__name__,
            )
            placeholder = output.new_tag("span", id=ref)
            return placeholder, False

        if not isinstance(node, Tag):
            text = str(node)
            return NavigableString(text), bool(text.strip())

        if node.name in self.opaque_html_tags:
            ref = self._next_opaque_ref()
            document.opaque_nodes[ref] = OpaqueBinding(
                html=str(node),
                node_type="Tag",
            )
            placeholder = output.new_tag(node.name, id=ref)
            return placeholder, False

        protected_attributes = {}
        visible_attributes = {}
        for name, value in node.attrs.items():
            if name in self.translatable_html_attributes and str(value):
                visible_attributes[name] = copy.deepcopy(value)
            else:
                protected_attributes[name] = copy.deepcopy(value)

        cloned = output.new_tag(node.name)
        if protected_attributes:
            ref = self._next_attribute_ref()
            document.attributes[ref] = AttributeBinding(
                tag_name=node.name,
                attributes=protected_attributes,
            )
            cloned["id"] = ref
        for name, value in visible_attributes.items():
            cloned[name] = value

        has_content = bool(visible_attributes)
        for child in node.contents:
            cloned_child, child_has_content = self._clone_html_node(
                output, child, document
            )
            cloned.append(cloned_child)
            has_content = has_content or child_has_content
        return cloned, has_content

    def _decompose_block(
        self,
        output: BeautifulSoup,
        block,
        value,
        field_ref: str,
        path: tuple[BlockPathStep, ...],
        block_type: str,
        document: DecomposedDocument,
    ) -> Tag | None:
        wrapper = output.new_tag("div")
        kind: BlockKind

        if isinstance(block, blocks.RichTextBlock):
            if not self._append_html(
                output, wrapper, _rich_text_source(value), document
            ):
                return None
            kind = "rich_text"
        elif isinstance(block, blocks.RawHTMLBlock):
            if not self._append_html(output, wrapper, str(value), document):
                return None
            kind = "raw_html"
        elif isinstance(
            block, (blocks.CharBlock, blocks.TextBlock, blocks.BlockQuoteBlock)
        ):
            text = "" if value is None else str(value)
            if not text:
                return None
            wrapper.append(NavigableString(text))
            kind = "text"
        elif isinstance(block, ImageBlock):
            child = self._decompose_block(
                output,
                block.child_blocks["alt_text"],
                value.contextual_alt_text if value else "",
                field_ref,
                path + (BlockPathStep("struct", "alt_text"),),
                "alt_text",
                document,
            )
            if child is None:
                return None
            wrapper.append(child)
            kind = "container"
        elif isinstance(block, blocks.StructBlock):
            for name, child_block in block.child_blocks.items():
                child = self._decompose_block(
                    output,
                    child_block,
                    value[name],
                    field_ref,
                    path + (BlockPathStep("struct", name),),
                    name,
                    document,
                )
                if child is not None:
                    wrapper.append(child)
            if not wrapper.contents:
                return None
            kind = "container"
        elif isinstance(block, blocks.StreamBlock):
            for index, child_value in enumerate(value):
                child = self._decompose_block(
                    output,
                    child_value.block,
                    child_value.value,
                    field_ref,
                    path + (BlockPathStep("stream", index),),
                    child_value.block_type,
                    document,
                )
                if child is not None:
                    wrapper.append(child)
            if not wrapper.contents:
                return None
            kind = "container"
        elif isinstance(block, blocks.ListBlock):
            for index, child_value in enumerate(value):
                child = self._decompose_block(
                    output,
                    block.child_block,
                    child_value,
                    field_ref,
                    path + (BlockPathStep("list", index),),
                    "item",
                    document,
                )
                if child is not None:
                    wrapper.append(child)
            if not wrapper.contents:
                return None
            kind = "container"
        else:
            return None

        ref = self._next_block_ref()
        wrapper["id"] = ref
        document.blocks[ref] = BlockBinding(
            field_ref=field_ref,
            path=path,
            block_type=block_type,
            kind=kind,
        )
        return wrapper

    def _parse_document(self, html: str) -> Tag:
        """Return one translation root while tolerating response wrappers.

        Providers may surround HTML with Markdown fences, commentary, or document
        elements. Ignore that outer content, but reject missing or multiple main
        elements because the translated document would be absent or ambiguous.
        """
        soup = BeautifulSoup(html, "html.parser")
        mains = soup.find_all("main", limit=2)
        if len(mains) != 1:
            raise DocumentTranslationValidationError(
                "Translated HTML must contain exactly one main element"
            )
        return mains[0]

    def _reference_counts(self, root: Tag) -> Counter:
        return Counter(
            tag["id"]
            for tag in root.find_all(True)
            if isinstance(tag.get("id"), str) and tag["id"][:1] in {"f", "b", "a", "x"}
        )

    def _validate_element(self, source: Tag, translated: Tag) -> None:
        if source.name != translated.name:
            raise DocumentTranslationValidationError(
                "Translated HTML changed an element tag"
            )
        if set(source.attrs) != set(translated.attrs):
            raise DocumentTranslationValidationError(
                "Translated HTML changed element attributes"
            )
        for name, value in source.attrs.items():
            if name == "id" and translated.attrs[name] != value:
                raise DocumentTranslationValidationError(
                    "Translated HTML moved or changed a reference"
                )
            if (
                name not in self.translatable_html_attributes
                and name != "id"
                and translated.attrs[name] != value
            ):
                raise DocumentTranslationValidationError(
                    "Translated HTML changed a protected attribute"
                )

        source_children = [child for child in source.children if isinstance(child, Tag)]
        translated_children = [
            child for child in translated.children if isinstance(child, Tag)
        ]
        if len(source_children) != len(translated_children):
            raise DocumentTranslationValidationError(
                "Translated HTML changed the element structure"
            )
        if any(
            isinstance(child, (Comment, Declaration, Doctype, ProcessingInstruction))
            for child in translated.children
        ):
            raise DocumentTranslationValidationError(
                "Translated HTML introduced an unsupported node"
            )
        for source_child, translated_child in zip(
            source_children, translated_children, strict=True
        ):
            self._validate_element(source_child, translated_child)

    def _restore_preserved_content(
        self, root: Tag, document: DecomposedDocument
    ) -> None:
        for ref, binding in document.attributes.items():
            tag = root.find(id=ref)
            translated_attributes = {
                name: copy.deepcopy(value)
                for name, value in tag.attrs.items()
                if name in self.translatable_html_attributes
            }
            tag.attrs = copy.deepcopy(binding.attributes)
            tag.attrs.update(translated_attributes)

        for ref, binding in document.opaque_nodes.items():
            placeholder = root.find(id=ref)
            node_types = {
                "Comment": Comment,
                "Declaration": Declaration,
                "Doctype": Doctype,
                "ProcessingInstruction": ProcessingInstruction,
            }
            if binding.node_type in node_types:
                placeholder.replace_with(node_types[binding.node_type](binding.html))
                continue
            fragment = BeautifulSoup(binding.html, "html.parser")
            replacement_nodes = list(fragment.contents)
            if not replacement_nodes:
                placeholder.decompose()
                continue
            first = replacement_nodes[0]
            placeholder.replace_with(first)
            for node in replacement_nodes[1:]:
                first.insert_after(node)
                first = node

    def _rehydrate_block(
        self,
        block,
        value,
        field_ref: str,
        path: tuple[BlockPathStep, ...],
        bindings: dict[tuple[str, tuple[BlockPathStep, ...]], str],
        root: Tag,
        translate_related_object,
    ):
        ref = bindings.get((field_ref, path))
        wrapper = root.find(id=ref) if ref is not None else None

        if isinstance(block, blocks.RichTextBlock):
            return RichText(wrapper.decode_contents()) if wrapper is not None else value
        if isinstance(block, blocks.RawHTMLBlock):
            return wrapper.decode_contents() if wrapper is not None else value
        if isinstance(
            block, (blocks.CharBlock, blocks.TextBlock, blocks.BlockQuoteBlock)
        ):
            return wrapper.get_text() if wrapper is not None else value
        if isinstance(block, ImageBlock):
            if value:
                value.contextual_alt_text = self._rehydrate_block(
                    block.child_blocks["alt_text"],
                    value.contextual_alt_text,
                    field_ref,
                    path + (BlockPathStep("struct", "alt_text"),),
                    bindings,
                    root,
                    translate_related_object,
                )
            return value
        if isinstance(block, blocks.StructBlock):
            for name, child_block in block.child_blocks.items():
                value[name] = self._rehydrate_block(
                    child_block,
                    value[name],
                    field_ref,
                    path + (BlockPathStep("struct", name),),
                    bindings,
                    root,
                    translate_related_object,
                )
            return value
        if isinstance(block, blocks.StreamBlock):
            for index, child in enumerate(value):
                child.value = self._rehydrate_block(
                    child.block,
                    child.value,
                    field_ref,
                    path + (BlockPathStep("stream", index),),
                    bindings,
                    root,
                    translate_related_object,
                )
            return value
        if isinstance(block, blocks.ListBlock):
            for index, child_value in enumerate(value):
                value[index] = self._rehydrate_block(
                    block.child_block,
                    child_value,
                    field_ref,
                    path + (BlockPathStep("list", index),),
                    bindings,
                    root,
                    translate_related_object,
                )
            return value
        if isinstance(block, blocks.ChooserBlock):
            return translate_related_object(value)
        return value

    def _translate_chooser_blocks(self, block, value, translate_related_object):
        if isinstance(block, ImageBlock):
            return value
        if isinstance(block, blocks.StructBlock):
            for name, child_block in block.child_blocks.items():
                value[name] = self._translate_chooser_blocks(
                    child_block, value[name], translate_related_object
                )
        elif isinstance(block, blocks.StreamBlock):
            for child in value:
                child.value = self._translate_chooser_blocks(
                    child.block, child.value, translate_related_object
                )
        elif isinstance(block, blocks.ListBlock):
            for index, child_value in enumerate(value):
                value[index] = self._translate_chooser_blocks(
                    block.child_block, child_value, translate_related_object
                )
        elif isinstance(block, blocks.ChooserBlock):
            return translate_related_object(value)
        return value


class HTMLDocumentTranslator(ABC):
    """Translate one protected HTML document per Wagtail object."""

    opaque_html_tags = frozenset(
        {"code", "math", "pre", "script", "style", "svg", "template"}
    )
    translatable_html_attributes = frozenset({"alt", "title", "aria-label"})

    def __init__(self, source_language_code: str, target_language_code: str) -> None:
        self.source_language_code = source_language_code
        self.target_language_code = target_language_code
        self.codec = HTMLDocumentCodec(
            opaque_html_tags=self.opaque_html_tags,
            translatable_html_attributes=self.translatable_html_attributes,
        )

    @abstractmethod
    def translate_document_html(self, html: str) -> str:
        """Translate a complete protected HTML document."""

    def translate_related_object(self, value):
        if not isinstance(value, TranslatableMixin):
            return value
        translation = (
            value.get_translations()
            .filter(locale__language_code=self.target_language_code)
            .first()
        )
        return translation or value

    def translate_obj(self, source_obj, target_obj):
        document = self.codec.decompose(source_obj)
        translated_html = document.html
        if document.fields:
            translated_html = self.translate_document_html(document.html)
        return self.codec.rehydrate(
            document,
            translated_html,
            source_obj,
            target_obj,
            self.translate_related_object,
        )
