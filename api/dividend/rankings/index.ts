interface StockItem {
  rank: number;
  code: string;
  name: string;
  market_cap: number;
  latest_price: number;
  ttm_dividends: number;
  lfy_dividends: number;
  ttm_yield: number;
  lfy_yield: number;
}

interface RankingsResponse {
  success: boolean;
  ttm_ranking: StockItem[];
  lfy_ranking: StockItem[];
  total_count: number;
  data_time: string;
  message?: string;
}

const MARKET_CAP_THRESHOLD = 1e11;

async function fetchStockData(): Promise<any[]> {
  console.log('[API] 获取股票数据...');
  const res = await fetch(
    'https://push2.eastmoney.com/api/qt/clist/get?pn=1&pz=100&po=1&np=1&ut=bd1d9ddb04089700cf9c27f6f7426281&fltt=2&invt=2&fid=f8&fs=m:0+t:6,m:0+t:13,m:0+t:80,m:1+t:2,m:1+t:23&fields=f2,f3,f4,f5,f6,f7,f8,f9,f12,f14,f20,f21',
    { signal: AbortSignal.timeout(10000) }
  );
  const data = await res.json();
  const stocks = data.data?.diff || [];
  console.log(`[API] 获取到 ${stocks.length} 只股票`);
  return stocks;
}

export default async function handler(): Promise<Response> {
  console.log('[API] 函数开始执行');
  const startTime = Date.now();
  
  try {
    const stocks = await fetchStockData();
    
    if (!stocks.length) {
      return Response.json({
        success: false,
        message: '无法获取A股数据，请稍后重试',
        ttm_ranking: [],
        lfy_ranking: [],
        total_count: 0
      });
    }

    const largeStocks = stocks.filter(s => {
      const marketCap = parseFloat(s.f20) || 0;
      const dividendYield = parseFloat(s.f8) || 0;
      return marketCap > MARKET_CAP_THRESHOLD && dividendYield > 0;
    }).slice(0, 30);
    
    console.log(`[API] 筛选出 ${largeStocks.length} 只大盘股（市值>1000亿，股息率>0）`);

    const results: StockItem[] = [];
    
    for (const stock of largeStocks) {
      const code = stock.f12;
      const name = stock.f14;
      const marketCap = parseFloat(stock.f20) || 0;
      const latestPrice = parseFloat(stock.f2) || 0;
      const dividendYield = parseFloat(stock.f8) || 0;

      if (!code || !name || marketCap <= 0 || latestPrice <= 0 || dividendYield <= 0) continue;

      const ttmDividends = (dividendYield / 100) * latestPrice;

      results.push({
        rank: 0,
        code,
        name,
        market_cap: Math.round(marketCap / 1e8),
        latest_price: Math.round(latestPrice * 100) / 100,
        ttm_dividends: Math.round(ttmDividends * 10000) / 10000,
        lfy_dividends: 0,
        ttm_yield: Math.round(dividendYield * 100) / 100,
        lfy_yield: 0
      });
    }

    const ttmRanking = results
      .sort((a, b) => b.ttm_yield - a.ttm_yield)
      .slice(0, 30)
      .map((item, i) => ({ ...item, rank: i + 1 }));

    const lfyRanking = results
      .sort((a, b) => b.ttm_yield - a.ttm_yield)
      .slice(0, 30)
      .map((item, i) => ({ ...item, rank: i + 1 }));

    const elapsed = Date.now() - startTime;
    console.log(`[API] 执行完成，耗时 ${elapsed}ms`);
    console.log(`[API] TTM排名: ${ttmRanking.length} 只, LFY排名: ${lfyRanking.length} 只`);

    return Response.json({
      success: true,
      ttm_ranking: ttmRanking,
      lfy_ranking: lfyRanking,
      total_count: largeStocks.length,
      data_time: new Date().toLocaleString('zh-CN')
    });
  } catch (error) {
    console.error('[API] 执行失败:', error);
    return Response.json({
      success: false,
      message: `数据获取失败: ${error instanceof Error ? error.message : '未知错误'}`,
      ttm_ranking: [],
      lfy_ranking: [],
      total_count: 0
    });
  }
}
