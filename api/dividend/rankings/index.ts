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
const MAX_STOCKS = 15;
const BATCH_SIZE = 15;

async function fetchStockList(): Promise<any[]> {
  console.log('[API] 获取股票列表...');
  const res = await fetch(
    'https://push2.eastmoney.com/api/qt/clist/get?pn=1&pz=100&po=1&np=1&ut=bd1d9ddb04089700cf9c27f6f7426281&fltt=2&invt=2&fid=f3&fs=m:0+t:6,m:0+t:13,m:0+t:80,m:1+t:2,m:1+t:23&fields=f2,f12,f14,f20',
    { signal: AbortSignal.timeout(15000) }
  );
  const data = await res.json();
  console.log(`[API] 获取到 ${data.data?.diff?.length || 0} 只股票`);
  return data.data?.diff || [];
}

async function fetchDividendDataBatch(codes: string[]): Promise<Map<string, any[]>> {
  console.log(`[API] 批量获取分红数据: ${codes.length} 只股票`);
  const results = new Map<string, any[]>();
  
  const promises = codes.map(async (code) => {
    try {
      const res = await fetch(
        `https://datacenter.eastmoney.com/securities/api/data/v1/get?reportName=RPT_DMSK_FN_FHPS&columns=SECURITY_CODE,FHP_DATE,FHP_AMOUNT&filter=(SECURITY_CODE="${code}")&pageSize=6&sortColumns=FHP_DATE&sortTypes=-1`,
        { signal: AbortSignal.timeout(5000) }
      );
      const data = await res.json();
      const items = data.result?.data || [];
      results.set(code, items);
    } catch (e) {
      console.log(`[API] 获取 ${code} 分红数据失败`);
      results.set(code, []);
    }
  });
  
  await Promise.all(promises);
  console.log(`[API] 批量获取完成，成功 ${results.size} 只`);
  return results;
}

function calculateDividends(rawData: any[], latestPrice: number) {
  if (!rawData?.length || latestPrice <= 0) {
    return { ttm: 0, lfy: 0 };
  }

  const today = new Date();
  const oneYearAgo = new Date(today.getTime() - 365 * 24 * 60 * 60 * 1000);
  const lastYear = today.getFullYear() - 1;

  let ttm = 0, lfy = 0;

  for (const item of rawData) {
    const date = new Date(item.FHP_DATE);
    if (isNaN(date.getTime())) continue;
    
    const dividend = (parseFloat(item.FHP_AMOUNT) || 0) / 10;
    if (dividend <= 0) continue;

    if (date >= oneYearAgo) ttm += dividend;
    if (date.getFullYear() === lastYear) lfy += dividend;
  }

  return { ttm, lfy };
}

export default async function handler(): Promise<Response> {
  console.log('[API] 函数开始执行');
  const startTime = Date.now();
  
  try {
    const stocks = await fetchStockList();
    
    if (!stocks.length) {
      return Response.json({
        success: false,
        message: '无法获取A股数据，请稍后重试',
        ttm_ranking: [],
        lfy_ranking: [],
        total_count: 0
      });
    }

    const largeStocks = stocks
      .filter(s => (parseFloat(s.f20) || 0) > MARKET_CAP_THRESHOLD)
      .slice(0, MAX_STOCKS);
    
    console.log(`[API] 筛选出 ${largeStocks.length} 只大盘股`);

    if (!largeStocks.length) {
      return Response.json({
        success: false,
        message: '没有找到市值大于1000亿的股票',
        ttm_ranking: [],
        lfy_ranking: [],
        total_count: 0
      });
    }

    const codes = largeStocks.map((s: any) => s.f12);
    const dividendMap = await fetchDividendDataBatch(codes);

    const results: StockItem[] = [];
    
    for (const stock of largeStocks) {
      const code = stock.f12;
      const name = stock.f14;
      const marketCap = parseFloat(stock.f20) || 0;
      const latestPrice = parseFloat(stock.f2) || 0;

      if (!code || !name || marketCap <= 0 || latestPrice <= 0) continue;

      const rawData = dividendMap.get(code) || [];
      const { ttm, lfy } = calculateDividends(rawData, latestPrice);

      if (ttm > 0 || lfy > 0) {
        results.push({
          rank: 0,
          code,
          name,
          market_cap: Math.round(marketCap / 1e8),
          latest_price: Math.round(latestPrice * 100) / 100,
          ttm_dividends: Math.round(ttm * 10000) / 10000,
          lfy_dividends: Math.round(lfy * 10000) / 10000,
          ttm_yield: Math.round((ttm / latestPrice) * 10000) / 100,
          lfy_yield: Math.round((lfy / latestPrice) * 10000) / 100
        });
      }
    }

    console.log(`[API] 有效数据: ${results.length} 只股票`);

    const ttmRanking = results
      .filter(r => r.ttm_yield > 0)
      .sort((a, b) => b.ttm_yield - a.ttm_yield)
      .slice(0, 30)
      .map((item, i) => ({ ...item, rank: i + 1 }));

    const lfyRanking = results
      .filter(r => r.lfy_yield > 0)
      .sort((a, b) => b.lfy_yield - a.lfy_yield)
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
