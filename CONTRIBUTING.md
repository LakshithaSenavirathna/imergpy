# Contributing

Thank you for improving `imergpy`.

## Local Setup

```bash
git clone https://github.com/LakshithaSenavirathna/imergpy.git
cd imergpy
pip install -e ".[dev]"
```

## Run Tests

```bash
pytest
```

## Credentials

Never commit NASA Earthdata usernames, passwords, API tokens, `.env` files, downloaded Excel files, or NetCDF files.

Use environment variables for local testing:

```powershell
$env:EARTHDATA_USERNAME = "your_username"
$env:EARTHDATA_PASSWORD = "your_password"
```

## Pull Requests

Please keep changes focused and include tests when changing downloader, processor, or analysis behavior.
