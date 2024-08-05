# Author: Felix Fontein <felix@fontein.de>
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or
# https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: 2024, Ansible Project

"""
Code for conversion to MarkDown.
"""

from __future__ import annotations

import io
import re
import typing as t
from html import escape as _html_escape
from urllib.parse import quote as _urllib_quote

from docutils import nodes, writers
from docutils.core import publish_parts
from docutils.writers.html5_polyglot import HTMLTranslator
from docutils.writers.html5_polyglot import Writer as HTMLWriter

from .utils import RenderResult, SupportedParser, get_docutils_publish_settings

_MD_ESCAPE = re.compile(r"""([!"#$%&'()*+,:;<=>?@[\\\]^_`{|}~.-])""")


def md_escape(text: str) -> str:
    """
    Escape a text for MarkDown.
    """
    return _MD_ESCAPE.sub(r"\\\1", text)


def html_escape(text: str) -> str:
    """
    Escape a text for HTML.
    """
    return _html_escape(text).replace("&quot;", '"')


class GlobalContext:
    """
    The global conversion context.
    """

    # How labels are mapped to link fragments
    labels: dict[str, str]

    fragments: set[str]

    def __init__(self):
        self.labels = {}
        self.fragments = set()

    def register_label(self, label: str) -> str:
        """
        Register a label. Produces the corresponding link fragment.
        """
        if label in self.labels:
            return self.labels[label]
        fragment = _urllib_quote(label, safe="")
        self.labels[label] = fragment
        self.fragments.add(fragment)
        return fragment

    def register_new_fragment(self, fragment: str) -> str:
        """
        Register a new fragment.

        If it already exists, will be modified until a new one is found.
        """
        counter = 0
        appendix = ""
        while (full_fragment := f"{fragment}{appendix}") in self.fragments:
            counter += 1
            appendix = f"-{counter}"
        self.fragments.add(full_fragment)
        return full_fragment


class Context:
    """
    Base context class for MarkDown conversion.
    """

    escape: bool

    _has_top: bool

    _top: list[str]
    _main: list[str]

    def __init__(self, has_top=False, escape=True):
        self.escape = escape
        self._has_top = has_top
        self._top = []
        self._main = []

    def add_top(self, text: str) -> None:
        """
        Add text to the top part.
        """
        if not self._has_top:
            raise ValueError("Context has no top part")
        self._top.append(text)

    def add_main(self, text: str) -> None:
        """
        Add text to the main part.
        """
        self._main.append(text)

    def replace_main(self, lines: list[str] | None = None) -> None:
        """
        Replace the content of the main part by the new list of strings.
        """
        self._main.clear()
        if lines:
            self._main.extend(lines)

    def ensure_newline(self) -> None:
        """
        Ensure that the main part ends with a newline, if it is not empty.
        """
        if self._main and not self._main[-1].endswith("\n"):
            self._main.append("\n")

    def ensure_double_newline(self) -> None:
        """
        Ensure that the main part ends with two newlines, if it is not empty.
        """
        if self._main:
            last = "".join(self._main[-2:])
            if not last.endswith("\n\n"):
                if last.endswith("\n"):
                    self._main.append("\n")
                else:
                    self._main.append("\n\n")

    def append(
        self,
        context: "Context",
    ) -> None:
        """
        Append another context to this context.
        """
        if context._has_top:  # pylint: disable=protected-access
            if not self._has_top:
                raise ValueError("Context has no top part")
            self._top.extend(context._top)  # pylint: disable=protected-access
        self._main.extend(context._main)  # pylint: disable=protected-access

    def close(self) -> None:
        """
        Close the context.

        Should be called before using its value / content, for example by
        passing it to ``append()`` or calling ``get_text()``.
        """

    def get_text(self) -> str:
        """
        Return the content of the context as a string.
        """
        return "".join(self._top + self._main)


class ListContext(Context):
    """
    Context for lists (enumeration, bullet list).
    """

    first_indent: str
    next_indent: str

    def __init__(self, indent: str):
        super().__init__()
        self.first_indent = indent
        self.next_indent = " " * len(indent)


