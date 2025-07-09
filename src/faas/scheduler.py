from apscheduler.schedulers.asyncio import AsyncIOScheduler
from datetime import timezone

scheduler = AsyncIOScheduler(timezone=timezone.utc)