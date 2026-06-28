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

interface RankingsData {
  success: boolean;
  ttm_ranking: StockItem[];
  lfy_ranking: StockItem[];
  total_count: number;
  data_time: string;
  message?: string;
}

type TabType = 'ttm' | 'lfy';

function formatMarketCap(yi: number): string {
  if (yi >= 10000) {
    return `${(yi / 10000).toFixed(2)}万亿`;
  }
  return `${yi.toFixed(0)}亿`;
}

function formatPrice(price: number): string {
  return price.toFixed(2);
}

function formatYield(y: number): string {
  return `${y.toFixed(2)}%`;
}

function getYieldColor(y: number): string {
  if (y >= 5) return 'color: #34d399; font-weight: 600;';
  if (y >= 3) return 'color: #d4a853; font-weight: 600;';
  return 'color: #e1e4e8;';
}

function getRankBadge(rank: number): string {
  if (rank === 1) return 'background: #d4a853; color: #1a1d23;';
  if (rank === 2) return 'background: #8b949e; color: #1a1d23;';
  if (rank === 3) return 'background: #cd7f32; color: #1a1d23;';
  return 'color: #8b949e;';
}

function renderTable(data: StockItem[], type: TabType): string {
  if (data.length === 0) {
    return `
      <div class="flex flex-col items-center justify-center py-20 text-secondary">
        <svg class="w-12 h-12 mb-4 opacity-40" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
        </svg>
        <p class="text-sm">暂无数据</p>
      </div>`;
  }

  const rows = data
    .map(
      (item) => `
    <tr class="table-row">
      <td class="table-cell text-center" style="width: 60px;">
        <span class="rank-badge" style="${getRankBadge(item.rank)}">${item.rank}</span>
      </td>
      <td class="table-cell font-medium" style="width: 100px;">${item.code}</td>
      <td class="table-cell font-medium" style="width: 120px;">${item.name}</td>
      <td class="table-cell text-right" style="width: 120px;">${formatMarketCap(item.market_cap)}</td>
      <td class="table-cell text-right" style="width: 100px;">${formatPrice(item.latest_price)}</td>
      <td class="table-cell text-right" style="width: 120px;">${item.ttm_dividends.toFixed(4)}</td>
      <td class="table-cell text-right" style="width: 120px;">${item.lfy_dividends.toFixed(4)}</td>
      <td class="table-cell text-right font-semibold" style="width: 100px; ${getYieldColor(type === 'ttm' ? item.ttm_yield : item.lfy_yield)}">
        ${formatYield(type === 'ttm' ? item.ttm_yield : item.lfy_yield)}
      </td>
    </tr>`
    )
    .join('');

  return `
    <div class="table-wrapper">
      <table class="data-table">
        <thead>
          <tr>
            <th class="table-header text-center" style="width: 60px;">排名</th>
            <th class="table-header" style="width: 100px;">代码</th>
            <th class="table-header" style="width: 120px;">名称</th>
            <th class="table-header text-right" style="width: 120px;">总市值</th>
            <th class="table-header text-right" style="width: 100px;">最新价</th>
            <th class="table-header text-right" style="width: 120px;">TTM分红</th>
            <th class="table-header text-right" style="width: 120px;">LFY分红</th>
            <th class="table-header text-right" style="width: 100px;">股息率</th>
          </tr>
        </thead>
        <tbody>
          ${rows}
        </tbody>
      </table>
    </div>`;
}