def get_language_from_literal_block(node: nodes.literal_block) -> str | None:
    """
    Obtain programming language from a literal block.
    """
    # Some versions store the language in the "language" attribute
    if "language" in node.attributes:
        return node.attributes["language"]
    # Some others simply store it as a class name that's not "code" or "code-block"
    for class_name in node.attributes["classes"]:
        if class_name not in ("code", "code-block"):
            return class_name
    return None


def count_leading_backticks(line: str) -> int:
    """
    Count the number of leading backticks of a string.
    """
    count = 0
    length = len(line)
    while count < length and line[count] == "`":
        count += 1
    return count


class DocumentContext:
    """
    Conversion context for a document.
    """

    section_depth: int
    global_context: GlobalContext
    unknown_node_types: set[str]
    created_labels: set[str]

    _contexts: list[Context]

    def __init__(self, global_context: GlobalContext):
        self.section_depth = 0
        self.global_context = global_context
        self.unknown_node_types = set()
        self.created_labels = set()
        self._contexts = [Context(has_top=True)]

    def push_context(self, context: Context) -> None:
        """
        Add a new context on the context stack.
        """
        self._contexts.append(context)

    def pop_context(self) -> None:
        """
        Pop the top-most context from the context stack.

        The last context cannot be popped, trying to do so will result in a
        ``ValueError`` exception.
        """
        if len(self._contexts) < 2:
            raise ValueError("Cannot pop last element")
        context = self._contexts.pop()
        context.close()
        self._contexts[-1].append(context)

    @property
    def top(self) -> Context:
        """
        Return the top-most context from the context stack.
        """
        return self._contexts[-1]


_Class = t.TypeVar("_Class")


def _add_unsupported_classes(clazz: _Class) -> _Class:
    def get_visit(class_name: str):
        # pylint: disable-next=unused-argument
        def visit_unsupported(self: t.Any, node: nodes.Node):
            # pylint: disable-next=protected-access
            self._context.unknown_node_types.add(class_name)
            raise nodes.SkipNode

        return visit_unsupported

    for class_name in nodes.node_class_names:
        function_name = f"visit_{class_name}"
        if not hasattr(clazz, function_name):
            setattr(clazz, function_name, get_visit(class_name))

    return clazz


def _add_simple(
    definitions: dict[str, tuple[str, str]]
) -> t.Callable[[_Class], _Class]:
    def decorator(clazz: _Class) -> _Class:
        def get_visit(start: str):
            # pylint: disable-next=unused-argument
            def visit(self: t.Any, node: nodes.Node) -> None:
                if start:
                    # pylint: disable-next=protected-access
                    self._context.top.add_main(start)

            return visit

        def get_depart(end: str):
            # pylint: disable-next=unused-argument
            def depart(self: t.Any, node: nodes.Node) -> None:
                if end:
                    # pylint: disable-next=protected-access
                    self._context.top.add_main(end)

            return depart

        for class_name, (start, end) in definitions.items():
            setattr(clazz, f"visit_{class_name}", get_visit(start))
            setattr(clazz, f"depart_{class_name}", get_depart(end))
        return clazz

    return decorator


def _add_skip(class_names: list[str]) -> t.Callable[[_Class], _Class]:
    def decorator(clazz: _Class) -> _Class:
        def visit(self: t.Any, node: nodes.Node) -> None:
            raise nodes.SkipNode

        for class_name in class_names:
            setattr(clazz, f"visit_{class_name}", visit)
        return clazz

    return decorator


