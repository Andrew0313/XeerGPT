"""
Usage Tracker - Tracks API usage per provider with rate limit reset times
FIXED VERSION - Proper persistence and date handling
Groq: 14,400 requests/day (resets midnight UTC)
OpenRouter: 200 requests/day free tier (resets midnight UTC)
"""

import json
import os
from datetime import datetime, timezone, timedelta
from pathlib import Path

# Use absolute path to prevent file location issues
BASE_DIR = Path(__file__).resolve().parent
USAGE_FILE = BASE_DIR / "usage_data.json"

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
    """Load usage data from file with proper error handling"""
    if not USAGE_FILE.exists():
        print(f"📂 Creating new usage file: {USAGE_FILE}")
        return {}
    try:
        with open(USAGE_FILE, "r") as f:
            data = json.load(f)
            print(f"📊 Loaded usage data: {data}")
            return data
    except json.JSONDecodeError:
        print(f"⚠️ Corrupted usage file, resetting")
        return {}
    except Exception as e:
        print(f"⚠️ Error loading usage data: {e}")
        return {}

def _save_data(data):
    """Save usage data to file with atomic write"""
    try:
        # Ensure directory exists
        USAGE_FILE.parent.mkdir(parents=True, exist_ok=True)
        
        # Write to temp file first, then rename (atomic)
        temp_file = USAGE_FILE.with_suffix('.tmp')
        with open(temp_file, "w") as f:
            json.dump(data, f, indent=2)
        
        # Atomic rename
        temp_file.replace(USAGE_FILE)
        print(f"💾 Saved usage data: {data}")
    except Exception as e:
        print(f"❌ Could not save usage data: {e}")

def _get_today_key():
    """Get today's date key in UTC (YYYY-MM-DD format)"""
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    print(f"📅 Today's date key: {today}")
    return today

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
    """
    Record one API call for the given provider
    FIXED: Properly handles date transitions and persistence
    """
    data = _load_data()
    today = _get_today_key()

    # Initialize provider if not exists
    if provider_key not in data:
        data[provider_key] = {
            "date": today,
            "count": 0
        }
        print(f"🆕 Initialized tracking for {provider_key}")

    # Check if we need to reset (new day)
    stored_date = data[provider_key].get("date")
    if stored_date != today:
        print(f"🔄 New day detected for {provider_key}: {stored_date} → {today}")
        data[provider_key] = {
            "date": today,
            "count": 0
        }

    # Increment count
    old_count = data[provider_key].get("count", 0)
    data[provider_key]["count"] = old_count + 1
    
    # CRITICAL: Save immediately to disk
    _save_data(data)
    
    new_count = data[provider_key]["count"]
    print(f"📈 {provider_key}: {old_count} → {new_count}")
    
    return new_count

def get_usage_stats():
    """
    Return full usage stats for all providers
    FIXED: Properly handles stale data and resets
    """
    data = _load_data()
    today = _get_today_key()
    stats = {}

    for provider_key, provider_info in PROVIDER_LIMITS.items():
        provider_data = data.get(provider_key, {})

        # Check if data is from today
        stored_date = provider_data.get("date")
        if stored_date != today:
            # Stale data - reset to 0
            count = 0
            print(f"🔄 Resetting stale data for {provider_key}: {stored_date} → {today}")
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
    print(f"🔄 Manually reset {provider_key}")

def get_debug_info():
    """Get debug information about usage tracking"""
    data = _load_data()
    today = _get_today_key()
    
    debug = {
        "file_path": str(USAGE_FILE),
        "file_exists": USAGE_FILE.exists(),
        "current_utc_date": today,
        "raw_data": data
    }
    
    return debug