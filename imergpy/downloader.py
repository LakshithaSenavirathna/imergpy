import os
import stat

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


class DownloadError(Exception):
    """Raised when an IMERG granule cannot be downloaded."""


class DownloadAuthError(DownloadError):
    """Raised when Earthdata authentication or authorization fails."""


EARTHDATA_AUTH_MESSAGE = (
    "NASA Earthdata access was denied. Check that your username/password are correct, "
    "then log in at https://urs.earthdata.nasa.gov and authorize the GES DISC application "
    "under Applications > Authorized Apps. If the password was shared publicly, change it "
    "before testing again."
)


def _short_response_text(response, limit=500):
    try:
        text = response.text
    except Exception:
        return ""
    text = " ".join(text.split())
    return text[:limit]


def _proxy_hint():
    proxy_keys = ("HTTP_PROXY", "HTTPS_PROXY", "ALL_PROXY", "http_proxy", "https_proxy", "all_proxy")
    active = [key for key in proxy_keys if os.environ.get(key)]
    if not active:
        return ""
    return (
        " This machine has proxy settings active via: "
        + ", ".join(active)
        + ". If Earthdata works on one PC but not another, compare VPN/proxy settings."
    )


def _build_session_netrc(username, password, retries=3):
    netrc_path = os.path.expanduser("~/.netrc")
    netrc_entry = (
        f"machine urs.earthdata.nasa.gov\n"
        f"    login {username}\n"
        f"    password {password}\n"
    )

    existing = ""
    if os.path.exists(netrc_path):
        with open(netrc_path, "r", encoding="utf-8") as f:
            existing = f.read()

    if "urs.earthdata.nasa.gov" not in existing:
        with open(netrc_path, "a", encoding="utf-8") as f:
            f.write(netrc_entry)
        try:
            os.chmod(netrc_path, stat.S_IRUSR | stat.S_IWUSR)
        except OSError:
            pass

    session = requests.Session()
    session.headers.update({"User-Agent": "imergpy/1.1.5"})
    session.trust_env = True

    retry = Retry(
        total=retries,
        backoff_factor=0.5,
        status_forcelist=(429, 500, 502, 503, 504),
        allowed_methods=("GET",),
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("https://", adapter)
    session.mount("http://", adapter)

    return session


def _invalid_download_reason(content_type, first_bytes, bytes_written):
    if bytes_written <= 0:
        return "NASA returned an empty file instead of IMERG NetCDF data."

    sample = first_bytes.lstrip()
    lower_sample = sample[:1000].lower()
    lower_type = (content_type or "").lower()

    if sample.startswith(b"\x89HDF\r\n\x1a\n") or sample.startswith(b"CDF"):
        return None

    auth_markers = (
        b"earthdata login",
        b"urs.earthdata",
        b"access denied",
        b"unauthorized",
        b"forbidden",
        b"you must be logged in",
    )
    if any(marker in lower_sample for marker in auth_markers):
        return EARTHDATA_AUTH_MESSAGE

    if lower_sample.startswith((b"<!doctype html", b"<html")):
        return (
            "NASA returned a web page instead of IMERG NetCDF data. This usually means "
            "Earthdata login or GES DISC authorization is required."
        )

    if any(kind in lower_type for kind in ("text/html", "text/plain", "application/xml")):
        return (
            "NASA returned a text/error response instead of IMERG NetCDF data. "
            "Check Earthdata access and the selected date/run type."
        )

    return None


class EarthdataDownloader:
    def __init__(self, username, password, timeout=60, retries=3):
        username = "" if username is None else str(username).strip()
        password = "" if password is None else str(password)

        if not username or not password:
            raise ValueError("NASA Earthdata username and password are required.")

        self.timeout = timeout
        self.session = _build_session_netrc(username, password, retries)

    def _build_url(self, lat, lon, dt, version, run_type="early", freq="hhr", bbox=None):
        from .config import get_time_string
        
        if bbox:
            min_lat, min_lon, max_lat, max_lon = bbox
            min_lat, max_lat = max(-90.0, float(min_lat)), min(90.0, float(max_lat))
            min_lon, max_lon = max(-180.0, float(min_lon)), min(180.0, float(max_lon))
        else:
            min_lat, max_lat = max(-90.0, lat - 0.1), min(90.0, lat + 0.1)
            min_lon, max_lon = max(-180.0, lon - 0.1), min(180.0, lon + 0.1)
        bbox = f"{min_lat},{min_lon},{max_lat},{max_lon}".replace(",", "%2C")

        year = dt.strftime("%Y")
        month = dt.strftime("%m")
        doy = dt.strftime("%j")
        date_str = dt.strftime("%Y%m%d")
        
        if freq == "hhr":
            time_str = get_time_string(dt)
            ext = "HDF5"
            if run_type == "early":
                shortname = "GPM_3IMERGHHE"
                prefix = f"3B-HHR-E.MS.MRG.3IMERG.{date_str}-{time_str}"
            elif run_type == "late":
                shortname = "GPM_3IMERGHHL"
                prefix = f"3B-HHR-L.MS.MRG.3IMERG.{date_str}-{time_str}"
            elif run_type == "final":
                shortname = "GPM_3IMERGHH"
                prefix = f"3B-HHR.MS.MRG.3IMERG.{date_str}-{time_str}"
            else:
                raise ValueError("run_type must be 'early', 'late', or 'final'.")
        elif freq == "daily":
            time_str = "S000000-E235959"
            ext = "nc4"
            if run_type == "early":
                shortname = "GPM_3IMERGDE"
                prefix = f"3B-DAY-E.MS.MRG.3IMERG.{date_str}-{time_str}"
            elif run_type == "late":
                shortname = "GPM_3IMERGDL"
                prefix = f"3B-DAY-L.MS.MRG.3IMERG.{date_str}-{time_str}"
            elif run_type == "final":
                shortname = "GPM_3IMERGDF"
                prefix = f"3B-DAY.MS.MRG.3IMERG.{date_str}-{time_str}"
            else:
                raise ValueError("run_type must be 'early', 'late', or 'final'.")
        elif freq == "monthly":
            time_str = f"S000000-E235959.{month}"
            ext = "HDF5"
            date_str = dt.strftime("%Y%m01") # Monthlies start on 1st
            if run_type == "final":
                shortname = "GPM_3IMERGM"
                prefix = f"3B-MO.MS.MRG.3IMERG.{date_str}-{time_str}"
            else:
                raise ValueError("Monthly frequency usually only supports 'final' run_type.")
        else:
            raise ValueError(f"Unsupported frequency: {freq}")

        filename = f"/data/GPM_L3/{shortname}.07/{year}/{doy}/{prefix}.{version}.{ext}"
        if freq == "daily":
             filename = f"/data/GPM_L3/{shortname}.07/{year}/{month}/{prefix}.{version}.{ext}"
        elif freq == "monthly":
             filename = f"/data/GPM_L3/{shortname}.07/{year}/{prefix}.{version}.{ext}"

        filename_encoded = filename.replace("/", "%2F")
        label = f"{prefix}.{version}.{ext}.SUB.nc4"

        return (
            f"https://gpm1.gesdisc.eosdis.nasa.gov/daac-bin/OTF/HTTP_services.cgi?"
            f"FILENAME={filename_encoded}&SERVICE=L34RS_GPM&LABEL={label}&BBOX={bbox}"
            f"&VERSION=1.02&VARIABLES=precipitation&SHORTNAME={shortname}&DATASET_VERSION=07&FORMAT=nc4%2F"
        )

    def download_granule(self, lat, lon, dt, out_path, run_type="early", freq="hhr", bbox=None):
        """Tries to download V07C first. If 404, falls back to V07B."""
        for version in ["V07C", "V07B", "V07A"]:
            try:
                url = self._build_url(lat, lon, dt, version, run_type, freq, bbox=bbox)
            except ValueError as e:
                raise e
                
            try:
                response = self.session.get(url, stream=True, timeout=self.timeout)
            except requests.RequestException as e:
                raise DownloadError(f"Network error while downloading {dt}: {e}") from e
            
            if response.status_code == 200:
                first_bytes = b""
                bytes_written = 0
                with open(out_path, "wb") as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            if not first_bytes:
                                first_bytes = chunk[:2048]
                            bytes_written += len(chunk)
                            f.write(chunk)

                reason = _invalid_download_reason(
                    response.headers.get("Content-Type", ""),
                    first_bytes,
                    bytes_written,
                )
                if reason:
                    try:
                        os.remove(out_path)
                    except OSError:
                        pass
                    raise DownloadError(reason)

                return True, version
            elif response.status_code == 404:
                continue
            elif response.status_code in (401, 403):
                detail = _short_response_text(response)
                message = EARTHDATA_AUTH_MESSAGE
                if detail:
                    message = f"{message} NASA response: {detail}"
                message = f"{message}{_proxy_hint()}"
                raise DownloadAuthError(message)
            else:
                detail = _short_response_text(response)
                raise DownloadError(
                    f"Failed to download data. Status: {response.status_code}. Response: {detail}"
                )
        
        raise DownloadError(f"File not available (tried V07C, V07B, V07A) for {dt} | Run: {run_type} | Freq: {freq}")
