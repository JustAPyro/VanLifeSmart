from fastapi import APIRouter

schedule_urls = APIRouter(prefix='/schedule')
from sensors import sensors
from local_server import scheduler


def schedule_info(job_id: str):
    job = scheduler.get_job(job_id)
    if not job:
        return {'error': 'could not find job', 'jobs': [{
            'id': job.id,
            'description': job.name
        } for job in scheduler.get_jobs()]}

    return {
        'description': job.name,
        'trigger': str(job.trigger),
        'next_run_time': job.next_run_time,
        'max_instances': job.max_instances,
        'misfire_grace_time': job.misfire_grace_time
    }


@schedule_urls.get(".json")
async def read_users():
    output = {'report': schedule_info('report')}
    return output
