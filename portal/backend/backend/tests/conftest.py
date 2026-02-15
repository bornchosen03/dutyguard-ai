import os
import sys

# Ensure the repository's `/portal/backend` directory is on sys.path so
# `import backend...` works when pytest collects tests from any CWD.
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
