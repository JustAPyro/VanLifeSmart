from apscheduler.job import Job
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from fastapi import APIRouter

schedule_urls = APIRouter(prefix='/schedule')
scheduler = AsyncIOScheduler()


def get_scheduler() -> AsyncIOScheduler:
    return scheduler


def schedule_info(job: Job):
    return {
        'id': job.id,
        'description': job.name,
        'trigger': str(job.trigger),
        'next_run_time': job.next_run_time,
        'max_instances': job.max_instances,
        'misfire_grace_time': job.misfire_grace_time,
        'active': 'True'
    }