function renderSkeleton(): string {
  const rows = Array.from({ length: 8 })
    .map(
      () => `
    <tr class="table-row">
      <td class="table-cell text-center" style="width: 60px;"><div class="skeleton-line" style="width: 24px; margin: 0 auto;"></div></td>
      <td class="table-cell" style="width: 100px;"><div class="skeleton-line" style="width: 60px;"></div></td>
      <td class="table-cell" style="width: 120px;"><div class="skeleton-line" style="width: 50px;"></div></td>
      <td class="table-cell text-right" style="width: 120px;"><div class="skeleton-line" style="width: 70px; margin-left: auto;"></div></td>
      <td class="table-cell text-right" style="width: 100px;"><div class="skeleton-line" style="width: 40px; margin-left: auto;"></div></td>
      <td class="table-cell text-right" style="width: 120px;"><div class="skeleton-line" style="width: 50px; margin-left: auto;"></div></td>
      <td class="table-cell text-right" style="width: 120px;"><div class="skeleton-line" style="width: 50px; margin-left: auto;"></div></td>
      <td class="table-cell text-right" style="width: 100px;"><div class="skeleton-line" style="width: 50px; margin-left: auto;"></div></td>
    </tr>`
    )
    .join('');

  return `
    <div class="loading-banner">
      <svg class="loading-spinner" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor">
        <circle cx="12" cy="12" r="10" stroke-width="2" stroke-dasharray="60" stroke-dashoffset="20">
          <animateTransform attributeName="transform" type="rotate" from="0 12 12" to="360 12 12" dur="1s" repeatCount="indefinite"/>
        </circle>
      </svg>
      <span>正在刷新数据，请稍后...</span>
    </div>
    <div class="table-wrapper">
      <table class="data-table">
        <thead>
          <tr>
            <th class="table-header text-center" style="width: 60px;">排名</th>
            <th class="table-header" style="width: 100px;">代码</th>
            <th class="table-header" style="width: 120px;">名称</th>
            <th class="table-header text-right" style="width: 120px;">总市值</th>
            <th class="table-header text-right" style="width: 100px;">最新价</th>
            <th class="table-header text-right" style="width: 120px;">TTM分红</th>
            <th class="table-header text-right" style="width: 120px;">LFY分红</th>
            <th class="table-header text-right" style="width: 100px;">股息率</th>
          </tr>
        </thead>
        <tbody>
          ${rows}
        </tbody>
      </table>
    </div>`;
}

function renderApp(data: RankingsData | null, loading: boolean, activeTab: TabType, error: string | null): string {
  const rankingData = activeTab === 'ttm' ? data?.ttm_ranking : data?.lfy_ranking;
  const tabLabel = activeTab === 'ttm' ? 'TTM（过去12个月）' : 'LFY（最近完整财年）';
  const yieldLabel = activeTab === 'ttm' ? 'TTM股息率' : 'LFY股息率';

  let contentHtml = '';
  if (loading) {
    contentHtml = renderSkeleton();
  } else if (error) {
    contentHtml = `
      <div class="flex flex-col items-center justify-center py-20 text-secondary">
        <svg class="w-12 h-12 mb-4" style="color: #f87171;" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4.5c-.77-.833-2.694-.833-3.464 0L3.34 16.5c-.77.833.192 2.5 1.732 2.5z" />
        </svg>
        <p class="text-sm" style="color: #f87171;">${error}</p>
        <button onclick="window.location.reload()" class="mt-4 px-4 py-2 rounded text-sm font-medium" style="background: #30363d; color: #e1e4e8; border: 1px solid #4a4f58; cursor: pointer;">
          重新加载
        </button>
      </div>`;
  } else if (rankingData && rankingData.length > 0) {
    contentHtml = renderTable(rankingData, activeTab);
  } else {
    contentHtml = `
      <div class="flex flex-col items-center justify-center py-20 text-secondary">
        <p class="text-sm">暂无排名数据</p>
      </div>`;
  }

  const totalCount = data?.total_count ?? 0;
  const rankCount = rankingData?.length ?? 0;

  return `
    <div class="app-container">
      <!-- Header -->
      <header class="app-header">
        <div class="header-content">
          <div>
            <h1 class="app-title">A股股息率排名</h1>
            <p class="app-subtitle">市值 > 1000亿人民币 · 股息率 Top 30</p>
          </div>
          <div class="header-meta">
            ${data ? `<span class="meta-badge">${totalCount} 家公司符合条件</span>` : ''}
            ${data?.data_time ? `<span class="meta-time">数据时间: ${data.data_time}</span>` : ''}
            <button class="refresh-btn" id="refresh-btn" ${loading ? 'disabled' : ''}>
              <svg class="refresh-icon ${loading ? 'spinning' : ''}" width="16" height="16" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
              </svg>
              刷新数据
            </button>
          </div>
        </div>
      </header>

      <!-- Tab Switcher -->
      <div class="tab-bar">
        <button class="tab-btn ${activeTab === 'ttm' ? 'tab-active' : ''}" data-tab="ttm">
          TTM 股息率
          <span class="tab-hint">过去12个月</span>
        </button>
        <button class="tab-btn ${activeTab === 'lfy' ? 'tab-active' : ''}" data-tab="lfy">
          LFY 股息率
          <span class="tab-hint">最近完整财年</span>
        </button>
      </div>

      <!-- Tab Description -->
      <div class="tab-desc">
        <div class="desc-icon">
          <svg width="16" height="16" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
        </div>
        <span>当前展示：<strong>${tabLabel}</strong> 股息率排名 · 股息率 = 每股分红 / 最新股价 × 100%</span>
      </div>

      <!-- Table -->
      <div class="table-container">
        ${contentHtml}
      </div>

      <!-- Footer -->
      <footer class="app-footer">
        <span>数据来源：AKShare · 股息率根据实际分红金额自行计算</span>
        <span>仅展示市值 > 1000亿人民币的公司</span>
      </footer>
    </div>`;
}

