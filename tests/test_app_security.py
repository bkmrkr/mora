"""Tests for app.py security features — headers and error handler."""


def test_security_headers_present(client):
    """All security headers should be set on every response."""
    resp = client.get('/')
    assert resp.headers.get('X-Content-Type-Options') == 'nosniff'
    assert resp.headers.get('X-Frame-Options') == 'SAMEORIGIN'
    assert 'Content-Security-Policy' in resp.headers


def test_csp_allows_inline_styles(client):
    """CSP should allow unsafe-inline for styles (admin templates use inline)."""
    csp = client.get('/').headers.get('Content-Security-Policy')
    assert "'unsafe-inline'" in csp


def test_csp_allows_data_images(client):
    """CSP should allow data: URIs for images (SVGs use data: URIs)."""
    csp = client.get('/').headers.get('Content-Security-Policy')
    assert "img-src 'self' data:" in csp


def test_error_handler_hides_details(app):
    """Error handler should NOT leak exception details to user."""
    @app.route('/test-500')
    def crash():
        raise ValueError('secret database password is xyz123')

    with app.test_client() as c:
        resp = c.get('/test-500')
        assert resp.status_code == 500
        body = resp.data.decode()
        assert 'secret database password' not in body
        assert 'xyz123' not in body
        assert 'Internal Server Error' in body


def test_wal_mode_set(temp_db):
    """SQLite WAL mode should be enabled."""
    from db.database import get_db
    conn = get_db()
    try:
        result = conn.execute('PRAGMA journal_mode').fetchone()
        assert result[0] == 'wal'
    finally:
        conn.close()


def test_foreign_keys_enabled(temp_db):
    """Foreign keys should be enforced."""
    from db.database import get_db
    conn = get_db()
    try:
        result = conn.execute('PRAGMA foreign_keys').fetchone()
        assert result[0] == 1
    finally:
        conn.close()
