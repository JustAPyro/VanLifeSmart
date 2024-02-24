from apscheduler.job import Job
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from fastapi import APIRouter, Depends

from .tools import get_scheduler

schedule_urls = APIRouter(prefix='/schedule')


def schedule_info(job: Job):
    print(job)
    return {
        'description': job.name,
        'trigger': str(job.trigger),
        'next_run_time': job.next_run_time,
        'max_instances': job.max_instances,
        'misfire_grace_time': job.misfire_grace_time
    }


@schedule_urls.get(".json")
async def read_users(scheduler: AsyncIOScheduler = Depends(get_scheduler)):
    return [schedule_info(job) for job in scheduler.get_jobs()]
