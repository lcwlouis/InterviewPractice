"""InterviewPractice — Streamlit application entry point.

Delegates to app/main.py which uses sidebar navigation with separate page modules.
Kept for backwards compatibility (``streamlit run app/streamlit_app.py``).
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.main import main  # noqa: E402

if __name__ == '__main__':
    main()
else:
    # When run via `streamlit run app/streamlit_app.py`
    main()
