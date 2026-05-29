import requests
from requests.adapters import HTTPAdapter
from requests.auth import HTTPBasicAuth
from urllib3.util.retry import Retry


class DownloadError(Exception):
    """Raised when an IMERG granule cannot be downloaded."""


class EarthdataDownloader:
    def __init__(self, username, password, timeout=60, retries=3):
        if not username or not password:
            raise ValueError("NASA Earthdata username and password are required.")

        self.timeout = timeout
        self.session = requests.Session()
        self.session.auth = HTTPBasicAuth(username, password)
        retry = Retry(
            total=retries,
            connect=retries,
            read=retries,
            status=retries,
            backoff_factor=0.5,
            status_forcelist=(429, 500, 502, 503, 504),
            allowed_methods=("GET",),
        )
        adapter = HTTPAdapter(max_retries=retry)
        self.session.mount("https://", adapter)
        self.session.mount("http://", adapter)

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
                with open(out_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                return True, version
            elif response.status_code == 404:
                continue
            else:
                raise DownloadError(f"Failed to download data. Status: {response.status_code}. Response: {response.text}")
        
        raise DownloadError(f"File not available (tried V07C, V07B, V07A) for {dt} | Run: {run_type} | Freq: {freq}")
