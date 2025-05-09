import requests
from celery import shared_task

# import models
from members.models import Member


@shared_task(time_limit=30, max_retries=0, name="members.get_city")
def get_city_from_zip(member_pk) -> None:
    """Get city and state from zip code using Zippopotam API"""
    member: Member = Member.objects.get(pk=member_pk)
    url: str = f"http://api.zippopotam.us/us/{member.zip_code}"
    response: requests.Response = requests.get(url, timeout=10)
    if response.status_code == 200:
        data: dict = response.json()
        city: str = data["places"][0]["place name"]
        state: str = data["places"][0]["state abbreviation"]
        member.city = city
        member.state = state
        member.save()
