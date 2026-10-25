"""DEV SHIM for Aziz's remem/config.py — only the vars the answer slice reads.

Assumes the real config exposes module-level constants named exactly like the
env vars in context/setup.md §5. Delete this shim once S0 is on main.
"""

import os

REMEM_DATA_DIR = os.environ.get("REMEM_DATA_DIR", "data/live")
TZ = os.environ.get("TZ", "America/Los_Angeles")

QUERY_TEMPLATE = os.environ.get("QUERY_TEMPLATE", "a photo of {X}")
Z_MIN = float(os.environ.get("Z_MIN", "3"))
Z_ACT = float(os.environ.get("Z_ACT", "5"))
TOP_K = int(os.environ.get("TOP_K", "10"))

ASK_TIMEOUT_S = float(os.environ.get("ASK_TIMEOUT_S", "5"))
VERIFY_BACKEND = os.environ.get("VERIFY_BACKEND", "none")
VERIFY_MODEL = os.environ.get("VERIFY_MODEL", "google/gemma-4-E4B-it")
VERIFY_N = int(os.environ.get("VERIFY_N", "5"))
VERIFY_TIMEOUT_S = float(os.environ.get("VERIFY_TIMEOUT_S", "2.5"))
CONF_ACT = float(os.environ.get("CONF_ACT", "0.8"))
CONF_ASK = float(os.environ.get("CONF_ASK", "0.5"))
