"""
Wearable sync orchestration service.

Manages provider registry, account connections, and sync jobs.
"""

from __future__ import annotations

import json
from datetime import date, timedelta, datetime
from typing import Any, Dict, Optional
from uuid import UUID

import structlog

from app.config import settings
from app.services.supabase_service import supabase_service
from app.services.wearables.base import wearable_registry
from app.services.wearables.garmin_garmy_provider import provider as garmin_provider
from app.utils.crypto import encrypt_text, decrypt_text

logger = structlog.get_logger()


class WearableSyncService:
    def __init__(self) -> None:
        # Register available providers
        wearable_registry.register(garmin_provider)
        self.db = supabase_service.client

    def _now(self) -> datetime:
        return datetime.utcnow()

    async def connect_account(self, user_id: UUID, provider: str, credentials: Dict[str, Any]) -> Dict[str, Any]:
        """Connect or update a wearable account for a user.

        Stores encrypted credentials when WEARABLE_CRED_SECRET is configured.
        """
        status = "connected"
        cred_blob: Optional[str] = None

        # Encrypt credentials if possible, otherwise mark configured_missing_secret
        try:
            serialized = json.dumps(credentials)
            cred_blob = encrypt_text(serialized)
            if cred_blob is None:
                status = "configured_missing_secret"
        except Exception as e:
            logger.error("credential_encrypt_failed", error=str(e))
            status = "configured_missing_secret"

        data = {
            "user_id": str(user_id),
            "provider": (provider or "").lower(),
            "status": status,
            "credentials_encrypted": cred_blob,
            "updated_at": self._now().isoformat(),
        }

        # Manual upsert to avoid SDK on_conflict quirks: UPDATE then INSERT if no rows affected
        try:
            # Attempt update first
            update_fields = {
                "status": data["status"],
                "credentials_encrypted": data.get("credentials_encrypted"),
                "updated_at": data["updated_at"],
            }
            upd = (
                self.db
                .table("wearable_accounts")
                .update(update_fields)
                .eq("user_id", str(user_id))
                .eq("provider", data["provider"])
                .execute()
            )

            if upd.data and len(upd.data) > 0:
                return upd.data[0]

            # No row updated, insert new
            ins = (
                self.db
                .table("wearable_accounts")
                .insert(data)
                .execute()
            )
            return ins.data[0] if ins.data else data
        except Exception as e:
            logger.error(
                "wearable_account_upsert_failed",
                error=str(e),
                provider=data["provider"],
                user_id=str(user_id),
            )
            raise

    async def start_sync(self, user_id: UUID, provider: str, days: int = 7) -> Dict[str, Any]:
        """Start a sync job synchronously (MVP). Returns job record."""
        job = {
            "user_id": str(user_id),
            "provider": provider,
            "status": "running",
            "started_at": self._now().isoformat(),
            "stats": {},
        }
        job_resp = self.db.table("wearable_sync_jobs").insert(job).execute()
        job_id = job_resp.data[0]["id"] if job_resp.data else None

        try:
            # Load account to get credentials
            acc = (
                self.db.table("wearable_accounts")
                .select("*")
                .eq("user_id", str(user_id))
                .eq("provider", provider)
                .single()
                .execute()
            ).data

            creds: Dict[str, Any] = {}
            if acc and acc.get("credentials_encrypted"):
                plaintext = decrypt_text(acc["credentials_encrypted"]) or "{}"
                try:
                    creds = json.loads(plaintext)
                except Exception:
                    creds = {}

            prov = wearable_registry.get(provider)
            if not prov:
                raise RuntimeError(f"Provider not available: {provider}")

            ok, err = await prov.authenticate(creds)
            if not ok:
                # Categorize auth errors for better user feedback
                if err in ["credentials_expired", "authentication_failed"]:
                    # Update account status to indicate re-auth needed
                    self.db.table("wearable_accounts").update({
                        "status": "auth_required",
                        "error_message": "Please reconnect your account - credentials have expired",
                        "updated_at": self._now().isoformat()
                    }).eq("user_id", str(user_id)).eq("provider", provider).execute()
                elif err == "rate_limited":
                    # Temporary error - don't change account status
                    logger.warning("wearable_rate_limited", provider=provider, user_id=str(user_id))
                elif err == "connection_error":
                    # Network issue - don't change account status
                    logger.warning("wearable_connection_error", provider=provider, user_id=str(user_id))

                raise RuntimeError(f"Auth failed: {err}")

            end = date.today()
            start = end - timedelta(days=days)
            stats = await prov.sync_range(user_id, start, end)

            # Persist results
            activities = stats.get('activities') or []
            health = stats.get('health_metrics') or []

            from app.services.supabase_service import SupabaseService
            s = SupabaseService()
            if activities:
                await s.upsert_activities_wearable(activities)
            if health:
                await s.create_health_metrics_bulk(health)

            # Finish job
            finish = {
                "status": "success",
                "finished_at": self._now().isoformat(),
                "stats": {**(stats or {}), "persisted": {"activities": len(activities), "health": len(health)}},
            }
            self.db.table("wearable_sync_jobs").update(finish).eq("id", job_id).execute()

            # Update last_sync_at on account
            self.db.table("wearable_accounts").update({"last_sync_at": self._now().isoformat(), "status": "connected"}).eq("user_id", str(user_id)).eq("provider", provider).execute()

            return {"id": job_id, **finish}

        except Exception as e:
            error_msg = str(e)

            # Categorize errors for appropriate logging and status updates
            is_auth_error = any(x in error_msg.lower() for x in ["auth failed", "credentials_expired", "unauthorized", "401"])
            is_rate_limit = any(x in error_msg.lower() for x in ["rate_limited", "rate limit", "429"])
            is_network_error = any(x in error_msg.lower() for x in ["connection_error", "timeout", "network"])

            # Log with appropriate level
            if is_rate_limit or is_network_error:
                logger.warning("wearable_sync_temporary_error", error=error_msg, user_id=str(user_id), provider=provider)
            else:
                logger.error("wearable_sync_failed", error=error_msg, user_id=str(user_id), provider=provider)

            # Update job status
            self.db.table("wearable_sync_jobs").update({
                "status": "error",
                "finished_at": self._now().isoformat(),
                "error_message": error_msg
            }).eq("id", job_id).execute()

            # Only update account status for auth errors (already handled above)
            # Don't mark account as "error" for temporary network/rate limit issues
            if not (is_rate_limit or is_network_error or is_auth_error):
                self.db.table("wearable_accounts").update({
                    "status": "error",
                    "error_message": error_msg
                }).eq("user_id", str(user_id)).eq("provider", provider).execute()

            return {"id": job_id, "status": "error", "error": error_msg}

    async def get_status(self, user_id: UUID) -> Dict[str, Any]:
        accs = (
            self.db.table("wearable_accounts")
            .select("*")
            .eq("user_id", str(user_id))
            .execute()
        ).data or []

        latest_job = (
            self.db.table("wearable_sync_jobs")
            .select("*")
            .eq("user_id", str(user_id))
            .order("created_at", desc=True)
            .limit(1)
            .execute()
        ).data

        return {
            "accounts": accs,
            "latest_job": latest_job[0] if latest_job else None,
            "providers": wearable_registry.list(),
        }


wearable_sync_service = WearableSyncService()
