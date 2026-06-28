from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from mangum import Mangum
import logging
from .utils import cached_data

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def get_status():
    """获取数据更新状态"""
    return {
        "status": cached_data.get('status', 'ready'),
        "update_time": cached_data.get('update_time'),
        "ttm_count": len(cached_data.get('ttm', [])),
        "lfy_count": len(cached_data.get('lfy', []))
    }


handler = Mangum(app)