@_add_unsupported_classes
@_add_simple(
    {
        "document": ("", ""),
        "inline": ("", ""),
        "generated": ("", ""),
        "literal": ("<code>", "</code>"),
        "emphasis": ("<em>", "</em>"),
        "strong": ("<strong>", "</strong>"),
        "subscript": ("<sub>", "</sub>"),
        "superscript": ("<sup>", "</sup>"),
    }
)
@_add_skip(
    [
        "comment",
    ]
)
class Translator(nodes.NodeVisitor):  # pylint: disable=too-many-public-methods
    """
    Translates a docutils node tree to MarkDown in a ``DocumentContext``.
    """

    _context: DocumentContext

    def __init__(self, document, document_context: DocumentContext):
        super().__init__(document)
        self._context = document_context

    def get_text(self) -> str:
        """
        Return the result as a text.

        Must only be called after processing the document, and at most once.
        """
        context = self._context.top
        context.close()
        return context.get_text().lstrip("\n").rstrip("\n")

    def _add_label(self, label: str) -> None:
        if label in self._context.created_labels:
            return
        self._context.created_labels.add(label)
        ref = self._context.global_context.register_label(label)
        self._context.top.add_main(f'<a id="{ref}"></a>\n')

    # Node: paragraph

    # pylint: disable-next=missing-function-docstring,unused-argument
    def visit_paragraph(self, node: nodes.section) -> None:
        self._context.top.ensure_double_newline()

    # pylint: disable-next=missing-function-docstring,unused-argument
    def depart_paragraph(self, node: nodes.section) -> None:
        self._context.top.ensure_double_newline()

    # Node: title

    # pylint: disable-next=missing-function-docstring
    def visit_title(self, node: nodes.title) -> None:
        level = self._context.section_depth + 1
        title = node.astext()
        text = f'{"#" * level} {md_escape(title)}\n\n'
        if self._context.section_depth == 0:
            self._context.top.add_top(text)
        else:
            self._context.top.ensure_newline()
            self._context.top.add_main(text)
        raise nodes.SkipNode

    # Node: section

    # pylint: disable-next=missing-function-docstring
    def visit_section(self, node: nodes.section) -> None:
        self._context.top.ensure_double_newline()
        if "ids" in node.attributes:
            for ref in node.attributes["ids"]:
                self._add_label(ref)
        self._context.section_depth += 1

    # pylint: disable-next=missing-function-docstring,unused-argument
    def depart_section(self, node: nodes.section) -> None:
        self._context.section_depth -= 1

    # Node: text

    # pylint: disable-next=missing-function-docstring,invalid-name
    def visit_Text(self, node: nodes.Text) -> None:
        text = node.astext()
        if self._context.top.escape:
            text = md_escape(text)
        self._context.top.add_main(text)

    # pylint: disable-next=missing-function-docstring,invalid-name
    def depart_Text(self, node: nodes.Text) -> None:
        pass

    # Node: target

    # pylint: disable-next=missing-function-docstring
    def visit_target(self, node: nodes.target) -> None:
        if "refid" in node.attributes:
            self._add_label(node.attributes["refid"])

    # pylint: disable-next=missing-function-docstring
    def depart_target(self, node: nodes.target) -> None:
        pass

    # Node: reference

    # pylint: disable-next=missing-function-docstring,unused-argument
    def visit_reference(self, node: nodes.reference) -> None:
        self._context.top.add_main("[")

    # pylint: disable-next=missing-function-docstring
    def depart_reference(self, node: nodes.reference) -> None:
        name: str
        ref: str
        if "refuri" in node.attributes:
            ref = node.attributes["refuri"]
            name = node.attributes.get("name") or "link"
        elif "refid" in node.attributes:
            ref = node.attributes["refid"]
            name = "reference"
        else:
            # docutils fails an assertion at this point
            raise ValueError(
                f"Do not know how to handle reference with attributes {node.attributes!r}"
            )
        if name == "reference":
            ref = self._context.global_context.register_label(ref)
            ref = f"#{ref}"
        self._context.top.add_main(f"]({md_escape(ref)})")

    # Node: bullet_list

    # pylint: disable-next=missing-function-docstring,unused-argument
    def visit_bullet_list(self, node: nodes.bullet_list) -> None:
        self._context.top.ensure_double_newline()
        self._context.push_context(ListContext("- "))

    # pylint: disable-next=missing-function-docstring,unused-argument
    def depart_bullet_list(self, node: nodes.bullet_list) -> None:
        self._context.pop_context()

    # Node: enumerated_list

    # pylint: disable-next=missing-function-docstring,unused-argument
    def visit_enumerated_list(self, node: nodes.enumerated_list) -> None:
        self._context.top.ensure_double_newline()
        self._context.push_context(ListContext("1. "))

    # pylint: disable-next=missing-function-docstring,unused-argument
    def depart_enumerated_list(self, node: nodes.enumerated_list) -> None:
        self._context.pop_context()

    # Node: list_item

    # pylint: disable-next=missing-function-docstring,unused-argument
    def visit_list_item(self, node: nodes.list_item) -> None:
        list_context = t.cast(ListContext, self._context.top)

        class ListItemContext(Context):
            """
            Context for a list item.
            """

            def close(self) -> None:
                text = self.get_text().strip("\n")
                self.replace_main()
                indent = list_context.first_indent
                for i, line in enumerate(text.splitlines()):
                    if i and not line.rstrip(" "):
                        self.add_main("\n")
                    else:
                        self.add_main(f"{indent}{line}\n")
                    indent = list_context.next_indent
                if not self._main:
                    self.add_main(f"{indent}\\ \n")

        self._context.push_context(ListItemContext())

    # pylint: disable-next=missing-function-docstring,unused-argument
    def depart_list_item(self, node: nodes.list_item) -> None:
        self._context.pop_context()

    # Node: literal_block

    # pylint: disable-next=missing-function-docstring
    def visit_literal_block(self, node: nodes.literal_block) -> None:
        self._context.top.ensure_newline()
        language = get_language_from_literal_block(node)

        class LiteralContext(Context):
            """
            Context for a literal block.
            """

            def __init__(self):
                super().__init__(escape=False)

            def close(self) -> None:
                self.ensure_newline()
                text = self.get_text()
                backticks_needed = "```"
                for line in text.splitlines():
                    if line.startswith(backticks_needed):
                        backticks_needed = "`" * (count_leading_backticks(line) + 1)
                self.replace_main(
                    [
                        f'{backticks_needed}{language or ""}\n',
                        text,
                        f"{backticks_needed}\n",
                    ]
                )

        self._context.push_context(LiteralContext())

    # pylint: disable-next=missing-function-docstring,unused-argument
    def depart_literal_block(self, node: nodes.literal_block) -> None:
        self._context.pop_context()

    # Node: block_quote

    # pylint: disable-next=missing-function-docstring,unused-argument
    def visit_block_quote(self, node: nodes.block_quote) -> None:
        class BlockQuoteContext(Context):
            """
            Context for a block quote.
            """

            def close(self) -> None:
                self.ensure_newline()
                lines = self.get_text().rstrip("\n").splitlines()
                self.replace_main(
                    [(f"> {line}\n" if line else ">\n") for line in lines]
                )

        self._context.push_context(BlockQuoteContext())

    # pylint: disable-next=missing-function-docstring,unused-argument
    def depart_block_quote(self, node: nodes.block_quote) -> None:
        self._context.pop_context()

    # Node: system_message

    # pylint: disable-next=missing-function-docstring
    def visit_system_message(self, node: nodes.system_message) -> None:
        self._context.top.ensure_double_newline()
        self._context.top.add_main("<details>\n")
        message_type = html_escape(node["type"])
        message_level = node["level"]
        source = node["source"]
        if node.hasattr("line"):
            source = f'{source}, line {node["line"]}'
        source = html_escape(source)
        self._context.top.add_main(
            f"<summary><strong>{message_type}/{message_level}</strong> ({source})</summary>\n\n"
        )

    # pylint: disable-next=missing-function-docstring,unused-argument
    def depart_system_message(self, node: nodes.system_message) -> None:
        self._context.top.ensure_double_newline()
        self._context.top.add_main("</details>\n\n")

    # Node: system_message

    # pylint: disable-next=missing-function-docstring,unused-argument
    def visit_note(self, node: nodes.note) -> None:
        class NoteContext(Context):
            """
            Context for a note.
            """

            def close(self) -> None:
                self.ensure_double_newline()
                lines = self.get_text().rstrip("\n").splitlines()
                # See https://github.com/orgs/community/discussions/16925 for the syntax
                self.replace_main(["> [!NOTE]\n"] + [f"> {line}\n" for line in lines])

        self._context.push_context(NoteContext())

    # pylint: disable-next=missing-function-docstring,unused-argument
    def depart_note(self, node: nodes.note) -> None:
        self._context.pop_context()

    # Node: topic

    # pylint: disable-next=missing-function-docstring,unused-argument
    def visit_topic(self, node: nodes.topic) -> None:
        # The main use of <topic> elements is for Table of Contents
        class TopicContext(Context):
            """
            Context for a topic.
            """

        self._context.section_depth += 1
        self._context.push_context(TopicContext())

    # pylint: disable-next=missing-function-docstring,unused-argument
    def depart_topic(self, node: nodes.topic) -> None:
        self._context.pop_context()
        self._context.section_depth -= 1

    # Node: image

    # pylint: disable-next=missing-function-docstring
    def visit_image(self, node: nodes.image) -> None:
        self._context.top.ensure_newline()
        alt = node.attributes.get("alt") or ""
        uri = node.attributes["uri"]
        width = node.attributes.get("width")
        height = node.attributes.get("height")
        if width is not None or height is not None:
            # We can only handle width and height with a HTML <img> tag
            attributes = []
            if alt:
                attributes.append(f'alt="{html_escape(alt)}"')
            if width:
                attributes.append(f'width="{html_escape(str(width))}"')
            if height:
                attributes.append(f'height="{html_escape(str(height))}"')
            self._context.top.add_main(
                f'<img src="{html_escape(uri)}" {" ".join(attributes)}>\n'
            )
        else:
            self._context.top.add_main(f"![{md_escape(alt)}]({md_escape(uri)})\n")
        raise nodes.SkipNode

    # Node: transition

    # pylint: disable-next=missing-function-docstring,unused-argument
    def visit_transition(self, node: nodes.transition) -> None:
        self._context.top.ensure_double_newline()
        self._context.top.add_main("---\n\n")
        raise nodes.SkipNode

    # Node: title_reference

    # pylint: disable-next=missing-function-docstring,unused-argument
    def visit_title_reference(self, node: nodes.title_reference) -> None:
        # This usually happens if someone uses single backticks instead of double backticks
        self._context.top.add_main('<em class="title-reference">')

    # pylint: disable-next=missing-function-docstring,unused-argument
    def depart_title_reference(self, node: nodes.title_reference) -> None:
        self._context.top.add_main("</em>")

    # Node: problematic

    # pylint: disable-next=missing-function-docstring
    def visit_problematic(self, node):
        if "refid" in node.attributes:
            self._context.top.add_main(
                f'<a href="#{html_escape(node.attributes["refid"])}">'
            )
        self._context.top.add_main('<span class="problematic">')

    # pylint: disable-next=missing-function-docstring
    def depart_problematic(self, node):
        self._context.top.add_main("</span>")
        if "refid" in node.attributes:
            self._context.top.add_main("</a>")

    # Node: problematic

    # pylint: disable-next=missing-function-docstring
    def visit_table(self, node):
        translator = HTMLTranslator(self.document)
        node.walkabout(translator)
        self._context.top.add_main("".join(translator.body).strip())
        raise nodes.SkipNode


