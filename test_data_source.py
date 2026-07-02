import requests
import logging
import time

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class StockDataSource:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })

    def get_eastmoney_spot(self):
        """从东方财富获取A股实时行情"""
        logger.info("尝试从东方财富获取行情数据...")
        url = 'https://push2.eastmoney.com/api/qt/clist/get'
        params = {
            'pn': '1',
            'pz': '200',
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
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if data.get('data', {}).get('diff'):
                stocks = []
                for item in data['data']['diff']:
                    stock = {
                        'code': item.get('f12', ''),
                        'name': item.get('f14', ''),
                        'price': float(item.get('f2', 0)),
                        'market_cap': float(item.get('f20', 0)) / 1e8 if item.get('f20') else 0
                    }
                    stocks.append(stock)
                logger.info(f"东方财富成功获取 {len(stocks)} 条数据")
                return stocks
            else:
                logger.warning("东方财富返回空数据")
                return None
        except Exception as e:
            logger.error(f"东方财富获取失败: {e}")
            return None

    def get_tencent_gtimg(self, stock_codes):
        """从腾讯GTimg获取股票数据"""
        logger.info(f"尝试从腾讯GTimg获取 {len(stock_codes)} 只股票数据...")
        
        all_stocks = []
        batch_size = 50
        for i in range(0, len(stock_codes), batch_size):
            batch = stock_codes[i:i+batch_size]
            codes_str = ','.join([f"sh{code}" if code.startswith('6') else f"sz{code}" for code in batch])
            
            url = f'https://qt.gtimg.cn/q={codes_str}'
            
            try:
                response = self.session.get(url, timeout=10)
                response.raise_for_status()
                
                lines = response.text.strip().split(';\n')
                for line in lines:
                    if '=' in line:
                        _, data_str = line.split('=', 1)
                        data = data_str.strip().strip('"').split('~')
                        if len(data) > 44:
                            stock = {
                                'code': data[2],
                                'name': data[1],
                                'price': float(data[3]) if data[3] else 0,
                                'market_cap': float(data[44]) if data[44] else 0
                            }
                            all_stocks.append(stock)
                
                time.sleep(0.5)
            except Exception as e:
                logger.error(f"腾讯GTimg批量获取失败: {e}")
        
        logger.info(f"腾讯GTimg成功获取 {len(all_stocks)} 条数据")
        return all_stocks if all_stocks else None

    def get_stock_data(self, simulate_eastmoney_fail=False):
        """获取股票数据，支持数据源切换"""
        import time
        start_time = time.time()
        logger.info("=" * 60)
        logger.info(f"[数据获取] 开始获取股票数据")
        logger.info(f"[数据获取] 模拟东方财富失败: {simulate_eastmoney_fail}")
        
        # 策略1: 东方财富
        logger.info(f"[数据源1] 尝试东方财富API...")
        if not simulate_eastmoney_fail:
            data = self.get_eastmoney_spot()
            if data:
                elapsed = time.time() - start_time
                logger.info(f"[数据源1] ✅ 东方财富成功，耗时 {elapsed:.2f}s")
                logger.info(f"[数据源1] 📊 返回 {len(data)} 条数据")
                logger.info(f"[数据获取] ✅ 数据获取成功，使用数据源: 东方财富")
                logger.info("=" * 60)
                return data
            else:
                logger.warning(f"[数据源1] ❌ 东方财富返回空数据，准备切换...")
        else:
            logger.warning(f"[数据源1] ⏭️ 已跳过东方财富（模拟失败模式）")
        
        # 策略2: 腾讯GTimg（需要先有代码列表）
        logger.info(f"[数据源2] 尝试腾讯GTimg API...")
        logger.info(f"[数据源2] 📋 股票代码列表长度: 10")
        test_codes = ['601398', '600036', '601318', '600000', '000001', '000858', '002594', '601899', '600519', '601988']
        data = self.get_tencent_gtimg(test_codes)
        if data:
            elapsed = time.time() - start_time
            logger.info(f"[数据源2] ✅ 腾讯GTimg成功，耗时 {elapsed:.2f}s")
            logger.info(f"[数据源2] 📊 返回 {len(data)} 条数据")
            logger.info(f"[数据获取] ✅ 数据获取成功，使用数据源: 腾讯GTimg")
            logger.info(f"[数据获取] 🔄 已从东方财富切换到腾讯GTimg")
            logger.info("=" * 60)
            return data
        else:
            logger.error(f"[数据源2] ❌ 腾讯GTimg获取失败")
        
        # 所有数据源都失败
        elapsed = time.time() - start_time
        logger.error(f"[数据获取] ❌ 所有数据源获取失败，耗时 {elapsed:.2f}s")
        logger.error(f"[数据获取] 📋 已尝试数据源: 东方财富, 腾讯GTimg")
        logger.info("=" * 60)
        return None


def test_switch_logic():
    """测试数据源切换逻辑"""
    source = StockDataSource()
    
    print("\n" + "="*60)
    print("测试1: 正常情况（东方财富可用）")
    print("="*60)
    data = source.get_stock_data(simulate_eastmoney_fail=False)
    if data:
        print(f"成功获取 {len(data)} 条数据")
        for stock in data[:5]:
            print(f"  {stock['code']} {stock['name']}: ¥{stock['price']} 市值:{stock['market_cap']:.2f}亿")
    else:
        print("获取失败")
    
    print("\n" + "="*60)
    print("测试2: 模拟东方财富失败，切换到腾讯GTimg")
    print("="*60)
    data = source.get_stock_data(simulate_eastmoney_fail=True)
    if data:
        print(f"成功切换到腾讯GTimg，获取 {len(data)} 条数据")
        for stock in data:
            print(f"  {stock['code']} {stock['name']}: ¥{stock['price']} 市值:{stock['market_cap']:.2f}亿")
    else:
        print("切换失败，所有数据源都不可用")


if __name__ == '__main__':
    test_switch_logic()