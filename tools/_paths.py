from pathlib import Path

SECRET_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = SECRET_ROOT / "data"
RAG_DIR = SECRET_ROOT / "rag"
POLICY_DIR = SECRET_ROOT / "policy"
TOOLS_DIR = SECRET_ROOT / "tools"
AUDIT_LOG = DATA_DIR / "audit_log.jsonl"

TELEMETRY_CSV = DATA_DIR / "tablet_press_events.csv"
BLIND_TELEMETRY_CSV = DATA_DIR / "tablet_press_events_blind.csv"
MAINTENANCE_CSV = DATA_DIR / "maintenance_history.csv"
INCIDENTS_JSONL = DATA_DIR / "incidents.jsonl"
BLIND_WINDOWS_JSON = TOOLS_DIR / "blind_dataset_windows.json"
RULES_CONFIG_JSON = TOOLS_DIR / "rules_config.json"
ACTION_POLICY_JSON = POLICY_DIR / "action_policy.json"
RAG_MANIFEST_CSV = RAG_DIR / "manifest.csv"
