#!/usr/bin/env python3
"""
Run daily adjustments for all users with active programs.

Usage:
  python -m scripts.daily_adjuster

Requires SUPABASE_URL and SUPABASE_SERVICE_KEY in env.
"""

import os
import sys
import structlog
from app.services.supabase_service import SupabaseService
from app.services.daily_adjuster_service import DailyAdjusterService

logger = structlog.get_logger()


def main():
    db = SupabaseService()
    client = db.client

    # Fetch active programs (last 1 day created or valid)
    progs = client.table("programs").select("id, user_id, program_start_date, valid_until") \
        .order("created_at", desc=True).limit(1000).execute().data

    svc = DailyAdjusterService(db)
    count = 0
    for p in progs:
        try:
            res = svc.adjust_today(p["user_id"], p["id"])
            logger.info("daily_adjustment", user_id=p["user_id"], program_id=p["id"], result=res)
            count += 1
        except Exception as e:
            logger.error("daily_adjustment_failed", user_id=p["user_id"], program_id=p["id"], error=str(e))

    logger.info("daily_adjuster_complete", processed=count)


if __name__ == "__main__":
    main()

