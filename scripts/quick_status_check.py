#!/usr/bin/env python3
"""
Quick Status Check Script
PERMANENT SCRIPT - Should be committed to repo

Fast production status check for monitoring and alerts.
Returns simple pass/fail without detailed output.

Usage:
    python scripts/quick_status_check.py
    
Exit codes:
    0 = All critical systems operational
    1 = Critical system failure
    2 = Degraded performance
"""

import requests
import sys
import json
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


def quick_check(base_url="https://theperspectiveshift.vercel.app"):
    """Perform fast critical system checks"""
    
    # Configure session with retries
    session = requests.Session()
    retry_strategy = Retry(
        total=2,
        backoff_factor=0.5,
        status_forcelist=[429, 500, 502, 503, 504],
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    
    critical_checks = []
    warnings = []
    
    # Critical: Homepage loads
    try:
        resp = session.get(f"{base_url}/", timeout=10)
        if resp.status_code == 200:
            critical_checks.append(("Homepage", True))
        else:
            critical_checks.append(("Homepage", False))
    except:
        critical_checks.append(("Homepage", False))
    
    # Critical: Health endpoint
    try:
        resp = session.get(f"{base_url}/health", timeout=10)
        if resp.status_code == 200:
            health = resp.json()
            db_connected = health.get('database') == 'connected'
            critical_checks.append(("Database", db_connected))
            critical_checks.append(("Health API", True))
        else:
            critical_checks.append(("Health API", False))
            critical_checks.append(("Database", False))
    except:
        critical_checks.append(("Health API", False))
        critical_checks.append(("Database", False))
    
    # Critical: Image generation
    try:
        resp = session.get(f"{base_url}/image/51_0?design=3", timeout=15)
        critical_checks.append(("Image Generation", resp.status_code == 200))
    except:
        critical_checks.append(("Image Generation", False))
    
    # Warning: Share tracking
    try:
        resp = session.post(
            f"{base_url}/track-share/51_0",
            json={'platform': 'instagram'},
            headers={'Content-Type': 'application/json'},
            timeout=10
        )
        if resp.status_code == 200 and resp.json().get('status') == 'success':
            warnings.append(("Share Tracking", True))
        else:
            warnings.append(("Share Tracking", False))
    except:
        warnings.append(("Share Tracking", False))
    
    # Determine status
    critical_failures = [name for name, passed in critical_checks if not passed]
    warning_failures = [name for name, passed in warnings if not passed]
    
    if critical_failures:
        print(f"CRITICAL: {', '.join(critical_failures)} failed")
        return 1
    elif warning_failures:
        print(f"DEGRADED: {', '.join(warning_failures)} issues")
        return 2
    else:
        print("OK: All systems operational")
        return 0


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Quick production status check')
    parser.add_argument('--url', default='https://theperspectiveshift.vercel.app',
                       help='Base URL to check')
    parser.add_argument('--quiet', '-q', action='store_true',
                       help='Suppress output, only return exit code')
    
    args = parser.parse_args()
    
    exit_code = quick_check(args.url)
    
    if not args.quiet:
        if exit_code == 0:
            print("✅ Production healthy")
        elif exit_code == 1:
            print("❌ Critical failure - immediate attention needed")
        elif exit_code == 2:
            print("⚠️ Degraded performance - monitor closely")
    
    sys.exit(exit_code)