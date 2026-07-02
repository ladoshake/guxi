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


def get_beijing_time():
    """获取当前北京时间"""
    os.environ['TZ'] = 'Asia/Shanghai'
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_session():
    """创建配置好的requests session"""
    session = requests.Session()
    retry_strategy = Retry(
        total=5,
        backoff_factor=2,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET", "POST"]
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        'Accept-Encoding': 'gzip, deflate',
        'Connection': 'keep-alive',
        'Referer': 'http://quote.eastmoney.com/',
    })
    
    return session


SESSION = create_session()


def fetch_eastmoney_direct():
    """从东方财富直接API获取A股实时行情"""
    logger.info("  [东方财富直接API] 开始获取数据...")
    url = 'https://push2.eastmoney.com/api/qt/clist/get'
    params = {
        'pn': '1',
        'pz': '5000',
        'po': '1',
        'np': '1',
        'ut': 'bd1d9ddb04089700cf9c27f6f7426281',
        'fltt': '2',
        'invt': '2',
        'fid': 'f3',
        'fs': 'm:0+t:6,m:0+t:13,m:0+t:80,m:1+t:2,m:1+t:23',
        'fields': 'f1,f2,f3,f4,f5,f6,f7,f8,f9,f10,f12,f13,f14,f15,f16,f17,f18,f20,f21,f23,f24,f25,f22,f11,f62,f128,f136,f115,f152'
    }
    
    try:
        response = SESSION.get(url, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        if data.get('data', {}).get('diff'):
            stocks = []
            for item in data['data']['diff']:
                stock = {
                    '代码': item.get('f12', ''),
                    '名称': item.get('f14', ''),
                    '最新价': float(item.get('f2', 0)),
                    '总市值': float(item.get('f20', 0))
                }
                stocks.append(stock)
            
            df = pd.DataFrame(stocks)
            logger.info(f"  [东方财富直接API] 成功获取 {len(df)} 条数据")
            return df
        else:
            logger.warning("  [东方财富直接API] 返回空数据")
            return None
    except Exception as e:
        logger.warning(f"  [东方财富直接API] 失败: {str(e)[:100]}")
        return None


def fetch_tencent_gtimg():
    """从腾讯GTimg获取A股实时行情（需要先获取代码列表）"""
    logger.info("  [腾讯GTimg] 开始获取数据...")
    
    code_list = []
    
    # 方法1: 从东方财富直接API获取代码列表
    try:
        logger.info("  [腾讯GTimg] 尝试从东方财富直接API获取代码列表...")
        url = 'https://push2.eastmoney.com/api/qt/clist/get'
        params = {
            'pn': '1',
            'pz': '5000',
            'po': '1',
            'np': '1',
            'ut': 'bd1d9ddb04089700cf9c27f6f7426281',
            'fltt': '2',
            'invt': '2',
            'fid': 'f3',
            'fs': 'm:0+t:6,m:0+t:13,m:0+t:80,m:1+t:2,m:1+t:23',
            'fields': 'f12,f14'
        }
        response = SESSION.get(url, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        if data.get('data', {}).get('diff'):
            code_list = [item.get('f12', '') for item in data['data']['diff'] if item.get('f12')]
            logger.info(f"  [腾讯GTimg] 从东方财富直接API获取到 {len(code_list)} 个股票代码")
    except Exception as e:
        logger.warning(f"  [腾讯GTimg] 从东方财富直接API获取代码列表失败: {str(e)[:50]}")
    
    # 方法2: 如果方法1失败，尝试从akshare获取
    if not code_list:
        try:
            logger.info("  [腾讯GTimg] 尝试从akshare获取代码列表...")
            df = ak.stock_zh_a_spot_em()
            if df is not None and not df.empty:
                if '代码' in df.columns:
                    code_list = df['代码'].astype(str).tolist()
                elif '股票代码' in df.columns:
                    code_list = df['股票代码'].astype(str).tolist()
                logger.info(f"  [腾讯GTimg] 从akshare获取到 {len(code_list)} 个股票代码")
        except Exception as e:
            logger.warning(f"  [腾讯GTimg] 从akshare获取代码列表失败: {str(e)[:50]}")
    
    if not code_list:
        logger.warning("  [腾讯GTimg] 无法获取股票代码列表")
        return None
    
    all_stocks = []
    batch_size = 50
    
    for i in range(0, len(code_list), batch_size):
        batch = code_list[i:i+batch_size]
        codes_str = ','.join([f"sh{code}" if code.startswith('6') else f"sz{code}" for code in batch])
        
        url = f'https://qt.gtimg.cn/q={codes_str}'
        
        try:
            response = SESSION.get(url, timeout=10)
            response.raise_for_status()
            
            lines = response.text.strip().split(';\n')
            for line in lines:
                if '=' in line:
                    _, data_str = line.split('=', 1)
                    data = data_str.strip().strip('"').split('~')
                    if len(data) > 44:
                        stock = {
                            '代码': data[2],
                            '名称': data[1],
                            '最新价': float(data[3]) if data[3] else 0,
                            '总市值': float(data[44]) * 1e8 if data[44] else 0
                        }
                        all_stocks.append(stock)
            
            time.sleep(0.3)
        except Exception as e:
            logger.warning(f"  [腾讯GTimg] 批量获取失败: {str(e)[:50]}")
    
    if all_stocks:
        df = pd.DataFrame(all_stocks)
        logger.info(f"  [腾讯GTimg] 成功获取 {len(df)} 条数据")
        return df
    else:
        logger.warning("  [腾讯GTimg] 返回空数据")
        return None


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


def get_stock_data_with_retry(max_retries=3, delay=20):
    """带重试机制的获取A股行情数据，使用多个数据源"""
    logger.info("=" * 60)
    logger.info("[数据获取] 开始获取股票行情数据")
    start_time = time.time()
    
    data_sources = [
        ('东方财富直接API', fetch_eastmoney_direct),
        ('腾讯GTimg', fetch_tencent_gtimg),
        ('akshare东方财富', lambda: ak.stock_zh_a_spot_em()),
        ('akshare上海+深圳A股', lambda: pd.concat([ak.stock_sh_a_spot_em(), ak.stock_sz_a_spot_em()], ignore_index=True)),
    ]
    
    for source_idx, (source_name, fetch_func) in enumerate(data_sources, 1):
        logger.info(f"[数据源{source_idx}] 尝试 {source_name}...")
        
        for attempt in range(max_retries):
            try:
                logger.info(f"  第 {attempt + 1}/{max_retries} 次尝试...")
                
                spot_df = fetch_func()
                if spot_df is not None and not spot_df.empty:
                    elapsed = time.time() - start_time
                    logger.info(f"[数据源{source_idx}] ✅ {source_name}成功，耗时 {elapsed:.2f}s")
                    logger.info(f"[数据源{source_idx}] 📊 返回 {len(spot_df)} 条数据")
                    logger.info(f"[数据获取] ✅ 数据获取成功，使用数据源: {source_name}")
                    logger.info("=" * 60)
                    return spot_df
                    
            except Exception as e:
                logger.warning(f"  失败: {str(e)[:100]}")
                if attempt < max_retries - 1:
                    wait_time = delay + attempt * 5
                    logger.info(f"  等待 {wait_time} 秒后重试...")
                    time.sleep(wait_time)
        
        logger.warning(f"[数据源{source_idx}] ❌ {source_name}数据源失败，切换到下一个数据源")
        time.sleep(5)
    
    elapsed = time.time() - start_time
    logger.error(f"[数据获取] ❌ 所有数据源获取失败，耗时 {elapsed:.2f}s")
    logger.error(f"[数据获取] 📋 已尝试数据源: {', '.join([s[0] for s in data_sources])}")
    logger.info("=" * 60)
    return None


def normalize_columns(df):
    """统一不同数据源的列名"""
    if df is None:
        return None
    
    column_mapping = {
        '股票代码': '代码',
        '股票名称': '名称',
        '最新价': '最新价',
        '总市值': '总市值',
        '市值': '总市值',
    }
    
    df = df.rename(columns=lambda x: column_mapping.get(x, x))
    
    required_columns = ['代码', '名称', '最新价']
    missing_cols = [col for col in required_columns if col not in df.columns]
    
    if missing_cols:
        logger.error(f"缺少必要列: {missing_cols}，当前列名: {list(df.columns)}")
        return None
    
    return df


def load_backup_data():
    """加载备份数据"""
    backup_file = 'data.json'
    if os.path.exists(backup_file):
        try:
            logger.info("尝试加载备份数据...")
            with open(backup_file, 'r', encoding='utf-8') as f:
                backup_data = json.load(f)
                if backup_data and 'ttm' in backup_data and 'lfy' in backup_data:
                    logger.info(f"成功加载备份数据，包含 {len(backup_data['ttm'])} 条TTM数据")
                    return backup_data
        except Exception as e:
            logger.warning(f"加载备份数据失败: {e}")
    return None


def get_stock_data():
    logger.info("开始获取A股数据...")

    logger.info("获取所有A股实时行情数据...")
    spot_df = get_stock_data_with_retry(max_retries=3, delay=20)
    
    if spot_df is None or spot_df.empty:
        logger.error("所有数据源获取行情数据失败")
        logger.info("尝试使用备份数据...")
        backup_data = load_backup_data()
        if backup_data:
            logger.info("使用备份数据更新时间戳后返回")
            backup_data['update_time'] = get_beijing_time()
            backup_data['is_backup'] = True
            return backup_data
        else:
            logger.error("无备份数据可用，数据生成失败")
            return None

    spot_df = normalize_columns(spot_df)
    if spot_df is None:
        logger.error("数据列名不匹配")
        return None

    logger.info(f"获取到 {len(spot_df)} 只股票行情")

    if '总市值' in spot_df.columns and not spot_df['总市值'].isna().all():
        large_cap_stocks = spot_df[
            (spot_df['总市值'] >= 1000 * 1e8) &
            (spot_df['总市值'].notna())
        ].copy()
        large_cap_stocks = large_cap_stocks.sort_values('总市值', ascending=False)
        logger.info(f"筛选出 {len(large_cap_stocks)} 只市值大于1000亿的股票")
    else:
        logger.warning("缺少市值数据，处理前200只股票")
        large_cap_stocks = spot_df.head(200).copy()

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
        'update_time': get_beijing_time(),
        'is_backup': False
    }


if __name__ == "__main__":
    success = False
    try:
        data = get_stock_data()
        if data:
            output_path = os.path.join(os.path.dirname(__file__), "data.json")
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            logger.info(f"数据已保存到 {output_path}")
            logger.info(f"TTM前30: {len(data['ttm'])}, LFY前30: {len(data['lfy'])}")
            success = True
        else:
            logger.error("数据生成失败")
    except Exception as e:
        logger.error(f"脚本执行异常: {e}")
        logger.info("尝试使用备份数据...")
        backup_data = load_backup_data()
        if backup_data:
            output_path = os.path.join(os.path.dirname(__file__), "data.json")
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(backup_data, f, ensure_ascii=False, indent=2)
            logger.info(f"已使用备份数据")
            success = True
        else:
            logger.error("无备份数据可用")
    finally:
        logger.info(f"脚本执行完成 (成功: {success})")