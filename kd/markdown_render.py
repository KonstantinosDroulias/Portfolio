"""Markdown → HTML for posts. Only signed-in authors write Markdown, so raw HTML is allowed."""
import re

import markdown

_EXTENSIONS = ["extra", "sane_lists", "toc", "smarty"]
_EXT_CONFIG = {"toc": {"permalink": False, "toc_depth": "2-3"}}

# A paragraph that only holds an image becomes a figure; the image title becomes the caption.
_LONE_IMG = re.compile(r"<p>\s*(<img\b[^>]*?)\s*/?>\s*</p>")
_TITLE = re.compile(r'\stitle="([^"]*)"')


def _figure(match):
    tag = match.group(1)
    caption = ""
    t = _TITLE.search(tag)
    if t:
        caption = t.group(1)
        tag = _TITLE.sub("", tag)
    img = f'{tag} loading="lazy" decoding="async">'
    cap = f"<figcaption>{caption}</figcaption>" if caption else ""
    return f"<figure>{img}{cap}</figure>"


def render_markdown(text):
    html = markdown.markdown(text or "", extensions=_EXTENSIONS, extension_configs=_EXT_CONFIG, output_format="html")
    html = _LONE_IMG.sub(_figure, html)
    html = re.sub(r"<table>", '<div class="table-wrap"><table>', html)
    html = re.sub(r"</table>", "</table></div>", html)
    return html


def word_count(text):
    return len(re.findall(r"\w+", re.sub(r"```.*?```", " ", text or "", flags=re.S)))
