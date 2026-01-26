"""Get Didier Stevens's pdf-parser.py and pdfid.py from github, place them in tools/ dir, and make executable."""
import os
import stat
import sys
from pathlib import Path

import requests

DIDIER_STEVENS_RAW_GITHUB_URL = 'https://raw.githubusercontent.com/DidierStevens/DidierStevensSuite/master/'
TOOL_EXECUTABLES= 'pdfid.py pdf-parser.py xorsearch.py'.split()

PROJECT_DIR = Path(__file__).parent.parent
TOOLS_DIR = PROJECT_DIR.joinpath('tools')
TOOLS_DIR.mkdir(exist_ok=True)


for tool in TOOL_EXECUTABLES:
    tool_path = TOOLS_DIR.joinpath(tool)
    tool_url = f"{DIDIER_STEVENS_RAW_GITHUB_URL}/{tool}"
    print(f"Downloading '{tool}' from {tool_url}")
    response = requests.get(tool_url)
    tool_path.write_text(response.text)
    print(f"Making '{tool_path}' executable...")
    tool_path.chmod(os.stat(tool_path).st_mode | stat.S_IEXEC)

print("\n\n\nDidier Stevens recommends always using the -O option with pdf-parser.py.")
print("This can be accomplished by setting the PDFPARSER_OPTIONS environment variable:\n")
print("         PDFPARSER_OPTIONS=-O\n")
print("You are encouraged to add that to your environment via your .bash_profile or similar.")
print("This has NOT been done automatically.")
