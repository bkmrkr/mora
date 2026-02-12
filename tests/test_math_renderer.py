"""Tests for server-side LaTeX math rendering via matplotlib."""
import concurrent.futures

from services.math_renderer import latex_to_svg, render_math_in_text


# --- latex_to_svg ---

def test_simple_expression():
    result = latex_to_svg('y - x')
    assert '<img' in result
    assert 'data:image/svg+xml;base64,' in result
    assert 'math-inline' in result


def test_fraction():
    result = latex_to_svg(r'\frac{1}{2}')
    assert '<img' in result


def test_sqrt():
    result = latex_to_svg(r'\sqrt{16}')
    assert '<img' in result


def test_superscript():
    result = latex_to_svg('x^2 + 3x - 5')
    assert '<img' in result


def test_display_mode():
    result = latex_to_svg('x^2', display=True)
    assert 'math-display' in result


def test_inline_mode_default():
    result = latex_to_svg('x + 1')
    assert 'math-inline' in result


def test_alt_attribute():
    result = latex_to_svg('y - x')
    assert 'alt="y - x"' in result


def test_malformed_latex_fallback():
    result = latex_to_svg(r'\undefinedcommand{x}')
    # Should not crash — either renders partially or falls back to <code>
    assert '<img' in result or 'math-fallback' in result


# --- render_math_in_text ---

def test_inline_delimiters():
    text = r'Solve \(y - x\) for y'
    result = render_math_in_text(text)
    assert '<img' in result
    assert r'\(' not in result
    assert r'\)' not in result


def test_display_delimiters():
    text = r'The equation is \[x^2 + 1 = 0\]'
    result = render_math_in_text(text)
    assert 'math-display' in result


def test_multiple_expressions():
    text = r'If \(x = 5\), what is \(2x + 3\)?'
    result = render_math_in_text(text)
    assert result.count('<img') == 2


def test_no_math_passthrough():
    text = 'What is 2 + 2?'
    result = render_math_in_text(text)
    assert result == text
    assert '<img' not in result


def test_none_returns_none():
    assert render_math_in_text(None) is None


def test_empty_string():
    assert render_math_in_text('') == ''


def test_non_string_returns_as_is():
    assert render_math_in_text(42) == 42


# --- Cache ---

def test_cache_hit():
    latex_to_svg.cache_clear()
    latex_to_svg('a + b')
    latex_to_svg('a + b')
    info = latex_to_svg.cache_info()
    assert info.hits >= 1


# --- Thread safety ---

def test_concurrent_rendering():
    expressions = ['x^2', r'\frac{1}{2}', r'\sqrt{4}', 'a + b']
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        futures = [pool.submit(latex_to_svg, e) for e in expressions * 3]
        results = [f.result() for f in futures]
    assert all('<img' in r or 'math-fallback' in r for r in results)
