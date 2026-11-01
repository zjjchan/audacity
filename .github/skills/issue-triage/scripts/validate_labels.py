#!/usr/bin/env python3
"""
validate_labels.py - Deterministic label validation script for Audacity Issue Triage.
Checks proposed labels against the canonical repository taxonomy, enforces mutual
exclusivity, and prevents unauthorized label application.
"""

import sys
import json

# Canonical list of allowed triage labels from Audacity repository
ALLOWED_LABELS = {
    # Types
    "bug",
    "AU3-bug",
    "Enhancement Request",
    "crash / freeze",
    "Could not reproduce",
    "regression",
    # Subsystems / Components
    "Audio Engine",
    "Effects (EGATs)",
    "Clips",
    "Tracks",
    "Cloud",
    "import-export",
    "UI",
    "Design / UX",
    "plugins",
    "accessibility",
    "Build / CI",
    # Platforms
    "Windows",
    "macOS",
    "Linux",
    # Triage States
    "needs-repro",
    "triage/needs-info",
    "triage/queued-backlog"
}

MUTUALLY_EXCLUSIVE_PAIRS = [
    {"bug", "Enhancement Request"},
    {"AU3-bug", "Enhancement Request"}
]

MAX_LABELS_PER_RUN = 3

def validate_labels(candidate_labels):
    valid = []
    invalid = []
    reasons = []

    # 1. Existence check
    for label in candidate_labels:
        clean_label = label.strip()
        if clean_label in ALLOWED_LABELS:
            if clean_label not in valid:
                valid.append(clean_label)
        else:
            invalid.append(clean_label)
            reasons.append(f"Label '{clean_label}' is not in the repository label whitelist.")

    # 2. Mutual exclusivity check
    for pair in MUTUALLY_EXCLUSIVE_PAIRS:
        overlap = set(valid).intersection(pair)
        if len(overlap) > 1:
            # If both are present, prioritize 'bug' or 'AU3-bug' over enhancement
            valid.remove("Enhancement Request")
            reasons.append(f"Removed 'Enhancement Request' due to mutual exclusivity with '{overlap - {'Enhancement Request'}}'.")

    # 3. Quota check
    if len(valid) > MAX_LABELS_PER_RUN:
        excess = valid[MAX_LABELS_PER_RUN:]
        valid = valid[:MAX_LABELS_PER_RUN]
        reasons.append(f"Trimmed excess labels {excess} to enforce MAX_LABELS limit ({MAX_LABELS_PER_RUN}).")

    return {
        "valid": valid,
        "invalid": invalid,
        "reasons": reasons,
        "approved": len(valid) > 0
    }

def main():
    if len(sys.argv) < 2:
        print(json.dumps({"error": "No labels provided. Usage: python validate_labels.py '<label1>, <label2>...'"}))
        sys.exit(1)

    raw_input = sys.argv[1]
    if raw_input.startswith("[") and raw_input.endswith("]"):
        try:
            candidates = json.loads(raw_input)
        except Exception:
            candidates = [l.strip() for l in raw_input.strip("[]").split(",") if l.strip()]
    else:
        candidates = [l.strip() for l in raw_input.split(",") if l.strip()]

    result = validate_labels(candidates)
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()