// 状态管理
let currentData: RankingsData | null = null;
let isLoading = true;
let activeTab: TabType = 'ttm';
let fetchError: string | null = null;

function updateUI(): void {
  const app = document.getElementById('app');
  if (!app) return;
  app.innerHTML = renderApp(currentData, isLoading, activeTab, fetchError);
  bindEvents();
}

function bindEvents(): void {
  const tabBtns = document.querySelectorAll<HTMLButtonElement>('.tab-btn');
  tabBtns.forEach((btn) => {
    btn.addEventListener('click', () => {
      const tab = btn.dataset.tab as TabType;
      if (tab && tab !== activeTab) {
        activeTab = tab;
        updateUI();
      }
    });
  });

  const refreshBtn = document.getElementById('refresh-btn');
  if (refreshBtn) {
    refreshBtn.addEventListener('click', () => {
      if (!isLoading) {
        fetchData();
      }
    });
  }
}

async function fetchData(): Promise<void> {
  console.log('[DEBUG] 开始获取数据...');
  isLoading = true;
  fetchError = null;
  updateUI();

  try {
    console.log('[DEBUG] 发送 API 请求到 /api/dividend/rankings');
    const response = await fetch('/api/dividend/rankings', {
      signal: AbortSignal.timeout(180000),
    });
    console.log(`[DEBUG] API 响应状态: ${response.status} ${response.statusText}`);

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }

    const data: RankingsData = await response.json();
    console.log('[DEBUG] API 响应数据:', JSON.stringify({
      success: data.success,
      total_count: data.total_count,
      ttm_count: data.ttm_ranking?.length ?? 0,
      lfy_count: data.lfy_ranking?.length ?? 0,
      data_time: data.data_time,
      message: data.message
    }, null, 2));

    if (!data.success) {
      throw new Error(data.message || '数据获取失败');
    }

    currentData = data;
    isLoading = false;
    console.log('[DEBUG] 数据加载成功，更新 UI');
    updateUI();
  } catch (err) {
    isLoading = false;
    console.error('[DEBUG] 数据获取失败:', err);
    if (err instanceof DOMException && err.name === 'TimeoutError') {
      fetchError = '请求超时，数据量较大请稍后重试';
    } else if (err instanceof Error) {
      fetchError = err.message || '网络请求失败';
    } else {
      fetchError = '未知错误';
    }
    updateUI();
  }
}

export function initApp(): void {
  const app = document.getElementById('app');
  if (!app) {
    console.error('App element not found');
    return;
  }

  // 初始渲染
  updateUI();

  // 获取数据
  fetchData();
}
