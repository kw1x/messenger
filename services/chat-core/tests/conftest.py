from __future__ import annotations

import sys
from pathlib import Path

# Make `app` importable when running pytest from the workspace root.
_SERVICE_ROOT = Path(__file__).resolve().parent.parent
if str(_SERVICE_ROOT) not in sys.path:
    sys.path.insert(0, str(_SERVICE_ROOT))
