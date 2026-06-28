import akshare as ak
import pandas as pd
import numpy as np
import re
from datetime import datetime, timedelta
from fastapi import FastAPI, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
import asyncio
import logging
import os
from threading import Lock
from concurrent.futures import ThreadPoolExecutor, as_completed

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

cached_data = {
    'ttm': [],
    'lfy': [],
    'update_time': None,
    'status': 'ready'
}
data_lock = Lock()


@app.get("/")
async def root():
    """提供首页"""
    return FileResponse(os.path.join(os.path.dirname(__file__), "index.html"))


def parse_dividend_per_share(description):
    """从分红说明中解析每股派息金额"""
    if pd.isna(description) or not isinstance(description, str):
        return 0.0
    
    # 匹配"10派X元"格式
    match = re.search(r'10派([\d.]+)元', description)
    if match:
        try:
            return float(match.group(1)) / 10
        except:
            pass
    
    # 匹配"派息比例"列
    return 0.0


def calculate_ttm_dividend(dividend_df):
    """计算TTM股息率 - 最近12个月的股息总和"""
    if dividend_df is None or dividend_df.empty:
        return 0.0, 0
    
    try:
        if '派息日' in dividend_df.columns:
            dividend_df = dividend_df.dropna(subset=['派息日'])
            if dividend_df.empty:
                return 0.0, 0
            
            dividend_df = dividend_df.copy()
            dividend_df['派息日'] = pd.to_datetime(dividend_df['派息日'], errors='coerce')
            dividend_df = dividend_df.dropna(subset=['派息日'])
            
            if dividend_df.empty:
                return 0.0, 0
            
            cutoff_date = datetime.now() - timedelta(days=365)
            recent = dividend_df[dividend_df['派息日'] >= cutoff_date]
            
            if recent.empty:
                return 0.0, 0
            
            recent = recent.sort_values('派息日', ascending=False)
            total = 0.0
            count = 0
            for _, row in recent.iterrows():
                desc = row.get('实施方案分红说明', '')
                div = parse_dividend_per_share(desc)
                if div > 0:
                    total += div
                    count += 1
            
            return total, count
    except Exception as e:
        logger.warning(f"计算TTM股息失败: {e}")
    return 0.0, 0


def calculate_lfy_dividend(dividend_df):
    """计算LFY股息率 - 上一个完整年度的股息总和"""
    if dividend_df is None or dividend_df.empty:
        return 0.0, 0
    
    try:
        if '派息日' in dividend_df.columns:
            dividend_df = dividend_df.dropna(subset=['派息日'])
            if dividend_df.empty:
                return 0.0, 0
            
            dividend_df = dividend_df.copy()
            dividend_df['派息日'] = pd.to_datetime(dividend_df['派息日'], errors='coerce')
            dividend_df = dividend_df.dropna(subset=['派息日'])
            
            if dividend_df.empty:
                return 0.0, 0
            
            current_year = datetime.now().year
            last_full_year = current_year - 1
            
            start_date = datetime(last_full_year, 1, 1)
            end_date = datetime(last_full_year, 12, 31)
            
            year_dividends = dividend_df[
                (dividend_df['派息日'] >= start_date) & 
                (dividend_df['派息日'] <= end_date)
            ]
            
            if year_dividends.empty:
                return 0.0, 0
            
            total = 0.0
            count = 0
            for _, row in year_dividends.iterrows():
                desc = row.get('实施方案分红说明', '')
                div = parse_dividend_per_share(desc)
                if div > 0:
                    total += div
                    count += 1
            
            return total, count
    except Exception as e:
        logger.warning(f"计算LFY股息失败: {e}")
    return 0.0, 0


def insert_into_top30(results_list, new_item, yield_field, max_count=30):
    """插入排序：将新数据插入TOP 30列表"""
    if len(results_list) < max_count:
        # 列表未满，直接插入并排序
        results_list.append(new_item)
        results_list.sort(key=lambda x: x[yield_field], reverse=True)
    else:
        # 列表已满，检查是否应该替换最小值
        min_yield = results_list[-1][yield_field]
        if new_item[yield_field] > min_yield:
            # 移除最小值，插入新值，重新排序
            results_list[-1] = new_item
            results_list.sort(key=lambda x: x[yield_field], reverse=True)
    return results_list


def process_single_stock(row_data):
    """处理单个股票的分红数据"""
    try:
        stock_code = str(row_data['代码']) if pd.notna(row_data['代码']) else ''
        price = float(row_data['最新价']) if pd.notna(row_data['最新价']) else 0
        market_cap = float(row_data['总市值']) if pd.notna(row_data['总市值']) else 0
        name = str(row_data['名称']) if pd.notna(row_data['名称']) else stock_code
        
        if not stock_code or price <= 0:
            return None
        
        try:
            dividend_df = ak.stock_dividend_cninfo(symbol=stock_code)
        except Exception as e:
            logger.debug(f"获取分红数据失败 {stock_code}: {e}")
            return None
        
        ttm_dividend, ttm_count = calculate_ttm_dividend(dividend_df)
        lfy_dividend, lfy_count = calculate_lfy_dividend(dividend_df)
        
        result = {
            'code': stock_code,
            'name': name,
            'price': price,
            'market_cap': market_cap / 1e8,
            'ttm_dividend': ttm_dividend,
            'ttm_yield': (ttm_dividend / price) * 100 if ttm_dividend > 0 and price > 0 else 0,
            'ttm_dividend_count': ttm_count,
            'lfy_dividend': lfy_dividend,
            'lfy_yield': (lfy_dividend / price) * 100 if lfy_dividend > 0 and price > 0 else 0,
            'lfy_dividend_count': lfy_count
        }
        return result
    except Exception as e:
        logger.debug(f"处理股票时出错: {e}")
        return None


