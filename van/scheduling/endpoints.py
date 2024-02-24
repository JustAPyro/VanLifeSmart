from apscheduler.schedulers.asyncio import AsyncIOScheduler
from fastapi import APIRouter, Depends

from .tools import get_scheduler, schedule_info

schedule_urls = APIRouter(prefix='/schedule')


@schedule_urls.get('.json')
async def all_schedules(scheduler: AsyncIOScheduler = Depends(get_scheduler)):
    return [schedule_info(job) for job in scheduler.get_jobs()]


@schedule_urls.get('/{schedule_id}.json')
async def schedule(schedule_id: str, scheduler: AsyncIOScheduler = Depends(get_scheduler)):
    return schedule_info(scheduler.get_job(schedule_id))
