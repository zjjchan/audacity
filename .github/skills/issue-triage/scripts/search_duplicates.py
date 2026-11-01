#!/usr/bin/env python3
"""
search_duplicates.py - Deterministic duplicate search script for Audacity Issue Triage.
Scans incoming issue text for symptom signatures, error terms, and component keywords,
matching against repository issues to identify potential duplicate reports.
"""

import sys
import json
import re

# Curated reference index of known frequently-reported or representative Audacity issues
REFERENCE_ISSUES = [
    {
        "number": 12109,
        "title": "Metadata is not written to MP3 files during export",
        "keywords": ["metadata", "mp3", "export", "tag", "id3", "artist", "title"],
        "url": "https://github.com/audacity/audacity/issues/12109"
    },
    {
        "number": 12625,
        "title": "Crash when switching workspaces",
        "keywords": ["crash", "workspace", "switch", "freeze", "hang", "qml"],
        "url": "https://github.com/audacity/audacity/issues/12625"
    },
    {
        "number": 12626,
        "title": "Project gets corrupted if compaction step is cancelled",
        "keywords": ["corrupt", "compaction", "cancel", "database", "sqlite", "project", "aup3"],
        "url": "https://github.com/audacity/audacity/issues/12626"
    },
    {
        "number": 12620,
        "title": "Audacity 3.7.9: 'Snap' to CDDA frames (75 fps) does not work",
        "keywords": ["snap", "cdda", "frames", "75 fps", "grid", "timeline", "snap to"],
        "url": "https://github.com/audacity/audacity/issues/12620"
    },
    {
        "number": 12588,
        "title": "Cloud conflict resolution crashes the app",
        "keywords": ["cloud", "conflict", "resolution", "crash", "audio.com", "sync"],
        "url": "https://github.com/audacity/audacity/issues/12588"
    },
    {
        "number": 12439,
        "title": "The export menu is desactivated",
        "keywords": ["export", "menu", "desactivated", "disabled", "greyed out", "cannot export"],
        "url": "https://github.com/audacity/audacity/issues/12439"
    },
    {
        "number": 12624,
        "title": "When copying clips between tracks of different sample rates, clip's amplitude and loudness change",
        "keywords": ["sample rate", "resample", "amplitude", "loudness", "copy", "paste", "clips"],
        "url": "https://github.com/audacity/audacity/issues/12624"
    }
]

def normalize_stem(word):
    w = word.lower().strip(".,;:!?\"'()[]{}")
    for suffix in ["tion", "ing", "ed", "es", "s"]:
        if len(w) > len(suffix) + 3 and w.endswith(suffix):
            return w[:-len(suffix)]
    return w

def tokenize(text):
    words = re.findall(r'\b[a-zA-Z0-9_\-\.]{3,}\b', text.lower())
    stop_words = {"the", "and", "for", "with", "this", "that", "from", "when", "then", "into", "audacity"}
    return [normalize_stem(w) for w in words if w not in stop_words]

def search_duplicates(title, body=""):
    tokens = set(tokenize(f"{title} {body}"))
    results = []

    for issue in REFERENCE_ISSUES:
        issue_keywords = set([normalize_stem(k) for k in issue["keywords"]])
        overlap = tokens.intersection(issue_keywords)
        if overlap:
            score = len(overlap) / len(issue_keywords)
            if score >= 0.25:  # keyword match threshold
                results.append({
                    "number": issue["number"],
                    "title": issue["title"],
                    "url": issue["url"],
                    "score": round(score, 2),
                    "matched_terms": list(overlap)
                })

    results.sort(key=lambda x: x["score"], reverse=True)
    return {
        "query_title": title,
        "duplicates_found": len(results) > 0,
        "candidates": results[:3]
    }

def main():
    if len(sys.argv) < 2:
        print(json.dumps({"error": "No query provided. Usage: python search_duplicates.py '<title>' '<body_optional>'"}))
        sys.exit(1)

    title = sys.argv[1]
    body = sys.argv[2] if len(sys.argv) > 2 else ""
    result = search_duplicates(title, body)
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()
