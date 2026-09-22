import sys
from pathlib import Path

# The script ships inside the skill and the tests do not, so put the skill's
# scripts directory on the import path for `from vault_health import ...`.
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "skills" / "vault-health" / "scripts"))
