# CONTRIBUTING
Contributions are welcome, just make sure that before you open a pull request:

1. The `pytest` suite passes (see [here](#Testing) for more info on running the tests).
1. You add tests for your changes to the `pytest` test suite.
1. You add a description of your changes to [the changelog](CHANGELOG.md).


# Development Environment Setup
1. `git clone https://github.com/michelcrypt4d4mus/pdfalyzer.git`
1. `cd pdfalyzer`

After that there's a forking path depending on whether or not you use [`poetry`](https://python-poetry.org) (which we use and recommend you also use if you're working on this code base) to manage your python lifestyle.

Note that the minimum versions for each package were chosen because that's what worked on my machine and not because that version had some critical bug fix or feature so it's entirely possible that using earlier versions than are specified in [pyproject.toml](pyproject.toml) will work just fine. Feel free to experiment if there's some kind of version conflict for you.

### With Python Poetry:
These commands are the [`poetry`](https://python-poetry.org) equivalent of the traditional virtualenv installation followed by `source venv/bin/activate` but there's a lot of ways to run a python script in a virtualenv with `poetry` so you do you if you prefer another approach.

```bash
poetry install --all-extras
source $(poetry env info --path)/bin/activate
```

### With A Manual `venv`:
```bash
python -m venv .venv              # Create a virtualenv in .venv
. .venv/bin/activate              # Activate the virtualenv
pip install .[extract]            # Install packages
```

Note that I'm not sure exactly how to get the `pdfalyze` command installed when developing outside of a `poetry` env, but creating a simple `run_pdfalyzer.py` file with these contents would do the same thing:

```python
from pdfalyzer import pdfalyzer
pdfalyzer()
```

# What To Contribute

### The Official TODO List
1. Highlight decodes with a lot of Javascript keywords
1. Check that `/ObjStm nodes are what they advertise themselves as
1. Figure out a way to differentiate nodes that have been forcibly placed based on heuristics and guesses instead of concrete PDF object references
1. https://github.com/mandiant/flare-floss (https://github.com/mandiant/flare-floss/releases/download/v2.1.0/floss-v2.1.0-linux.zip)
1. https://github.com/1Project/Scanr/blob/master/emulator/emulator.py

### YARA Rules
We love any and all PDF malware related YARA rules so send them our way.


# Testing
The `pytest` suite checks a lot of things, including that the colored output exactly matches various fixture files in the repo.

```bash
# Run all tests (including the slow ones):
pytest -v --slow

# Run tests (but not the slow ones):
pytest

# Run only the slow tests:
pytest -m slow --slow:
```
See [pytest's official docs](https://docs.pytest.org/en/7.1.x/how-to/usage.html) for other instantiation options.

You must have `pdf-parser.py` installed to run a few of the tests. You can get it by running `pdfalyzer_install_pdf_parser` (or you can just [download it manually](https://raw.githubusercontent.com/DidierStevens/DidierStevensSuite/master/pdf-parser-py) and place it in a `pdfalyzer/pfd_tools/` directory).


If you make changes to the output for a test fixture you may need to update the recorded fixture files in [`tests/fixtures/rendered/`](tests/fixtures/rendered/), which you can do like this:

```bash
PYTEST_REBUILD_FIXTURES pytest
```
