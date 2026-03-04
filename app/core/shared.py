from meilisearch import Client

from app.config import settings

meili_client = Client(settings.meilisearch_host, settings.meilisearch_api_key)
