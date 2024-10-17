# CONTRIBUTING

Code contributions are welcomed and appreciated. Just submit a PR!

The current build environment uses `pre-commit`, and `hatch`.

### Environment setup:

```console
pip install hatch
git clone git@github.com:afourney/aprstastic.git
cd aprstastic
pre-commit install

# Optionally run the pre-commit scripts at any time
pre-commit run --all-files
```

### Running and testing:

From the aprstastic directory:

```console
hatch shell

# Running
python -m aprstastic


# Testing
hatch test
```
