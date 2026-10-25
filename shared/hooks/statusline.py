"""Status line: model and effort, context use, and the five-hour and weekly plan limits.

Prints one ASCII line such as "Opus 5.5 high | ctx 34% | 5h 12% | 7d 40%". Fields that a session
doesn't report (rate limits before the first reply, for example) are left out.
"""

import json
import sys


def main():
    data = json.load(sys.stdin)
    head = (data.get("model") or {}).get("display_name", "?")
    effort = (data.get("effort") or {}).get("level")
    parts = [f"{head} {effort}" if effort else head]
    used = (data.get("context_window") or {}).get("used_percentage")
    if used is not None:
        parts.append(f"ctx {round(used)}%")
    limits = data.get("rate_limits") or {}
    for key, label in (("five_hour", "5h"), ("seven_day", "7d")):
        pct = (limits.get(key) or {}).get("used_percentage")
        if pct is not None:
            parts.append(f"{label} {round(pct)}%")
    print(" | ".join(parts))


if __name__ == "__main__":
    main()
