from apscheduler.job import Job
from fastapi import APIRouter
from local_server import scheduler

schedule_urls = APIRouter(prefix='/schedule')


def schedule_info(job: Job):
    return {
        'description': job.name,
        'trigger': str(job.trigger),
        'next_run_time': job.next_run_time,
        'max_instances': job.max_instances,
        'misfire_grace_time': job.misfire_grace_time
    }


@schedule_urls.get(".json")
async def read_users():
    return [schedule_info(job) for job in scheduler.get_jobs()]
