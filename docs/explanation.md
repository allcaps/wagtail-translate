# Explanation

This document details the concepts underlying Wagtail Translate and explains the reasoning behind its design choices. It aims to enhance and expand your understanding of Wagtail Translation.

## Idea and positioning

[Wagtail Localize](https://wagtail-localize.org/) and [Wagtail Simple Translation](https://docs.wagtail.org/en/stable/reference/contrib/simple_translation.html) are the go-to solutions for multilingual Wagtail projects.
Wagtail Localize offers advanced features that may be excessive for many projects, while Wagtail Simple Translation only copies pages to new locales, requiring manual translation.

**Wagtail Translate** adds machine translations to Wagtail. It works with Simple Translation, providing an ideal solution for projects seeking a straightforward interface with robust translation support.

Your content editors will appreciate the simplicity of Wagtail Translate. 🥳

## Features

- Machine translation
- Integration with OpenAI compatible LLMs including Ollama (local models)
- Integration with DeepL
- Highly customizable

## Architecture

Wagtail Translate operates at the model level. It runs in the background and does not include a user interface.

Wagtail Translate listens for Wagtail's `copy_for_translation_done` signal to initiate the machine translation.

Therefore, Wagtail Translate works well in combination with Wagtail Simple Translation. Simple Translation is a Wagtail Core Contrib module and provides the user interface to copy pages to another locale.

Wagtail Translate is indifferent on what triggers the signal. This could be Simple Translation, other products, or custom code.

## Customizing default behaviors

Wagtail Translate is designed to be flexible, allowing you to tailor its behavior to your needs.

- Provide your own translation service
- Run in sync or hand of to a background workers.
- Define your own signal handler
- Customize the translation process

## Background workers

Wagtail Translate uses external services like DeepL to provide translations. These services can take time, fail to respond, or have downtime.

By default, Wagtail Translate handles translations synchronously, meaning they block the current thread, and the user must wait for all translations to complete. This can negatively impact performance and user experience.

Django's [background workers](https://www.djangoproject.com/weblog/2024/may/29/django-enhancement-proposal-14-background-workers/) are an accepted proposal and are in development. Once available, they will offer a unified way to offload tasks. Wagtail Translate is expected to support them. For now, if you need translations offloaded to a background task, you can customize the default behaviors and implement this yourself.

## Fields to translate

Wagtail Translate introspects the model definition to identify the fields that need translation. You can control which fields are translated by implementing a `get_translatable_fields` method on your model.

## Context and HTMLDocumentCodec

Wagtail Translate encodes the translatable (page/snippet) into an HTML document.
The whole document is submitted to the machine translation service as a whole.
This strategy gives the most context to the translator. For example, a page title is a `h1`. Sign


Wagtail has rich text and raw fields, which may contain HTML. Translating text
nodes separately loses context. For example:

```html
<p>The <em>black</em> cat</p>
```
Translating word-for-word into French yields:
```html
<p>Le <em>noir</em> chat</p>
```
But it should be translated as:
```html
<p>Le chat <em>noir</em></p>
```

Word order can vary across languages, and words may have different meanings depending on the context.
For instance, the word "bow" can refer to a weapon for shooting arrows or a gesture of respect.
In French, these are translated as "arc" and "révérence," respectively.
If translation service has too little context, there is a risk of incorrect translation.

Wagtail Translate instead composes one HTML document for the complete page or
snippet. It uses semantic elements for the title and fields, and nested `div`
elements for StreamField blocks. The translation service therefore sees all
selected content and complete rich-text fragments in one request. This allows
translations such as:

```html
<p>Le chat <em>noir</em></p>
```

The translated document must preserve its elements and temporary reference IDs.
Text can move around inline elements where target-language grammar requires it.

URLs, IDs, classes, styles, data attributes, reference-valued ARIA attributes,
and Wagtail's `linktype`, `embedtype`, and object IDs are replaced with temporary
references. They are restored locally after validation. Existing non-empty
`alt`, `title`, and `aria-label` values remain available for translation.
Technical subtrees such as `script`, `style`, `code`, `pre`, SVG, and MathML stay
local as opaque values.

HTML preservation is DOM-equivalent rather than byte-for-byte. Quote style,
attribute ordering, entity spelling, and insignificant formatting may be
normalized, while element structure and attribute values remain equivalent.

The complete response is validated before any field is applied. A failure leaves
the source untouched and the already-created target copy untranslated. DeepL,
OpenAI-compatible LLMs, ROT13, and custom integrations all use this same document
contract.

DeepL does not document translation of HTML attribute values, so its
translator may leave `alt`, `title`, and `aria-label` untranslated.

## Translation of related objects

For related objects (foreign keys) Wagtail Translate checks if the object is translatable, and if the translations exist.
If the translation exists, it is used; otherwise, the original object is used.

This approach prevents deep traversal as related objects can have related objects of their own.
It also accommodates intentional cross-language references.
For example, a multilingual site might have blogs exclusively in English, requiring links to the English posts regardless of the referencing page's locale.

Since Wagtail Translate can't forsee the intended behavior, it uses the simplest approach:
use if the translation exists, otherwise use the original object.
This  means that sometimes the content editor needs to step in and translate the related object, and select that related object.

To adjust this behavior, override
`HTMLDocumentTranslator.translate_related_object`.
