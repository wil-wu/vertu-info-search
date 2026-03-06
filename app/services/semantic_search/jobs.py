import logging

from apscheduler.triggers.cron import CronTrigger

from app.core.shared import meili_client, httpx_sync_client, scheduler
from .config import semantic_search_settings

logger = logging.getLogger(__name__)


def update_product_realtime_info_job():
    """
    更新产品实时信息
    """
    logger.info("--- [JOB] 更新产品实时信息 ---")

    products = []
    page = 1
    per_page = 50

    while True:
        response = httpx_sync_client.get(
            f"{semantic_search_settings.product_info_url}/products",
            headers={"Authorization": f"Basic {semantic_search_settings.product_info_token}"},
            params={"page": page, "per_page": per_page},
            timeout=20,
        )

        for product in response.json():
            price = product.get("price")
            try:
                price = float(price)
            except ValueError:
                continue
            
            products.append({
                "id": product.get("id"),
                "name": product.get("name"),
                "price": price,
            })

        logger.info(f"--- [JOB] 更新产品实时信息: {len(products)} 条 ---")

        if len(response.json()) < per_page:
            break
        page += 1
    
    if not products:
        logger.warning("--- [JOB] 无产品数据，跳过索引更新 ---")
        return

    tmp_index = meili_client.index("overseas_product_tmp")
    add_task_info = tmp_index.add_documents(products)
    add_task = meili_client.wait_for_task(add_task_info.task_uid)
    if add_task.status != "succeeded":
        logger.warning("--- [JOB] 写入临时索引失败，中止: %s ---", add_task.details)
        return

    swap_task_info = meili_client.swap_indexes([
        {"indexes": ["overseas_product", "overseas_product_tmp"]}
    ])
    swap_task = meili_client.wait_for_task(swap_task_info.task_uid)
    if swap_task.status != "succeeded":
        logger.warning("--- [JOB] 交换索引失败，保留临时索引: %s ---", swap_task.details)
        return

    tmp_index.delete()

    logger.info("--- [JOB] 更新产品实时信息完成 ---")


scheduler.add_job(
    update_product_realtime_info_job, 
    CronTrigger.from_crontab(semantic_search_settings.product_info_crontab)
)
