"""
Timezone-Aware Scheduler
Handles scheduling of digest notifications with proper timezone support for IST.
"""

import logging
from datetime import datetime, time
from typing import Optional, Dict, Any, Callable
import pytz
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

logger = logging.getLogger(__name__)


class TimezoneScheduler:
    """
    Scheduler with timezone support for IST (Indian Standard Time).
    Ensures digest notifications are sent at correct local times.
    """

    def __init__(self, timezone: str = 'Asia/Kolkata'):
        """
        Initialize the timezone-aware scheduler.
        
        Args:
            timezone: Timezone string (default: 'Asia/Kolkata' for IST)
        """
        self.timezone = pytz.timezone(timezone)
        self.scheduler = BackgroundScheduler(timezone=self.timezone)
        self.jobs = {}
        logger.info(f"TimezoneScheduler initialized with timezone: {timezone}")

    def add_digest_job(self, 
                       digest_type: str, 
                       schedule_config: Dict[str, Any], 
                       callback: Callable) -> bool:
        """
        Add a digest job based on configuration.
        
        Args:
            digest_type: Type of digest (e.g., 'morning', 'evening')
            schedule_config: Schedule configuration dict with 'time', 'enabled', etc.
            callback: Function to call when job triggers
            
        Returns:
            bool: True if job was added successfully
        """
        if not schedule_config.get('enabled', False):
            logger.info(f"Digest '{digest_type}' is disabled, skipping schedule")
            return False
        
        time_str = schedule_config.get('time')
        if not time_str:
            logger.error(f"No time specified for digest '{digest_type}'")
            return False
        
        try:
            # Parse time string (e.g., '06:50' or '16:10')
            hour, minute = map(int, time_str.split(':'))
            
            # Get timezone from config or use default
            config_tz = schedule_config.get('timezone', 'Asia/Kolkata')
            job_timezone = pytz.timezone(config_tz)
            
            # Create cron trigger with timezone
            trigger = CronTrigger(
                hour=hour,
                minute=minute,
                timezone=job_timezone
            )
            
            # Remove existing job if present
            job_id = f"digest_{digest_type}"
            if job_id in self.jobs:
                self.scheduler.remove_job(job_id)
                logger.info(f"Removed existing job: {job_id}")
            
            # Add new job
            job = self.scheduler.add_job(
                callback,
                trigger=trigger,
                id=job_id,
                name=f"{digest_type.capitalize()} Digest",
                replace_existing=True
            )
            
            self.jobs[job_id] = job
            
            # Log in both UTC and local timezone for clarity
            now_utc = datetime.now(pytz.UTC)
            now_local = now_utc.astimezone(job_timezone)
            
            logger.info(
                f"Scheduled '{digest_type}' digest at {time_str} {config_tz} "
                f"(Current local time: {now_local.strftime('%H:%M:%S %Z')})"
            )
            
            return True
            
        except ValueError as e:
            logger.error(f"Invalid time format for digest '{digest_type}': {time_str} - {e}")
            return False
        except Exception as e:
            logger.error(f"Failed to schedule digest '{digest_type}': {e}")
            return False

    def start(self):
        """Start the scheduler."""
        if not self.scheduler.running:
            self.scheduler.start()
            logger.info("TimezoneScheduler started")
        else:
            logger.warning("TimezoneScheduler already running")

    def stop(self):
        """Stop the scheduler."""
        if self.scheduler.running:
            self.scheduler.shutdown()
            logger.info("TimezoneScheduler stopped")

    def get_next_run_time(self, digest_type: str) -> Optional[datetime]:
        """
        Get the next scheduled run time for a digest.
        
        Args:
            digest_type: Type of digest
            
        Returns:
            Next run time as datetime, or None if not scheduled
        """
        job_id = f"digest_{digest_type}"
        job = self.jobs.get(job_id)
        
        if job:
            return job.next_run_time
        
        return None

    def get_scheduled_jobs(self) -> Dict[str, Dict[str, Any]]:
        """
        Get information about all scheduled jobs.
        
        Returns:
            Dictionary of job information
        """
        jobs_info = {}
        
        for job_id, job in self.jobs.items():
            next_run = job.next_run_time
            jobs_info[job_id] = {
                'name': job.name,
                'next_run_utc': next_run.isoformat() if next_run else None,
                'next_run_local': next_run.astimezone(self.timezone).strftime('%Y-%m-%d %H:%M:%S %Z') if next_run else None
            }
        
        return jobs_info

    def convert_utc_to_local(self, utc_time: datetime) -> datetime:
        """
        Convert UTC time to local timezone.
        
        Args:
            utc_time: UTC datetime
            
        Returns:
            Local datetime
        """
        if utc_time.tzinfo is None:
            utc_time = pytz.UTC.localize(utc_time)
        return utc_time.astimezone(self.timezone)

    def convert_local_to_utc(self, local_time: datetime) -> datetime:
        """
        Convert local time to UTC.
        
        Args:
            local_time: Local datetime
            
        Returns:
            UTC datetime
        """
        if local_time.tzinfo is None:
            local_time = self.timezone.localize(local_time)
        return local_time.astimezone(pytz.UTC)
