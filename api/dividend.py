from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from mangum import Mangum
import logging
from .utils import cached_data, get_stock_data

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
async def get_dividend_data():
    """获取股息率数据API"""
    global cached_data

    if not cached_data['ttm'] or not cached_data['lfy']:
        get_stock_data()

    return {
        "success": True,
        "status": "ready",
        "data": {
            "ttm": cached_data['ttm'],
            "lfy": cached_data['lfy']
        },
        "update_time": cached_data['update_time']
    }


handler = Mangum(app)