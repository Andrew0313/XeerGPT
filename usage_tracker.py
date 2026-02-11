"""
Usage Tracker - DATABASE-BACKED VERSION
FIXED: Uses database instead of JSON file for persistent storage
Survives server restarts and deployments
"""

from datetime import datetime, timezone, timedelta
from models import db, UsageTracking

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

def _get_today_date():
    """Get today's date in UTC (date object, not string)"""
    return datetime.now(timezone.utc).date()

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
    FIXED: Uses database for persistence
    
    Args:
        provider_key: Provider identifier ('groq', 'openrouter', etc.)
    
    Returns:
        int: Current usage count for today
    """
    from app import app  # Import here to avoid circular dependency
    
    with app.app_context():
        today = _get_today_date()
        
        # Get or create usage record for this provider
        usage = UsageTracking.query.filter_by(provider=provider_key).first()
        
        if usage is None:
            # First time tracking this provider
            usage = UsageTracking(
                provider=provider_key,
                date=today,
                count=0
            )
            db.session.add(usage)
            print(f"🆕 Created usage tracking for {provider_key}")
        
        # Check if we need to reset (new day)
        if usage.date != today:
            print(f"🔄 New day detected for {provider_key}: {usage.date} → {today}")
            usage.date = today
            usage.count = 0
        
        # Increment count
        old_count = usage.count
        usage.count += 1
        
        # CRITICAL: Commit to database
        try:
            db.session.commit()
            print(f"📈 {provider_key}: {old_count} → {usage.count} (saved to DB)")
        except Exception as e:
            print(f"❌ Database error: {e}")
            db.session.rollback()
            raise
        
        return usage.count

def get_usage_stats():
    """
    Return full usage stats for all providers
    FIXED: Reads from database
    
    Returns:
        dict: Usage statistics for each provider
    """
    from app import app  # Import here to avoid circular dependency
    
    stats = {}
    
    with app.app_context():
        today = _get_today_date()
        
        for provider_key, provider_info in PROVIDER_LIMITS.items():
            # Get usage from database
            usage = UsageTracking.query.filter_by(provider=provider_key).first()
            
            # Check if data is from today
            if usage is None or usage.date != today:
                # No data or stale data - count is 0
                count = 0
                if usage and usage.date != today:
                    print(f"🔄 Stale data for {provider_key}: {usage.date} → {today}")
            else:
                count = usage.count
            
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
    """
    Manually reset a provider's usage (admin use)
    
    Args:
        provider_key: Provider to reset
    """
    from app import app
    
    with app.app_context():
        today = _get_today_date()
        usage = UsageTracking.query.filter_by(provider=provider_key).first()
        
        if usage:
            usage.date = today
            usage.count = 0
            db.session.commit()
            print(f"🔄 Manually reset {provider_key}")
        else:
            # Create new record
            usage = UsageTracking(
                provider=provider_key,
                date=today,
                count=0
            )
            db.session.add(usage)
            db.session.commit()
            print(f"🆕 Created and reset {provider_key}")

def get_debug_info():
    """Get debug information about usage tracking"""
    from app import app
    
    with app.app_context():
        today = _get_today_date()
        
        debug = {
            "storage": "database (SQLite)",
            "current_utc_date": str(today),
            "providers": {}
        }
        
        all_usage = UsageTracking.query.all()
        for usage in all_usage:
            debug["providers"][usage.provider] = {
                "date": str(usage.date),
                "count": usage.count,
                "is_today": usage.date == today,
                "updated_at": str(usage.updated_at)
            }
        
        return debug