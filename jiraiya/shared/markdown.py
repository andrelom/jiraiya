import json
from typing import Dict, Any, List


class ADFToMarkdownConverter:
    """
    A class to convert Atlassian Document Format (ADF) JSON to Markdown.
    """

    def __init__(self, adf_json: Dict[str, Any]) -> None:
        self.adf_json = adf_json

    def parse_node(self, node: Dict[str, Any]) -> str:
        """
        Recursively parse a node from the ADF structure and convert it to Markdown.
        """
        node_type = node.get("type")
        content = node.get("content", [])

        handlers = {
            "paragraph": lambda: self.parse_paragraph(content),
            "heading": lambda: self.parse_heading(node),
            "orderedList": lambda: self.parse_list(content, ordered=True),
            "bulletList": lambda: self.parse_list(content, ordered=False),
            "listItem": lambda: self.parse_paragraph(content),
            "text": lambda: self.parse_text(node),
            "mediaSingle": lambda: self.parse_media_single(content),
            "inlineCard": lambda: self.parse_inline_card(node),
            "blockquote": lambda: f"> {self.parse_paragraph(content)}",
            "rule": lambda: "---",
            "mediaInline": lambda: self.parse_media_inline(node),
            "emoji": lambda: node.get("attrs", {}).get("text", ""),
            "mention": lambda: f"@{node.get('attrs', {}).get('text', '')}",
            "status": lambda: f"[{node.get('attrs', {}).get('text', '')}]",
            "codeBlock": lambda: self.parse_code_block(node, content),
            "panel": lambda: f"> **Panel:** {self.parse_paragraph(content)}",
            "expand": lambda: self.parse_expand(node, content),
            "nestedExpand": lambda: self.parse_node({"type": "expand", "content": content}),
            "table": lambda: self.parse_table(content),
            "decisionList": lambda: self.parse_list(content, ordered=False),
            "decisionItem": lambda: f"- [Decision] {self.parse_paragraph(content)}",
            "taskList": lambda: self.parse_task_list(content),
            "taskItem": lambda: self.parse_task_item(node),
            "mediaGroup": lambda: self.parse_media_group(content),
            "extension": lambda: self.parse_extension(node),
            "inlineExtension": lambda: self.parse_inline_extension(node),
            "layoutSection": lambda: self.parse_layout_section(content),
            "layoutColumn": lambda: self.parse_layout_column(node, content),
            "unsupportedBlock": lambda: "<!-- Unsupported block content -->",
            "unsupportedInline": lambda: "<!-- Unsupported inline content -->",
        }

        return handlers.get(node_type, lambda: f"<!-- Unsupported node type: {node_type} -->")()

    def parse_paragraph(self, content: List[Dict[str, Any]]) -> str:
        return ''.join(self.parse_node(child) for child in content)

    def parse_heading(self, node: Dict[str, Any]) -> str:
        level = node.get("attrs", {}).get("level", 1)
        return f"{'#' * level} {self.parse_paragraph(node.get('content', []))}"

    def parse_list(self, items: List[Dict[str, Any]], ordered: bool) -> str:
        prefix = lambda i: f"{i + 1}. " if ordered else "- "
        return '\n'.join(f"{prefix(i)}{self.parse_node(item)}" for i, item in enumerate(items))

    def parse_task_list(self, items: List[Dict[str, Any]]) -> str:
        return '\n'.join(self.parse_node(item) for item in items)

    def parse_task_item(self, node: Dict[str, Any]) -> str:
        checked = "x" if node.get("attrs", {}).get("state") == "DONE" else " "
        content = self.parse_paragraph(node.get("content", []))
        return f"- [{checked}] {content}"

    def parse_text(self, node: Dict[str, Any]) -> str:
        text = node.get("text", "")
        for mark in node.get("marks", []):
            text = self.apply_mark(mark, text)
        return text

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
            "alignment": lambda: f"<div style='text-align:{attrs.get('align', 'left')}'>{text}</div>",
        }.get(mark_type, lambda: text)()

    def parse_code_block(self, node: Dict[str, Any], content: List[Dict[str, Any]]) -> str:
        language = node.get("attrs", {}).get("language", "")
        return f"```{language}\n{self.parse_paragraph(content)}\n```"

    def parse_media_single(self, content: List[Dict[str, Any]]) -> str:
        media = content[0].get("attrs", {}) if content else {}
        return f"![{media.get('alt', 'image')}]({media.get('url', '')})"

    def parse_inline_card(self, node: Dict[str, Any]) -> str:
        url = node.get("attrs", {}).get("url", "")
        return f"[{url}]({url})"

    def parse_media_inline(self, node: Dict[str, Any]) -> str:
        media = node.get("attrs", {})
        return f"![{media.get('alt', 'image')}]({media.get('url', '')})"

    def parse_expand(self, node: Dict[str, Any], content: List[Dict[str, Any]]) -> str:
        title = node.get("attrs", {}).get("title", "Expand")
        body = self.parse_paragraph(content)
        return f"<details><summary>{title}</summary>{body}</details>"

    def parse_media_group(self, content: List[Dict[str, Any]]) -> str:
        return '\n'.join(f"![{media.get('attrs', {}).get('alt', 'image')}]({media.get('attrs', {}).get('url', '')})" for media in content)

    def parse_table(self, rows: List[Dict[str, Any]]) -> str:
        markdown = [" | ".join(self.parse_node(cell) for cell in row.get("content", [])) for row in rows if row.get("type") == "tableRow"]
        header_sep = " | ".join(["---"] * len(markdown[0].split(" | "))) if markdown else ""
        return f"\n{markdown[0]}\n{header_sep}\n" + "\n".join(markdown[1:]) if markdown else ""

    def parse_extension(self, node: Dict[str, Any]) -> str:
        attrs = node.get("attrs", {})
        return f"<!-- Extension: {attrs.get('extensionType', 'generic')}, Parameters: {attrs.get('parameters', {})} -->"

    def parse_inline_extension(self, node: Dict[str, Any]) -> str:
        attrs = node.get("attrs", {})
        return f"<!-- Inline Extension: {attrs.get('extensionType', 'generic')}, Parameters: {attrs.get('parameters', {})} -->"

    def parse_layout_section(self, content: List[Dict[str, Any]]) -> str:
        return '\n'.join(self.parse_node(column) for column in content)

    def parse_layout_column(self, node: Dict[str, Any], content: List[Dict[str, Any]]) -> str:
        width = node.get("attrs", {}).get("width", "100%")
        return f"<div style='width:{width}%'>{self.parse_paragraph(content)}</div>"

    def convert(self) -> str:
        if self.adf_json.get("type") != "doc":
            raise ValueError("Invalid ADF document. Root node must be of type 'doc'.")
        return '\n\n'.join(self.parse_node(node) for node in self.adf_json.get("content", []))
