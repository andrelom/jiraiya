import logging

from enum import Enum
from typing import Dict, Any, List, Callable, Optional


logging.basicConfig(level=logging.WARNING)

class NodeType(Enum):
    BLOCKQUOTE = "blockquote"
    BULLET_LIST = "bulletList"
    CODE_BLOCK = "codeBlock"
    DECISION_ITEM = "decisionItem"
    DECISION_LIST = "decisionList"
    EMOJI = "emoji"
    EXPAND = "expand"
    EXTENSION = "extension"
    HEADING = "heading"
    INLINE_CARD = "inlineCard"
    INLINE_EXTENSION = "inlineExtension"
    LAYOUT_COLUMN = "layoutColumn"
    LAYOUT_SECTION = "layoutSection"
    LIST_ITEM = "listItem"
    MEDIA_GROUP = "mediaGroup"
    MEDIA_INLINE = "mediaInline"
    MEDIA_SINGLE = "mediaSingle"
    MENTION = "mention"
    NESTED_EXPAND = "nestedExpand"
    ORDERED_LIST = "orderedList"
    PANEL = "panel"
    PARAGRAPH = "paragraph"
    RULE = "rule"
    STATUS = "status"
    TABLE = "table"
    TASK_ITEM = "taskItem"
    TASK_LIST = "taskList"
    TEXT = "text"
    UNSUPPORTED_BLOCK = "unsupportedBlock"
    UNSUPPORTED_INLINE = "unsupportedInline"

class ADFToMarkdownConverter:
    """
    A class to convert Atlassian Document Format (ADF) JSON to Markdown.
    """

    def __init__(self, adf_json: Dict[str, Any], custom_renderers: Optional[Dict[str, Callable]] = None) -> None:
        self.adf_json = adf_json
        self.custom_renderers = custom_renderers or {}

    def parse_node(self, node: Dict[str, Any]) -> str:
        """
        Recursively parse a node from the ADF structure and convert it to Markdown.
        """
        try:
            node_type = node.get("type")
            content = node.get("content", [])

            if node_type in self.custom_renderers:
                return self.custom_renderers[node_type](node)

            handlers = {
                NodeType.PARAGRAPH.value: lambda: self.parse_paragraph(content),
                NodeType.HEADING.value: lambda: self.parse_heading(node),
                NodeType.ORDERED_LIST.value: lambda: self.parse_list(content, ordered=True),
                NodeType.BULLET_LIST.value: lambda: self.parse_list(content, ordered=False),
                NodeType.LIST_ITEM.value: lambda: self.parse_paragraph(content),
                NodeType.TEXT.value: lambda: self.parse_text(node),
                NodeType.MEDIA_SINGLE.value: lambda: self.parse_media(node),
                NodeType.INLINE_CARD.value: lambda: self.parse_inline_card(node),
                NodeType.BLOCKQUOTE.value: lambda: f"> {self.parse_paragraph(content)}",
                NodeType.RULE.value: lambda: "---",
                NodeType.MEDIA_INLINE.value: lambda: self.parse_media(node),
                NodeType.EMOJI.value: lambda: node.get("attrs", {}).get("text", ""),
                NodeType.MENTION.value: lambda: f"@{node.get('attrs', {}).get('text', '')}",
                NodeType.STATUS.value: lambda: f"[{node.get('attrs', {}).get('text', '')}]",
                NodeType.CODE_BLOCK.value: lambda: self.parse_code_block(node, content),
                NodeType.PANEL.value: lambda: f"> **Panel:** {self.parse_paragraph(content)}",
                NodeType.EXPAND.value: lambda: self.parse_expand(node, content),
                NodeType.TABLE.value: lambda: self.parse_table(content),
                NodeType.TASK_LIST.value: lambda: self.parse_task_list(content),
                NodeType.TASK_ITEM.value: lambda: self.parse_task_item(node),
                NodeType.UNSUPPORTED_BLOCK.value: lambda: "<!-- Unsupported block content -->",
                NodeType.UNSUPPORTED_INLINE.value: lambda: "<!-- Unsupported inline content -->",
            }

            return handlers.get(node_type, lambda: f"<!-- Unsupported node type: {node_type} -->")()
        except Exception as e:
            logging.error(f"Error parsing node: {e}")
            return f"<!-- Error parsing node: {e} -->"

    def parse_code_block(self, node: Dict[str, Any], content: List[Dict[str, Any]]) -> str:
        language = node.get("attrs", {}).get("language", "")
        return f"```{language}\n{self.parse_paragraph(content)}\n```"

    def parse_expand(self, node: Dict[str, Any], content: List[Dict[str, Any]]) -> str:
        title = node.get("attrs", {}).get("title", "Expand")
        body = self.parse_paragraph(content)
        return f"<details><summary>{title}</summary>{body}</details>"

    def parse_heading(self, node: Dict[str, Any]) -> str:
        level = node.get("attrs", {}).get("level", 1)
        return f"{'#' * level} {self.parse_paragraph(node.get('content', []))}"

    def parse_inline_card(self, node: Dict[str, Any]) -> str:
        url = node.get("attrs", {}).get("url", "")
        return f"[{url}]({url})"

    def parse_list(self, items: List[Dict[str, Any]], ordered: bool) -> str:
        prefix = lambda i: f"{i + 1}. " if ordered else "- "
        return '\n'.join(f"{prefix(i)}{self.parse_node(item)}" for i, item in enumerate(items))

    def parse_media(self, node: Dict[str, Any], default_alt: str = "image") -> str:
        media = node.get("attrs", {})
        return f"![{media.get('alt', default_alt)}]({media.get('url', '')})"

    def parse_paragraph(self, content: List[Dict[str, Any]]) -> str:
        return ''.join(self.parse_node(child) for child in content)

    def parse_table(self, rows: List[Dict[str, Any]]) -> str:
        if not rows:
            return "<!-- Empty table -->"
        markdown = [" | ".join(self.parse_node(cell) for cell in row.get("content", [])) for row in rows if row.get("type") == "tableRow"]
        header_sep = " | ".join(["---"] * len(markdown[0].split(" | "))) if markdown else ""
        return f"\n{markdown[0]}\n{header_sep}\n" + "\n".join(markdown[1:]) if markdown else ""

    def parse_task_item(self, node: Dict[str, Any]) -> str:
        checked = "x" if node.get("attrs", {}).get("state") == "DONE" else " "
        content = self.parse_paragraph(node.get("content", []))
        return f"- [{checked}] {content}"

    def parse_task_list(self, items: List[Dict[str, Any]]) -> str:
        return '\n'.join(self.parse_node(item) for item in items)

    def parse_text(self, node: Dict[str, Any]) -> str:
        text = node.get("text", "")
        for mark in node.get("marks", []):
            text = self.apply_mark(mark, text)
        return text

    def convert(self) -> str:
        if self.adf_json.get("type") != "doc":
            raise ValueError("Invalid ADF document. Root node must be of type 'doc'.")
        return '\n\n'.join(self.parse_node(node) for node in self.adf_json.get("content", []))

    @staticmethod
    def apply_mark(mark: Dict[str, Any], text: str) -> str:
        mark_type = mark.get("type")
        attrs = mark.get("attrs", {})
        return {
            "strong": lambda: f"**{text}**",
            "em": lambda: f"*{text}*",
            "underline": lambda: f"<u>{text}</u>",
            "strike": lambda: f"~~{text}~~",
            "code": lambda: f"`{text}`",
            "textColor": lambda: f"<span style='color:{attrs.get('color', 'inherit')}'>{text}</span>",
        }.get(mark_type, lambda: text)()