def get_stock_data():
    """获取A股数据并计算股息率 - 并发处理"""
    global cached_data
    logger.info("开始获取A股数据...")
    
    logger.info("获取所有A股实时行情数据...")
    spot_df = ak.stock_zh_a_spot_em()
    if spot_df is None or spot_df.empty:
        logger.error("获取行情数据失败")
        return
    
    logger.info(f"获取到 {len(spot_df)} 只股票行情")
    
    large_cap_stocks = spot_df[
        (spot_df['总市值'] >= 1000 * 1e8) & 
        (spot_df['总市值'].notna())
    ].copy()
    
    # 按市值降序排序，优先处理大市值股票
    large_cap_stocks = large_cap_stocks.sort_values('总市值', ascending=False)
    
    logger.info(f"筛选出 {len(large_cap_stocks)} 只市值大于1000亿的股票")
    
    # 初始化结果列表
    results_ttm = []
    results_lfy = []
    processed = 0
    
    # 使用线程池并发处理
    stocks_list = [row for _, row in large_cap_stocks.iterrows()]
    
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = {executor.submit(process_single_stock, row): row for row in stocks_list}
        
        for future in as_completed(futures):
            result = future.result()
            if result is None:
                continue
            
            processed += 1
            
            # 处理TTM数据
            if result['ttm_dividend'] > 0:
                ttm_item = {
                    'code': result['code'],
                    'name': result['name'],
                    'price': result['price'],
                    'market_cap': result['market_cap'],
                    'ttm_dividend': result['ttm_dividend'],
                    'ttm_yield': result['ttm_yield'],
                    'ttm_dividend_count': result['ttm_dividend_count']
                }
                results_ttm = insert_into_top30(results_ttm, ttm_item, 'ttm_yield')
                
                # 实时更新缓存
                with data_lock:
                    cached_data['ttm'] = results_ttm.copy()
                    cached_data['update_time'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # 处理LFY数据
            if result['lfy_dividend'] > 0:
                lfy_item = {
                    'code': result['code'],
                    'name': result['name'],
                    'price': result['price'],
                    'market_cap': result['market_cap'],
                    'lfy_dividend': result['lfy_dividend'],
                    'lfy_yield': result['lfy_yield'],
                    'lfy_dividend_count': result['lfy_dividend_count']
                }
                results_lfy = insert_into_top30(results_lfy, lfy_item, 'lfy_yield')
                
                # 实时更新缓存
                with data_lock:
                    cached_data['lfy'] = results_lfy.copy()
                    cached_data['update_time'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            if processed % 20 == 0:
                logger.info(f"已处理 {processed} 只股票，TTM TOP30: {len(results_ttm)}, LFY TOP30: {len(results_lfy)}")
    
    logger.info(f"完成！TTM前30: {len(results_ttm)}, LFY前30: {len(results_lfy)}")


def update_data_in_background():
    """后台更新数据 - 实时更新缓存"""
    global cached_data
    
    with data_lock:
        cached_data['status'] = 'updating'
        cached_data['ttm'] = []
        cached_data['lfy'] = []
    
    try:
        get_stock_data()
        
        with data_lock:
            cached_data['status'] = 'ready'
            
        logger.info("后台数据更新完成")
        
    except Exception as e:
        logger.error(f"后台更新数据失败: {e}")
        with data_lock:
            cached_data['status'] = 'ready'


@app.get("/api/dividend")
async def get_dividend_data(background_tasks: BackgroundTasks):
    """获取股息率数据API"""
    global cached_data
    
    with data_lock:
        status = cached_data['status']
        ttm = cached_data['ttm'].copy()
        lfy = cached_data['lfy'].copy()
        update_time = cached_data['update_time']
    
    # 如果没有数据且状态为ready，启动后台更新
    if (not ttm or not lfy) and status == 'ready':
        background_tasks.add_task(update_data_in_background)
        return {
            "success": True,
            "status": "updating",
            "data": {
                "ttm": [],
                "lfy": []
            },
            "message": "数据正在加载中，请稍后刷新",
            "update_time": update_time
        }
    
    return {
        "success": True,
        "status": status,
        "data": {
            "ttm": ttm,
            "lfy": lfy
        },
        "update_time": update_time
    }


@app.get("/api/status")
async def get_status():
    """获取数据更新状态"""
    with data_lock:
        return {
            "status": cached_data['status'],
            "update_time": cached_data['update_time'],
            "ttm_count": len(cached_data['ttm']),
            "lfy_count": len(cached_data['lfy'])
        }


@app.get("/api/refresh")
async def refresh_data(background_tasks: BackgroundTasks):
    """手动刷新数据"""
    with data_lock:
        if cached_data['status'] == 'updating':
            return {
                "success": False,
                "message": "数据正在更新中，请稍后再试"
            }
    
    background_tasks.add_task(update_data_in_background)
    
    return {
        "success": True,
        "message": "数据刷新已启动，请稍后查看结果"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
