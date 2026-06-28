"""
A股股息率排名后端服务
从 akshare 获取数据，计算 TTM 和 LFY 股息率排名
"""
from typing import Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import akshare as ak
import pandas as pd
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="A股股息率排名")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

MARKET_CAP_THRESHOLD = 1e11  # 1000亿


def fetch_dividend_data(code: str, name: str, market_cap: float, latest_price: float) -> Optional[dict]:
    """获取单只股票的分红数据并计算股息率"""
    try:
        div_df = ak.stock_fhps_detail_em(symbol=code)
        if div_df is None or div_df.empty:
            return None

        div_df = div_df.copy()

        # akshare 列名是固定的
        date_col = "除权除息日"
        dividend_col = "现金分红-现金分红比例"

        if date_col not in div_df.columns or dividend_col not in div_df.columns:
            return None

        div_df[date_col] = pd.to_datetime(div_df[date_col], errors="coerce")
        div_df = div_df.dropna(subset=[date_col, dividend_col])
        div_df[dividend_col] = pd.to_numeric(div_df[dividend_col], errors="coerce")
        div_df = div_df.dropna(subset=[dividend_col])

        if div_df.empty:
            return None

        # 现金分红比例是"每10股派X元"，需要除以10得到每股分红
        div_df["每股分红"] = div_df[dividend_col] / 10.0

        today = datetime.now()

        # TTM：过去12个月的分红总和
        one_year_ago = today - timedelta(days=365)
        ttm_mask = div_df[date_col] >= one_year_ago
        ttm_dividends = float(div_df.loc[ttm_mask, "每股分红"].sum())

        # LFY：最近一个完整财年的分红总和
        current_year = today.year
        last_fy_start = datetime(current_year - 1, 1, 1)
        last_fy_end = datetime(current_year - 1, 12, 31)
        lfy_mask = (div_df[date_col] >= last_fy_start) & (div_df[date_col] <= last_fy_end)
        lfy_dividends = float(div_df.loc[lfy_mask, "每股分红"].sum())

        # 如果没有LFY数据，尝试使用上一个财年
        if lfy_dividends == 0:
            prev_fy_start = datetime(current_year - 2, 1, 1)
            prev_fy_end = datetime(current_year - 2, 12, 31)
            prev_mask = (div_df[date_col] >= prev_fy_start) & (div_df[date_col] <= prev_fy_end)
            lfy_dividends = float(div_df.loc[prev_mask, "每股分红"].sum())

        ttm_yield = (ttm_dividends / latest_price) * 100 if ttm_dividends > 0 else 0
        lfy_yield = (lfy_dividends / latest_price) * 100 if lfy_dividends > 0 else 0

        return {
            "code": code,
            "name": name,
            "market_cap": round(market_cap / 1e8, 2),
            "latest_price": round(latest_price, 2),
            "ttm_dividends": round(ttm_dividends, 4),
            "lfy_dividends": round(lfy_dividends, 4),
            "ttm_yield": round(ttm_yield, 2),
            "lfy_yield": round(lfy_yield, 2),
        }
    except Exception as e:
        logger.warning(f"获取 {code} {name} 分红数据失败: {e}")
        return None


@app.get("/api/dividend/rankings")
async def get_dividend_rankings():
    """获取股息率排名数据"""
    try:
        logger.info("正在获取A股全量数据...")
        df = ak.stock_zh_a_spot_em()

        if df is None or df.empty:
            raise HTTPException(status_code=500, detail="无法获取A股数据")

        # 筛选市值大于1000亿
        df_large = df[df["总市值"] > MARKET_CAP_THRESHOLD].copy()
        logger.info(f"市值>1000亿的公司数量: {len(df_large)}")

        if df_large.empty:
            return {
                "success": True,
                "ttm_ranking": [],
                "lfy_ranking": [],
                "total_count": 0,
                "message": "没有市值大于1000亿的公司",
            }

        # 构建代码->价格的映射
        price_map: dict[str, float] = {}
        for _, row in df_large.iterrows():
            code = str(row["代码"])
            try:
                price_map[code] = float(row["最新价"])
            except (ValueError, TypeError):
                price_map[code] = 0.0

        # 并发获取分红数据
        results: list[dict] = []
        stocks = [
            (str(row["代码"]), str(row["名称"]), float(row["总市值"]), price_map.get(str(row["代码"]), 0.0))
            for _, row in df_large.iterrows()
        ]

        with ThreadPoolExecutor(max_workers=8) as executor:
            futures = {
                executor.submit(fetch_dividend_data, code, name, mcap, price): code
                for code, name, mcap, price in stocks
            }
            for future in as_completed(futures):
                result = future.result()
                if result is not None:
                    results.append(result)

        logger.info(f"成功获取 {len(results)} 只股票的分红数据")

        # TTM 股息率排名（前30）- 深拷贝避免共享引用
        ttm_sorted = sorted(
            [r for r in results if r["ttm_yield"] > 0],
            key=lambda x: x["ttm_yield"],
            reverse=True,
        )[:30]
        ttm_ranking = []
        for i, item in enumerate(ttm_sorted):
            ttm_ranking.append({**item, "rank": i + 1})

        # LFY 股息率排名（前30）
        lfy_sorted = sorted(
            [r for r in results if r["lfy_yield"] > 0],
            key=lambda x: x["lfy_yield"],
            reverse=True,
        )[:30]
        lfy_ranking = []
        for i, item in enumerate(lfy_sorted):
            lfy_ranking.append({**item, "rank": i + 1})

        return {
            "success": True,
            "ttm_ranking": ttm_ranking,
            "lfy_ranking": lfy_ranking,
            "total_count": len(df_large),
            "data_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }

    except Exception as e:
        logger.error(f"获取股息率排名失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/dividend/health")
async def health_check():
    """健康检查"""
    return {"status": "ok", "timestamp": datetime.now().isoformat()}
