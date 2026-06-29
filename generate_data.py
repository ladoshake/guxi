import akshare as ak
import pandas as pd
import re
from datetime import datetime, timedelta
import json
import logging
import os
import time
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 配置akshare的请求参数，增加重试和超时
def setup_akshare_retry():
    """配置akshare的请求重试机制"""
    session = requests.Session()
    retry_strategy = Retry(
        total=5,  # 最大重试次数
        backoff_factor=2,  # 重试间隔因子
        status_forcelist=[429, 500, 502, 503, 504],  # 需要重试的HTTP状态码
        allowed_methods=["GET", "POST"]
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    
    # 设置请求头，模拟浏览器访问
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        'Accept-Encoding': 'gzip, deflate',
        'Connection': 'keep-alive',
        'Referer': 'http://quote.eastmoney.com/',
    })
    
    # 将配置的session应用到akshare
    try:
        import akshare.stock_feature.stock_hist_em as hist_em
        hist_em.requests_session = session
    except:
        logger.warning("无法配置akshare的session，使用默认配置")


def parse_dividend_per_share(description):
    if pd.isna(description) or not isinstance(description, str):
        return 0.0

    match = re.search(r'10派([\d.]+)元', description)
    if match:
        try:
            return float(match.group(1)) / 10
        except:
            pass

    return 0.0


def calculate_ttm_dividend(dividend_df):
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


def get_stock_data_with_retry(max_retries=3, delay=10):
    """带重试机制的获取A股行情数据"""
    for attempt in range(max_retries):
        try:
            logger.info(f"尝试获取A股行情数据 (第 {attempt + 1}/{max_retries} 次)...")
            spot_df = ak.stock_zh_a_spot_em()
            if spot_df is not None and not spot_df.empty:
                return spot_df
        except Exception as e:
            logger.warning(f"获取行情数据失败 (第 {attempt + 1} 次): {e}")
            if attempt < max_retries - 1:
                logger.info(f"等待 {delay} 秒后重试...")
                time.sleep(delay)
    
    return None


def get_stock_data():
    # 首先配置重试机制
    setup_akshare_retry()
    
    logger.info("开始获取A股数据...")

    logger.info("获取所有A股实时行情数据...")
    spot_df = get_stock_data_with_retry(max_retries=5, delay=15)
    if spot_df is None or spot_df.empty:
        logger.error("获取行情数据失败，多次重试后仍无法获取")
        return None

    logger.info(f"获取到 {len(spot_df)} 只股票行情")

    large_cap_stocks = spot_df[
        (spot_df['总市值'] >= 1000 * 1e8) &
        (spot_df['总市值'].notna())
    ].copy()

    large_cap_stocks = large_cap_stocks.sort_values('总市值', ascending=False)

    logger.info(f"筛选出 {len(large_cap_stocks)} 只市值大于1000亿的股票")

    results_ttm = []
    results_lfy = []
    processed = 0

    for _, row in large_cap_stocks.iterrows():
        try:
            stock_code = str(row['代码']) if pd.notna(row['代码']) else ''
            price = float(row['最新价']) if pd.notna(row['最新价']) else 0
            market_cap = float(row['总市值']) if pd.notna(row['总市值']) else 0
            name = str(row['名称']) if pd.notna(row['名称']) else stock_code

            if not stock_code or price <= 0:
                continue

            # 对每个股票的分红数据获取也增加重试
            dividend_df = None
            for retry in range(3):
                try:
                    dividend_df = ak.stock_dividend_cninfo(symbol=stock_code)
                    break
                except Exception as e:
                    if retry < 2:
                        time.sleep(2)
                    else:
                        logger.debug(f"获取分红数据失败 {stock_code}: {e}")

            if dividend_df is None:
                continue

            ttm_dividend, ttm_count = calculate_ttm_dividend(dividend_df)
            lfy_dividend, lfy_count = calculate_lfy_dividend(dividend_df)

            if ttm_dividend > 0:
                ttm_item = {
                    'code': stock_code,
                    'name': name,
                    'price': price,
                    'market_cap': market_cap / 1e8,
                    'ttm_dividend': ttm_dividend,
                    'ttm_yield': (ttm_dividend / price) * 100 if price > 0 else 0,
                    'ttm_dividend_count': ttm_count
                }
                results_ttm.append(ttm_item)
                results_ttm.sort(key=lambda x: x['ttm_yield'], reverse=True)
                results_ttm = results_ttm[:30]

            if lfy_dividend > 0:
                lfy_item = {
                    'code': stock_code,
                    'name': name,
                    'price': price,
                    'market_cap': market_cap / 1e8,
                    'lfy_dividend': lfy_dividend,
                    'lfy_yield': (lfy_dividend / price) * 100 if price > 0 else 0,
                    'lfy_dividend_count': lfy_count
                }
                results_lfy.append(lfy_item)
                results_lfy.sort(key=lambda x: x['lfy_yield'], reverse=True)
                results_lfy = results_lfy[:30]

            processed += 1
            if processed % 20 == 0:
                logger.info(f"已处理 {processed} 只股票")

        except Exception as e:
            logger.debug(f"处理股票时出错: {e}")
            continue

    return {
        'ttm': results_ttm,
        'lfy': results_lfy,
        'update_time': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }


if __name__ == "__main__":
    data = get_stock_data()
    if data:
        output_path = os.path.join(os.path.dirname(__file__), "data.json")
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        logger.info(f"数据已保存到 {output_path}")
        logger.info(f"TTM前30: {len(data['ttm'])}, LFY前30: {len(data['lfy'])}")
    else:
        logger.error("数据生成失败")