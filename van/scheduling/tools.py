from apscheduler.schedulers.asyncio import AsyncIOScheduler
from fastapi import APIRouter, Depends

schedule_urls = APIRouter(prefix='/schedule')
scheduler = AsyncIOScheduler()


def get_scheduler() -> AsyncIOScheduler:
    return scheduler
