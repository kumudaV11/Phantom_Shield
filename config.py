"""Application configuration for PHANTOM SHIELD."""
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Spam verdict: SPAM DETECTED when matched categories >= threshold.
DEFAULT_THRESHOLD = 2
MIN_THRESHOLD = 1
MAX_THRESHOLD = 5

# Upload limits (bytes / counts).
MAX_UPLOAD_BYTES = 1 * 1024 * 1024      # 1 MB per uploaded file
MAX_EMAIL_CHARS = 200_000               # maximum characters scanned per email
MAX_EMAILS_PER_FILE = 500
MAX_TRACE_CHARS = 400                   # step-by-step traces limited to this many chars

# Multi-email .txt delimiter: a line containing exactly this text.
EMAIL_DELIMITER = "---EMAIL---"

DATASET_PATH = os.path.join(BASE_DIR, "data", "email_dataset.json")
GENERATED_DIR = os.path.join(BASE_DIR, "generated")

# Local only by default. Change HOST only if you really want LAN access.
HOST = os.environ.get("PHANTOM_HOST", "127.0.0.1")
PORT = int(os.environ.get("PHANTOM_PORT", "5000"))
