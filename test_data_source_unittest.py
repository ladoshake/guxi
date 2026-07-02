import unittest
from unittest.mock import Mock, patch, MagicMock
import requests
from test_data_source import StockDataSource


class TestStockDataSource(unittest.TestCase):
    
    def setUp(self):
        """测试前初始化"""
        self.source = StockDataSource()
    
    def test_eastmoney_response_format(self):
        """测试东方财富API响应格式"""
        mock_response = Mock()
        mock_response.raise_for_status = Mock()
        mock_response.json.return_value = {
            'data': {
                'diff': [
                    {
                        'f12': '601398',
                        'f14': '工商银行',
                        'f2': 7.05,
                        'f20': 1900766000000
                    }
                ]
            }
        }
        
        with patch.object(self.source.session, 'get', return_value=mock_response):
            data = self.source.get_eastmoney_spot()
            
            self.assertIsNotNone(data)
            self.assertEqual(len(data), 1)
            self.assertEqual(data[0]['code'], '601398')
            self.assertEqual(data[0]['name'], '工商银行')
            self.assertEqual(data[0]['price'], 7.05)
            self.assertAlmostEqual(data[0]['market_cap'], 19007.66, places=2)
    
    def test_eastmoney_empty_response(self):
        """测试东方财富返回空数据"""
        mock_response = Mock()
        mock_response.raise_for_status = Mock()
        mock_response.json.return_value = {'data': {'diff': None}}
        
        with patch.object(self.source.session, 'get', return_value=mock_response):
            data = self.source.get_eastmoney_spot()
            self.assertIsNone(data)
    
    def test_eastmoney_network_error(self):
        """测试东方财富网络错误"""
        with patch.object(self.source.session, 'get', side_effect=requests.exceptions.ConnectionError):
            data = self.source.get_eastmoney_spot()
            self.assertIsNone(data)
    
    def test_tencent_gtimg_response_format(self):
        """测试腾讯GTimg响应格式"""
        mock_response = Mock()
        mock_response.raise_for_status = Mock()
        mock_response.text = 'v_sh601398="1~工商银行~601398~7.05~7.06~7.03~3584757~1709032~1875725~7.04~18101~7.03~50980~7.02~48537~7.01~79625~7.00~294119~7.05~2696~7.06~19823~7.07~15647~7.08~17107~7.09~11739~~20260702161421~-0.01~-0.14~7.14~7.00~7.05/3584757/2528095306~3584757~252810~0.13~6.77~~7.14~7.00~1.98~19007.66~25126.64~0.65~7.77~6.35~0.92~424350~7.05~7.23~6.82~~~-0.08~252809.5306~0.0000~0~ ~GP-A~-9.16~-1.95~4.40~8.58~0.67~8.09~6.68~-4.21~-3.16~-5.51~269612212539~356406257089~76.00~-0.70~269612212539~~~-2.15~0.28~~CNY~0~___D__F__N~6.98~70861~";'
        
        with patch.object(self.source.session, 'get', return_value=mock_response):
            data = self.source.get_tencent_gtimg(['601398'])
            
            self.assertIsNotNone(data)
            self.assertEqual(len(data), 1)
            self.assertEqual(data[0]['code'], '601398')
            self.assertEqual(data[0]['name'], '工商银行')
            self.assertEqual(data[0]['price'], 7.05)
            self.assertAlmostEqual(data[0]['market_cap'], 19007.66, places=2)
    
    def test_tencent_gtimg_batch_response(self):
        """测试腾讯GTimg批量查询"""
        mock_response = Mock()
        mock_response.raise_for_status = Mock()
        mock_response.text = '''v_sh601398="1~工商银行~601398~7.05~7.06~7.03~3584757~1709032~1875725~7.04~18101~7.03~50980~7.02~48537~7.01~79625~7.00~294119~7.05~2696~7.06~19823~7.07~15647~7.08~17107~7.09~11739~~20260702161421~-0.01~-0.14~7.14~7.00~7.05/3584757/2528095306~3584757~252810~0.13~6.77~~7.14~7.00~1.98~19007.66~25126.64~0.65~7.77~6.35~0.92~424350~7.05~7.23~6.82~~~-0.08~252809.5306~0.0000~0~ ~GP-A~-9.16~-1.95~4.40~8.58~0.67~8.09~6.68~-4.21~-3.16~-5.51~269612212539~356406257089~76.00~-0.70~269612212539~~~-2.15~0.28~~CNY~0~___D__F__N~6.98~70861~";
v_sh600036="1~招商银行~600036~36.60~35.91~36.28~944614~509573~435042~36.59~250~36.58~31~36.57~599~36.56~192~36.55~194~36.60~5209~36.61~653~36.62~313~36.63~534~36.64~288~~20260702161412~0.69~1.92~36.80~36.13~36.60/944614/3442082753~944614~344208~0.46~6.12~~36.80~36.13~1.87~7550.19~9230.46~0.82~39.50~32.32~0.89~-5731~36.44~6.10~6.15~~~0.21~344208.2753~0.0000~0~ ~GP-A~-10.92~1.02~8.23~11.76~1.12~45.54~35.28~-4.26~-4.94~-7.95~20628944429~25219845601~-69.36~-8.01~20628944429~~~-1.92~0.38~~CNY~0~___D__F__N~35.91~944614~";'''
        
        with patch.object(self.source.session, 'get', return_value=mock_response):
            data = self.source.get_tencent_gtimg(['601398', '600036'])
            
            self.assertIsNotNone(data)
            self.assertEqual(len(data), 2)
            self.assertEqual(data[0]['code'], '601398')
            self.assertEqual(data[1]['code'], '600036')
    
    def test_tencent_gtimg_network_error(self):
        """测试腾讯GTimg网络错误"""
        with patch.object(self.source.session, 'get', side_effect=requests.exceptions.ConnectionError):
            data = self.source.get_tencent_gtimg(['601398'])
            self.assertIsNone(data)
    
    def test_tencent_gtimg_empty_response(self):
        """测试腾讯GTimg返回空数据"""
        mock_response = Mock()
        mock_response.raise_for_status = Mock()
        mock_response.text = ''
        
        with patch.object(self.source.session, 'get', return_value=mock_response):
            data = self.source.get_tencent_gtimg(['601398'])
            self.assertIsNone(data)
    
    def test_data_source_switch_eastmoney_success(self):
        """测试数据源切换：东方财富成功"""
        mock_eastmoney = Mock()
        mock_eastmoney.raise_for_status = Mock()
        mock_eastmoney.json.return_value = {
            'data': {
                'diff': [{'f12': '601398', 'f14': '工商银行', 'f2': 7.05, 'f20': 190076600000}]
            }
        }
        
        with patch.object(self.source.session, 'get', return_value=mock_eastmoney):
            data = self.source.get_stock_data(simulate_eastmoney_fail=False)
            
            self.assertIsNotNone(data)
            self.assertEqual(len(data), 1)
            self.assertEqual(data[0]['code'], '601398')
    
    def test_data_source_switch_to_tencent(self):
        """测试数据源切换：东方财富失败，切换到腾讯"""
        mock_eastmoney = Mock()
        mock_eastmoney.raise_for_status.side_effect = requests.exceptions.ConnectionError
        
        mock_tencent = Mock()
        mock_tencent.raise_for_status = Mock()
        mock_tencent.text = 'v_sh601398="1~工商银行~601398~7.05~7.06~7.03~3584757~1709032~1875725~7.04~18101~7.03~50980~7.02~48537~7.01~79625~7.00~294119~7.05~2696~7.06~19823~7.07~15647~7.08~17107~7.09~11739~~20260702161421~-0.01~-0.14~7.14~7.00~7.05/3584757/2528095306~3584757~252810~0.13~6.77~~7.14~7.00~1.98~19007.66~25126.64~0.65~7.77~6.35~0.92~424350~7.05~7.23~6.82~~~-0.08~252809.5306~0.0000~0~ ~GP-A~-9.16~-1.95~4.40~8.58~0.67~8.09~6.68~-4.21~-3.16~-5.51~269612212539~356406257089~76.00~-0.70~269612212539~~~-2.15~0.28~~CNY~0~___D__F__N~6.98~70861~";'
        
        call_count = [0]
        
        def mock_get(*args, **kwargs):
            call_count[0] += 1
            if call_count[0] == 1:
                return mock_eastmoney
            else:
                return mock_tencent
        
        with patch.object(self.source.session, 'get', side_effect=mock_get):
            data = self.source.get_stock_data(simulate_eastmoney_fail=False)
            
            self.assertIsNotNone(data)
            self.assertEqual(len(data), 1)
            self.assertEqual(data[0]['code'], '601398')
    
    def test_data_source_all_fail(self):
        """测试数据源切换：所有数据源都失败"""
        with patch.object(self.source.session, 'get', side_effect=requests.exceptions.ConnectionError):
            data = self.source.get_stock_data(simulate_eastmoney_fail=False)
            self.assertIsNone(data)
    
    def test_stock_data_format(self):
        """测试返回数据格式正确性"""
        mock_response = Mock()
        mock_response.raise_for_status = Mock()
        mock_response.text = 'v_sh601398="1~工商银行~601398~7.05~7.06~7.03~3584757~1709032~1875725~7.04~18101~7.03~50980~7.02~48537~7.01~79625~7.00~294119~7.05~2696~7.06~19823~7.07~15647~7.08~17107~7.09~11739~~20260702161421~-0.01~-0.14~7.14~7.00~7.05/3584757/2528095306~3584757~252810~0.13~6.77~~7.14~7.00~1.98~19007.66~25126.64~0.65~7.77~6.35~0.92~424350~7.05~7.23~6.82~~~-0.08~252809.5306~0.0000~0~ ~GP-A~-9.16~-1.95~4.40~8.58~0.67~8.09~6.68~-4.21~-3.16~-5.51~269612212539~356406257089~76.00~-0.70~269612212539~~~-2.15~0.28~~CNY~0~___D__F__N~6.98~70861~";'
        
        with patch.object(self.source.session, 'get', return_value=mock_response):
            data = self.source.get_tencent_gtimg(['601398'])
            
            for stock in data:
                self.assertIn('code', stock)
                self.assertIn('name', stock)
                self.assertIn('price', stock)
                self.assertIn('market_cap', stock)
                self.assertIsInstance(stock['code'], str)
                self.assertIsInstance(stock['name'], str)
                self.assertIsInstance(stock['price'], float)
                self.assertIsInstance(stock['market_cap'], float)
    
    def test_market_cap_filter(self):
        """测试市值筛选逻辑"""
        test_data = [
            {'code': '601398', 'name': '工商银行', 'price': 7.05, 'market_cap': 19007.66},
            {'code': '600036', 'name': '招商银行', 'price': 36.6, 'market_cap': 7550.19},
            {'code': '000001', 'name': '平安银行', 'price': 10.28, 'market_cap': 1994.90},
            {'code': '000002', 'name': '万科A', 'price': 15.5, 'market_cap': 999.99}
        ]
        
        filtered = [s for s in test_data if s['market_cap'] > 1000]
        
        self.assertEqual(len(filtered), 3)
        self.assertNotIn('000002', [s['code'] for s in filtered])


if __name__ == '__main__':
    unittest.main(verbosity=2)