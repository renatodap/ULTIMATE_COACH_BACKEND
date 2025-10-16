"""
Garmin provider via Garmy.

Feature-flagged; acts as a stub if Garmy is unavailable or disabled.
"""

from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID

import structlog

from app.config import settings
from app.services.wearables.base import WearableProvider

logger = structlog.get_logger()


class GarminGarmyProvider(WearableProvider):
    name = "garmin"

    def __init__(self) -> None:
        self._enabled = settings.GARMIN_ENABLED
        self._available = False
        self._client = None
        if self._enabled:
            try:
                from garmy import AuthClient, APIClient  # type: ignore

                self._AuthClient = AuthClient
                self._APIClient = APIClient
                self._available = True
            except Exception as e:  # ImportError or others
                logger.warning("garmy_import_failed", error=str(e))
                self._available = False

    async def authenticate(self, credentials: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        if not self._enabled:
            return False, "Garmin provider disabled"
        if not self._available:
            return False, "Garmy library not available"

        try:
            email = credentials.get("email")
            password = credentials.get("password")
            if not email or not password:
                return False, "Missing email/password"

            auth_client = self._AuthClient()
            api_client = self._APIClient(auth_client=auth_client)
            auth_client.login(email, password)
            self._client = api_client
            return True, None
        except Exception as e:
            error_str = str(e).lower()

            # Provide user-friendly error messages for common issues
            if '401' in error_str or 'unauthorized' in error_str:
                logger.warning("garmin_auth_expired", error=str(e))
                return False, "credentials_expired"
            elif '429' in error_str or 'rate limit' in error_str:
                logger.warning("garmin_rate_limited", error=str(e))
                return False, "rate_limited"
            elif 'timeout' in error_str or 'connection' in error_str:
                logger.warning("garmin_connection_failed", error=str(e))
                return False, "connection_error"
            else:
                logger.error("garmin_auth_failed", error=str(e))
                return False, "authentication_failed"

    async def sync_range(
        self, user_id: UUID, start: date, end: date, metrics: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Fetch Garmin data via Garmy and map to domain payloads.
        Returns dict with 'activities' and 'health_metrics'.
        """
        if not (self._enabled and self._available and self._client):
            logger.info("garmin_sync_skipped", enabled=self._enabled, available=self._available)
            return {"activities": [], "health_metrics": [], "counts": {"activities": 0}}

        logger.info("garmin_sync_range", user_id=str(user_id), start=str(start), end=str(end))

        api = self._client
        activities: List[Dict[str, Any]] = []
        health: List[Dict[str, Any]] = []

        # Helpers
        def iso(dt: datetime | str) -> str:
            if isinstance(dt, str):
                return dt
            return dt.isoformat()

        def map_category(garmin_type: str) -> str:
            g = (garmin_type or '').lower()
            if any(k in g for k in ['run', 'cycle', 'bike', 'walk', 'cardio']):
                return 'cardio_steady_state'
            if any(k in g for k in ['hiit', 'interval']):
                return 'cardio_interval'
            if any(k in g for k in ['strength', 'weights', 'resistance']):
                return 'strength_training'
            if any(k in g for k in ['yoga', 'stretch', 'mobility']):
                return 'flexibility'
            if any(k in g for k in ['tennis', 'basketball', 'soccer', 'sport']):
                return 'sports'
            return 'other'

        # Activities
        try:
            # Attempt to list activities in range; fallbacks are guarded
            act_metric = getattr(api, 'metrics', None)
            get_fn = getattr(act_metric, 'get', None)
            list_fn = getattr(act_metric, 'list', None)
            garmin_activities = []
            if act_metric and get_fn:
                # Many libs use metrics.get('activities').list(...)
                try:
                    acts = act_metric.get('activities')
                    if hasattr(acts, 'list'):
                        garmin_activities = acts.list(start=start, end=end)
                except Exception:
                    garmin_activities = []

            for a in garmin_activities or []:
                # Best-effort field extraction
                wearable_id = str(
                    a.get('ActivityId')
                    or a.get('activityId')
                    or a.get('id')
                    or ''
                )
                if not wearable_id:
                    continue
                name = (
                    a.get('ActivityName')
                    or a.get('activityName')
                    or a.get('name')
                    or 'Workout'
                )
                gtype = (
                    a.get('ActivityType')
                    or a.get('activityType')
                    or a.get('type')
                    or ''
                )

                # Timestamps: prefer Garmin export keys
                start_ts = a.get('StartTimeInSeconds')
                duration_sec = (
                    a.get('DurationInSeconds')
                    or a.get('duration')
                    or a.get('durationSec')
                )
                start_time = None
                end_time = None
                if start_ts is not None:
                    try:
                        start_dt = datetime.fromtimestamp(int(start_ts), tz=timezone.utc)
                        start_time = start_dt.isoformat()
                        if duration_sec:
                            end_dt = start_dt + timedelta(seconds=float(duration_sec))
                            end_time = end_dt.isoformat()
                    except Exception:
                        start_time = None
                        end_time = None
                else:
                    # Fallback to other keys
                    start_time = a.get('startTimeLocal') or a.get('startTimeGmt') or a.get('startTime')
                    end_time = a.get('endTimeLocal') or a.get('endTimeGmt') or a.get('endTime')
                    duration_sec = duration_sec

                calories = (
                    a.get('ActiveKilocalories')
                    or a.get('calories')
                    or a.get('caloriesBurned')
                )
                device = a.get('DeviceName') or a.get('deviceName') or a.get('device')
                url = a.get('activityUrl') or a.get('url')
                distance_m = (
                    a.get('DistanceInMeters')
                    or a.get('distance')
                    or a.get('distanceMeters')
                )
                avg_hr = (
                    a.get('AverageHeartRateInBeatsPerMinute')
                    or a.get('avgHR')
                    or a.get('averageHR')
                )
                max_hr = (
                    a.get('MaxHeartRateInBeatsPerMinute')
                    or a.get('maxHR')
                    or a.get('maxHeartRate')
                )
                elev_gain = (
                    a.get('TotalElevationGainInMeters')
                    or a.get('elevationGain')
                    or a.get('elevationGainMeters')
                )
                avg_speed_mps = a.get('AverageSpeedInMetersPerSecond')
                avg_pace_min_per_km = a.get('AveragePaceInMinutesPerKilometer')

                metrics_json: Dict[str, Any] = {}
                if distance_m is not None:
                    metrics_json['distance_km'] = round(float(distance_m) / 1000.0, 3)
                if avg_hr is not None:
                    metrics_json['avg_heart_rate'] = int(avg_hr)
                if max_hr is not None:
                    metrics_json['max_heart_rate'] = int(max_hr)
                if elev_gain is not None:
                    metrics_json['elevation_gain_m'] = float(elev_gain)

                # avg pace (min/km) if distance+duration present
                try:
                    if avg_pace_min_per_km is not None:
                        pace_min = float(avg_pace_min_per_km)
                        minutes = int(pace_min)
                        seconds = int(round((pace_min - minutes) * 60))
                        metrics_json['avg_pace'] = f"{minutes}:{str(seconds).zfill(2)}/km"
                    elif distance_m and duration_sec and float(distance_m) > 0:
                        pace_min = (float(duration_sec) / 60.0) / (float(distance_m) / 1000.0)
                        minutes = int(pace_min)
                        seconds = int(round((pace_min - minutes) * 60))
                        metrics_json['avg_pace'] = f"{minutes}:{str(seconds).zfill(2)}/km"
                except Exception:
                    pass

                # avg speed kph if provided in m/s
                try:
                    if avg_speed_mps is not None:
                        metrics_json['avg_speed_kph'] = round(float(avg_speed_mps) * 3.6, 2)
                except Exception:
                    pass

                # Optional steps
                if a.get('Steps') is not None:
                    metrics_json['steps'] = int(a.get('Steps'))

                activity_obj = {
                    'user_id': str(user_id),
                    'category': map_category(str(gtype)),
                    'activity_name': name,
                    'start_time': iso(start_time) if start_time else None,
                    'end_time': iso(end_time) if end_time else None,
                    'duration_minutes': int(round(float(duration_sec) / 60.0)) if duration_sec else None,
                    'calories_burned': int(calories) if calories is not None else None,
                    'intensity_mets': None,  # unknown; leave for estimator if needed
                    'metrics': metrics_json,
                    'notes': None,
                    'wearable_activity_id': wearable_id,
                    'device_name': device,
                    'wearable_url': url,
                    'raw_wearable_data': a,
                }
                activities.append(activity_obj)
        except Exception as e:
            logger.warning("garmin_fetch_activities_failed", error=str(e))

        # Heart rate / Stress / Sleep (daily-level examples)
        def as_dt(s: str) -> datetime:
            try:
                return datetime.fromisoformat(s.replace('Z', '+00:00'))
            except Exception:
                return datetime.utcnow()

        try:
            metrics_api = getattr(api, 'metrics', None)
            if metrics_api and hasattr(metrics_api, 'get'):
                # Heart rate daily
                try:
                    hr_api = metrics_api.get('heart_rate')
                    if hasattr(hr_api, 'list'):
                        hr_days = hr_api.list(start=start, end=end)
                        for d in hr_days or []:
                            recorded = d.get('day') or d.get('date') or d.get('timestamp')
                            if not recorded:
                                continue
                            value = {
                                'resting_hr': d.get('restingHR'),
                                'avg_hr': d.get('averageHR'),
                                'max_hr': d.get('maxHR'),
                            }
                            health.append({
                                'user_id': str(user_id),
                                'recorded_at': iso(recorded),
                                'metric_type': 'heart_rate',
                                'value': value,
                            })
                except Exception:
                    pass

                # Stress daily
                try:
                    stress_api = metrics_api.get('stress')
                    if hasattr(stress_api, 'list'):
                        st_days = stress_api.list(start=start, end=end)
                        for d in st_days or []:
                            recorded = d.get('day') or d.get('date') or d.get('timestamp')
                            if not recorded:
                                continue
                            value = {
                                'avg_stress': d.get('avgStressLevel'),
                                'max_stress': d.get('maxStressLevel'),
                            }
                            health.append({
                                'user_id': str(user_id),
                                'recorded_at': iso(recorded),
                                'metric_type': 'stress',
                                'value': value,
                            })
                except Exception:
                    pass

                # Sleep daily
                try:
                    sleep_api = metrics_api.get('sleep')
                    if hasattr(sleep_api, 'list') or hasattr(sleep_api, 'get'):
                        # Prefer list over range
                        sl_days = []
                        if hasattr(sleep_api, 'list'):
                            sl_days = sleep_api.list(start=start, end=end)
                        elif hasattr(sleep_api, 'get'):
                            # Get may accept date strings
                            cur = start
                            while cur <= end:
                                sl_days.extend(sleep_api.get(str(cur)))
                                cur = date.fromordinal(cur.toordinal() + 1)
                        for s in sl_days or []:
                            recorded = s.get('day') or s.get('date') or s.get('sleepDate')
                            if not recorded:
                                continue
                            value = {
                                'overall_sleep_score': s.get('overall_sleep_score') or s.get('score'),
                                'duration_minutes': s.get('durationMinutes') or s.get('duration'),
                                'stages': s.get('stages') or {},
                            }
                            health.append({
                                'user_id': str(user_id),
                                'recorded_at': iso(recorded),
                                'metric_type': 'sleep',
                                'value': value,
                            })
                except Exception:
                    pass

        except Exception as e:
            logger.warning("garmin_fetch_metrics_failed", error=str(e))

        return {"activities": activities, "health_metrics": health, "counts": {"activities": len(activities), "health": len(health)}}


provider = GarminGarmyProvider()
