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
async def refresh_data():
    """手动刷新数据"""
    global cached_data
    cached_data['ttm'] = []
    cached_data['lfy'] = []
    get_stock_data()

    return {
        "success": True,
        "message": "数据刷新完成"
    }


handler = Mangum(app)