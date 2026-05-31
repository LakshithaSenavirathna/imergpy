from imergpy.downloader import (
    EARTHDATA_AUTH_MESSAGE,
    DownloadAuthError,
    _build_session_netrc,
    _invalid_download_reason,
)


def test_valid_hdf5_download_has_no_error_reason():
    reason = _invalid_download_reason(
        "application/octet-stream",
        b"\x89HDF\r\n\x1a\nsome-data",
        100,
    )

    assert reason is None


def test_valid_netcdf_download_has_no_error_reason():
    reason = _invalid_download_reason("application/x-netcdf", b"CDF\x02some-data", 100)

    assert reason is None


def test_earthdata_login_page_is_reported_as_access_denied():
    reason = _invalid_download_reason(
        "text/html",
        b"<!DOCTYPE html><html><title>Earthdata Login</title></html>",
        100,
    )

    assert EARTHDATA_AUTH_MESSAGE in reason


def test_empty_download_is_invalid():
    reason = _invalid_download_reason("application/octet-stream", b"", 0)

    assert "empty file" in reason


def test_auth_error_is_distinct_type():
    assert issubclass(DownloadAuthError, Exception)


def test_username_is_trimmed_when_downloader_is_created(monkeypatch, tmp_path):
    from imergpy.downloader import EarthdataDownloader

    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv("USERPROFILE", str(tmp_path))
    downloader = EarthdataDownloader("  user  ", "password")
    netrc_text = (tmp_path / ".netrc").read_text(encoding="utf-8")

    assert downloader.session.trust_env is True
    assert "login user" in netrc_text


def test_build_session_netrc_uses_trust_env(monkeypatch, tmp_path):
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv("USERPROFILE", str(tmp_path))

    session = _build_session_netrc("user", "password")

    assert session.trust_env is True
    assert (tmp_path / ".netrc").exists()
