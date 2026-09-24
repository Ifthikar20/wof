"""
Markdown -> safe HTML. Raw HTML in the source is disabled at the parser level, and the
output is then run through nh3 (Rust `ammonia`) with a strict allowlist as a second
barrier. The frontend renders only this server-produced HTML.
"""

import nh3
from markdown_it import MarkdownIt

_md = MarkdownIt("commonmark", {"html": False, "linkify": False, "typographer": True})
_md.disable("image")  # images come from the vetted media pipeline, never arbitrary URLs

ALLOWED_TAGS = {
    "p",
    "br",
    "hr",
    "h2",
    "h3",
    "h4",
    "strong",
    "em",
    "blockquote",
    "ul",
    "ol",
    "li",
    "code",
    "pre",
    "a",
}
ALLOWED_ATTRS = {"a": {"href", "title"}}
ALLOWED_SCHEMES = {"https", "http", "mailto"}


def render_markdown(source: str) -> str:
    html = _md.render(source or "")
    # Demote h1 (reserved for the story title) to h2.
    html = html.replace("<h1>", "<h2>").replace("</h1>", "</h2>")
    return nh3.clean(
        html,
        tags=ALLOWED_TAGS,
        attributes=ALLOWED_ATTRS,
        url_schemes=ALLOWED_SCHEMES,
        link_rel="nofollow noopener noreferrer ugc",
        strip_comments=True,
    )
