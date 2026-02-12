"""Server-side LaTeX math rendering using matplotlib's mathtext.

Converts \\(...\\) and \\[...\\] LaTeX expressions to inline SVG images.
Uses Figure() directly (not pyplot) for thread safety in Flask threaded mode.
No TeX installation required — matplotlib's built-in mathtext parser handles it.
"""
import base64
import io
import logging
import re
from functools import lru_cache

from matplotlib.figure import Figure
from matplotlib.backends.backend_svg import FigureCanvasSVG

logger = logging.getLogger(__name__)

INLINE_RE = re.compile(r'\\\((.+?)\\\)', re.DOTALL)
DISPLAY_RE = re.compile(r'\\\[(.+?)\\\]', re.DOTALL)


@lru_cache(maxsize=512)
def latex_to_svg(latex_expr, fontsize=16, display=False):
    """Render a LaTeX expression to an inline <img> tag with base64 SVG.

    Returns HTML string. On failure, returns a <code> fallback.
    """
    try:
        fig = Figure(figsize=(0.01, 0.01))
        fig.patch.set_alpha(0)
        FigureCanvasSVG(fig)
        fig.text(0, 0, f'${latex_expr}$', fontsize=fontsize,
                 math_fontfamily='cm')
        buf = io.BytesIO()
        fig.savefig(buf, format='svg', bbox_inches='tight',
                    pad_inches=0.02, transparent=True)
        b64 = base64.b64encode(buf.getvalue()).decode('ascii')
        css_class = 'math-display' if display else 'math-inline'
        return (f'<img class="{css_class}" '
                f'src="data:image/svg+xml;base64,{b64}" '
                f'alt="{latex_expr}">')
    except Exception as exc:
        logger.warning('Failed to render LaTeX: %s — expr: %s', exc, latex_expr)
        return f'<code class="math-fallback">{latex_expr}</code>'


def render_math_in_text(text):
    """Replace \\(...\\) and \\[...\\] in text with rendered SVG images."""
    if not text or not isinstance(text, str):
        return text
    if '\\(' not in text and '\\[' not in text:
        return text
    text = DISPLAY_RE.sub(
        lambda m: latex_to_svg(m.group(1).strip(), fontsize=18, display=True),
        text,
    )
    text = INLINE_RE.sub(
        lambda m: latex_to_svg(m.group(1).strip(), fontsize=16, display=False),
        text,
    )
    return text
