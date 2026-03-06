from meilisearch import Client
from apscheduler.schedulers.background import BackgroundScheduler
from httpx import Client as HttpxClient

from app.config import settings

meili_client = Client(settings.meilisearch_host, settings.meilisearch_api_key)

scheduler = BackgroundScheduler()

httpx_sync_client = HttpxClient()
