from fastapi import APIRouter

schedule_urls = APIRouter(prefix='schedule')


@schedule_urls.get("all.json")
async def read_users():
    return [{"username": "Rick"}, {"username": "Morty"}]
