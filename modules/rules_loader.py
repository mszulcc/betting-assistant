"""
Rules Loader module.

Reads all Markdown (.md) files from the data/rules/ directory and injects
their content into the LLM system prompt as "Custom Betting Rules".

Usage:
  - Drop any .md file into data/rules/
  - The content is automatically picked up on the next Streamlit reload
  - Files are reloaded every RELOAD_TTL_SECONDS (default: 60s) in a live session

File naming convention (optional but helpful):
  - 01_bankroll.md
  - 02_value_strategy.md
  - moje_zasady.md
  Files are loaded in alphabetical order.
"""

import os
import time
import glob

_RULES_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "rules")

# In-memory cache: avoid re-reading disk on every message
_cache: dict = {
    "content": None,       # str — concatenated rules text
    "fetched_at": 0.0,
    "ttl": 60.0,           # re-read files every 60 seconds
}


def _read_rules_dir() -> str:
    """
    Read all .md files from data/rules/ in alphabetical order.
    Returns a single concatenated string, or '' if the directory is empty or missing.
    """
    os.makedirs(_RULES_DIR, exist_ok=True)
    md_files = sorted(glob.glob(os.path.join(_RULES_DIR, "*.md")))

    if not md_files:
        return ""

    parts = []
    for path in md_files:
        fname = os.path.basename(path)
        try:
            with open(path, encoding="utf-8") as f:
                text = f.read().strip()
            if text:
                parts.append(f"### {fname}\n\n{text}")
        except Exception as e:
            parts.append(f"### {fname}\n\n_(Error reading file: {e})_")

    return "\n\n---\n\n".join(parts)


def get_rules() -> str:
    """
    Return the combined rules text from all MD files in data/rules/.
    Uses a 60-second in-memory cache to avoid disk reads on every message.
    Returns '' if no files exist.
    """
    global _cache
    now = time.time()
    if _cache["content"] is None or (now - _cache["fetched_at"]) > _cache["ttl"]:
        _cache["content"] = _read_rules_dir()
        _cache["fetched_at"] = now
    return _cache["content"]


def has_rules() -> bool:
    """Return True if at least one rules file is present."""
    return bool(get_rules())


def get_rules_dir() -> str:
    """Return the absolute path to the rules directory."""
    return _RULES_DIR


def list_rule_files() -> list[dict]:
    """
    Return metadata about loaded rule files.
    Useful for displaying in the UI.
    """
    os.makedirs(_RULES_DIR, exist_ok=True)
    result = []
    for path in sorted(glob.glob(os.path.join(_RULES_DIR, "*.md"))):
        stat = os.stat(path)
        result.append({
            "filename": os.path.basename(path),
            "path": path,
            "size_kb": round(stat.st_size / 1024, 1),
            "modified": time.strftime("%Y-%m-%d %H:%M", time.localtime(stat.st_mtime)),
        })
    return result


def invalidate_cache():
    """Force rules to be re-read on next get_rules() call."""
    _cache["fetched_at"] = 0.0