class MarkDownWriter(writers.Writer):
    """
    Create a MarkDown document from a docutils node tree.
    """

    # Needed to be able to run HTMLTranslator on nodes
    settings_spec = HTMLWriter.settings_spec

    def __init__(self, document_context: DocumentContext):
        writers.Writer.__init__(self)
        self.document_context = document_context
        self.translator_class = Translator

    def translate(self) -> None:
        """
        Translate the document node tree to MarkDown.
        """
        translator = self.translator_class(self.document, self.document_context)
        self.document.walkabout(translator)
        self.output = translator.get_text()


def render_as_markdown(
    source: str,
    /,
    parser_name: SupportedParser,
    global_context: GlobalContext | None = None,
    source_path: str | None = None,
    destination_path: str | None = None,
) -> RenderResult:
    """
    Render the document as MarkDown.
    """
    if global_context is None:
        global_context = GlobalContext()
    document_context = DocumentContext(global_context)
    warnings_stream = io.StringIO()
    parts = publish_parts(
        source=source,
        source_path=source_path,
        destination_path=destination_path,
        parser_name=parser_name,
        writer=MarkDownWriter(document_context),
        settings_overrides=get_docutils_publish_settings(warnings_stream),
    )
    return RenderResult(
        parts["whole"],
        document_context.unknown_node_types,
        warnings_stream.getvalue().splitlines(),
    )


__all__ = ("GlobalContext", "render_as_markdown")
