# Publishing Guide

This guide is for package maintainers.

## 1. Clean And Test

```bash
pytest
```

Check that no secrets or generated files are present:

```bash
rg "password|EARTHDATA_PASSWORD|pypi-"
```

## 2. Build

```bash
python -m build
```

This creates:

```text
dist/imergpy-<version>.tar.gz
dist/imergpy-<version>-py3-none-any.whl
```

## 3. Check Package Metadata

```bash
python -m twine check dist/*
```

## 4. Upload To TestPyPI First

```bash
python -m twine upload --repository testpypi dist/*
```

## 5. Upload To PyPI

```bash
python -m twine upload dist/*
```

Use a PyPI API token. Do not use your PyPI password.

For a new project, the first upload usually needs an account-wide token. After the first upload, create a project-scoped token for `imergpy` and revoke the account-wide token.
