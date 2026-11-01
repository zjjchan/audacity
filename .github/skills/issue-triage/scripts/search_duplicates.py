#!/usr/bin/env python3
"""
search_duplicates.py - Deterministic duplicate search script for Audacity Issue Triage.
Scans incoming issue text for symptom signatures, error terms, and component keywords,
matching against repository issues to identify potential duplicate reports.
"""

import sys
import json
import re

# Curated reference index of past frequently-reported or representative Audacity issues
REFERENCE_ISSUES = [
    {
        "number": 12109,
        "title": "Metadata is not written to MP3 files during export",
        "keywords": ["metadata", "mp3", "export", "tag", "id3", "artist", "title"],
        "url": "https://github.com/audacity/audacity/issues/12109"
    },
    {
        "number": 12606,
        "title": "Crash on dock layout rebuild (workspace switch, closing project) after the first window is closed",
        "keywords": ["crash", "dock", "layout", "workspace", "switch", "freeze", "hang", "window"],
        "url": "https://github.com/audacity/audacity/issues/12606"
    },
    {
        "number": 10500,
        "title": "Project corrupted when pressing cancel during compacting project",
        "keywords": ["corrupt", "compaction", "cancel", "database", "sqlite", "project", "aup3", "close"],
        "url": "https://github.com/audacity/audacity/issues/10500"
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

def search_duplicates(title, body="", exclude_number=None):
    tokens = set(tokenize(f"{title} {body}"))
    results = []

    for issue in REFERENCE_ISSUES:
        if exclude_number and str(issue["number"]) == str(exclude_number):
            continue
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
    exclude_number = sys.argv[3] if len(sys.argv) > 3 else None
    result = search_duplicates(title, body, exclude_number)
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()
