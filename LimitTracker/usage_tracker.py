"""
Usage Tracker - Tracks API usage per provider with rate limit reset times
Groq: 14,400 requests/day (resets midnight UTC)
OpenRouter: 200 requests/day free tier (resets midnight UTC)
"""

import json
import os
from datetime import datetime, timezone, timedelta

USAGE_FILE = "usage_data.json"

# Provider limits (adjust these to match your actual plan)
PROVIDER_LIMITS = {
    "groq": {
        "display_name": "Groq",
        "icon": "⚡",
        "daily_limit": 14400,      # Groq free tier: 14,400 req/day
        "reset_hour_utc": 0,       # Resets at midnight UTC
        "color": "#10a37f"
    },
    "openrouter": {
        "display_name": "OpenRouter",
        "icon": "🔀",
        "daily_limit": 200,        # OpenRouter free tier: 200 req/day
        "reset_hour_utc": 0,
        "color": "#6366f1"
    }
}

def _load_data():
    """Load usage data from file"""
    if not os.path.exists(USAGE_FILE):
        return {}
    try:
        with open(USAGE_FILE, "r") as f:
            return json.load(f)
    except Exception:
        return {}

def _save_data(data):
    """Save usage data to file"""
    try:
        with open(USAGE_FILE, "w") as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        print(f"⚠️ Could not save usage data: {e}")

def _get_today_key():
    """Get today's date key in UTC"""
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")

def _get_reset_time(provider_key):
    """Get the next reset datetime for a provider (midnight UTC)"""
    now = datetime.now(timezone.utc)
    # Next midnight UTC
    tomorrow = (now + timedelta(days=1)).replace(
        hour=0, minute=0, second=0, microsecond=0
    )
    return tomorrow

def _get_reset_time_local(provider_key):
    """Get reset time as local time string (Malaysia UTC+8)"""
    reset_utc = _get_reset_time(provider_key)
    # Convert to Malaysia time (UTC+8)
    malaysia_offset = timedelta(hours=8)
    reset_local = reset_utc + malaysia_offset
    return reset_local.strftime("%I:%M %p MYT")

def _seconds_until_reset(provider_key):
    """Seconds until the next reset"""
    reset_utc = _get_reset_time(provider_key)
    now = datetime.now(timezone.utc)
    delta = reset_utc - now
    return max(0, int(delta.total_seconds()))

def _format_countdown(seconds):
    """Format seconds into h m s string"""
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60
    if hours > 0:
        return f"{hours}h {minutes}m"
    elif minutes > 0:
        return f"{minutes}m {secs}s"
    else:
        return f"{secs}s"

def record_usage(provider_key: str):
    """Record one API call for the given provider"""
    data = _load_data()
    today = _get_today_key()

    if provider_key not in data:
        data[provider_key] = {}

    # Auto-reset if it's a new day
    if "date" not in data[provider_key] or data[provider_key]["date"] != today:
        data[provider_key] = {
            "date": today,
            "count": 0
        }

    data[provider_key]["count"] = data[provider_key].get("count", 0) + 1
    _save_data(data)
    return data[provider_key]["count"]

def get_usage_stats():
    """Return full usage stats for all providers"""
    data = _load_data()
    today = _get_today_key()
    stats = {}

    for provider_key, provider_info in PROVIDER_LIMITS.items():
        provider_data = data.get(provider_key, {})

        # Reset if stale date
        if provider_data.get("date") != today:
            count = 0
        else:
            count = provider_data.get("count", 0)

        limit = provider_info["daily_limit"]
        remaining = max(0, limit - count)
        percent_used = min(100, round((count / limit) * 100, 1))
        seconds_left = _seconds_until_reset(provider_key)

        stats[provider_key] = {
            "display_name": provider_info["display_name"],
            "icon": provider_info["icon"],
            "color": provider_info["color"],
            "used": count,
            "limit": limit,
            "remaining": remaining,
            "percent_used": percent_used,
            "percent_remaining": round(100 - percent_used, 1),
            "reset_in_seconds": seconds_left,
            "reset_countdown": _format_countdown(seconds_left),
            "reset_time_local": _get_reset_time_local(provider_key),
            "status": _get_status(percent_used)
        }

    return stats

def _get_status(percent_used):
    """Return status label based on usage percent"""
    if percent_used >= 95:
        return "critical"
    elif percent_used >= 75:
        return "warning"
    elif percent_used >= 50:
        return "moderate"
    else:
        return "good"

def reset_provider(provider_key: str):
    """Manually reset a provider's usage (admin use)"""
    data = _load_data()
    today = _get_today_key()
    data[provider_key] = {"date": today, "count": 0}
    _save_data(data)