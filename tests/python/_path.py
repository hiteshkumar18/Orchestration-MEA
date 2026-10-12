"""Make the orchestration modules importable the way api.py imports them."""
import sys
from pathlib import Path

ORCH = Path(__file__).resolve().parents[2] / "orchestration"
if str(ORCH) not in sys.path:
    sys.path.insert(0, str(ORCH))
