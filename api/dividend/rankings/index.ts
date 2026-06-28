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

async function fetchStockList(): Promise<any[]> {
  try {
    const res = await fetch('https://push2.eastmoney.com/api/qt/clist/get?pn=1&pz=500&po=1&np=1&ut=bd1d9ddb04089700cf9c27f6f7426281&fltt=2&invt=2&fid=f3&fs=m:0+t:6,m:0+t:13,m:0+t:80,m:1+t:2,m:1+t:23&fields=f1,f2,f3,f4,f5,f6,f7,f8,f9,f10,f12,f13,f14,f15,f16,f17,f18,f20,f21,f23,f24,f25,f26,f22,f33,f11,f62,f128,f136,f115,f152');
    const data = await res.json();
    if (data.data && data.data.diff) {
      return data.data.diff;
    }
    return [];
  } catch {
    return [];
  }
}

async function fetchDividendData(code: string): Promise<any[]> {
  try {
    const res = await fetch(`https://datacenter.eastmoney.com/securities/api/data/v1/get?reportName=RPT_DMSK_FN_FHPS&columns=SECURITY_CODE,SECURITY_NAME_ABBR,FHP_DATE,FHP_AMOUNT,FHP_TYPE&filter=(SECURITY_CODE="${code}")&pageSize=50&sortColumns=FHP_DATE&sortTypes=-1`);
    const data = await res.json();
    if (data.result && data.result.data) {
      return data.result.data;
    }
    return [];
  } catch {
    return [];
  }
}

function parseDividendData(rawData: any[], latestPrice: number) {
  if (!rawData || rawData.length === 0 || latestPrice <= 0) {
    return { ttmDividends: 0, lfyDividends: 0 };
  }

  const today = new Date();
  const oneYearAgo = new Date(today.getTime() - 365 * 24 * 60 * 60 * 1000);
  const currentYear = today.getFullYear();

  let ttmDividends = 0;
  let lfyDividends = 0;

  for (const item of rawData) {
    const dateStr = item.FHP_DATE;
    const amount = parseFloat(item.FHP_AMOUNT) || 0;

    if (!dateStr || amount <= 0) continue;

    const date = new Date(dateStr);
    if (isNaN(date.getTime())) continue;

    const dividend = amount / 10;

    if (date >= oneYearAgo) {
      ttmDividends += dividend;
    }

    if (date.getFullYear() === currentYear - 1) {
      lfyDividends += dividend;
    }
  }

  if (lfyDividends === 0) {
    for (const item of rawData) {
      const dateStr = item.FHP_DATE;
      const amount = parseFloat(item.FHP_AMOUNT) || 0;

      if (!dateStr || amount <= 0) continue;

      const date = new Date(dateStr);
      if (isNaN(date.getTime())) continue;

      if (date.getFullYear() === currentYear - 2) {
        lfyDividends += amount / 10;
      }
    }
  }

  return { ttmDividends, lfyDividends };
}

export default async function handler(
  request: Request
): Promise<Response> {
  try {
    const stocks = await fetchStockList();
    
    if (stocks.length === 0) {
      return Response.json({
        success: false,
        message: '无法获取A股数据',
        ttm_ranking: [],
        lfy_ranking: [],
        total_count: 0
      });
    }

    const largeStocks = stocks.filter(s => {
      const marketCap = parseFloat(s.f20) || 0;
      return marketCap > MARKET_CAP_THRESHOLD;
    });

    if (largeStocks.length === 0) {
      return Response.json({
        success: true,
        message: '没有市值大于1000亿的公司',
        ttm_ranking: [],
        lfy_ranking: [],
        total_count: 0
      });
    }

    const results: StockItem[] = [];

    for (const stock of largeStocks.slice(0, 50)) {
      const code = stock.f12;
      const name = stock.f14;
      const marketCap = parseFloat(stock.f20) || 0;
      const latestPrice = parseFloat(stock.f2) || 0;

      if (!code || !name || marketCap <= 0 || latestPrice <= 0) {
        continue;
      }

      const dividendData = await fetchDividendData(code);
      const { ttmDividends, lfyDividends } = parseDividendData(dividendData, latestPrice);

      const ttmYield = ttmDividends > 0 ? (ttmDividends / latestPrice) * 100 : 0;
      const lfyYield = lfyDividends > 0 ? (lfyDividends / latestPrice) * 100 : 0;

      if (ttmYield > 0 || lfyYield > 0) {
        results.push({
          rank: 0,
          code,
          name,
          market_cap: Math.round(marketCap / 1e8 * 100) / 100,
          latest_price: Math.round(latestPrice * 100) / 100,
          ttm_dividends: Math.round(ttmDividends * 10000) / 10000,
          lfy_dividends: Math.round(lfyDividends * 10000) / 10000,
          ttm_yield: Math.round(ttmYield * 100) / 100,
          lfy_yield: Math.round(lfyYield * 100) / 100
        });
      }

      await new Promise(resolve => setTimeout(resolve, 100));
    }

    const ttmSorted = results
      .filter(r => r.ttm_yield > 0)
      .sort((a, b) => b.ttm_yield - a.ttm_yield)
      .slice(0, 30);

    const lfySorted = results
      .filter(r => r.lfy_yield > 0)
      .sort((a, b) => b.lfy_yield - a.lfy_yield)
      .slice(0, 30);

    const response: RankingsResponse = {
      success: true,
      ttm_ranking: ttmSorted.map((item, i) => ({ ...item, rank: i + 1 })),
      lfy_ranking: lfySorted.map((item, i) => ({ ...item, rank: i + 1 })),
      total_count: largeStocks.length,
      data_time: new Date().toLocaleString('zh-CN')
    };

    return Response.json(response);
  } catch (error) {
    const message = error instanceof Error ? error.message : '未知错误';
    return Response.json({
      success: false,
      message: `数据获取失败: ${message}`,
      ttm_ranking: [],
      lfy_ranking: [],
      total_count: 0
    });
  }
}