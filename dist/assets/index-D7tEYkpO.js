(function(){const e=document.createElement("link").relList;if(e&&e.supports&&e.supports("modulepreload"))return;for(const l of document.querySelectorAll('link[rel="modulepreload"]'))s(l);new MutationObserver(l=>{for(const a of l)if(a.type==="childList")for(const n of a.addedNodes)n.tagName==="LINK"&&n.rel==="modulepreload"&&s(n)}).observe(document,{childList:!0,subtree:!0});function r(l){const a={};return l.integrity&&(a.integrity=l.integrity),l.referrerPolicy&&(a.referrerPolicy=l.referrerPolicy),l.crossOrigin==="use-credentials"?a.credentials="include":l.crossOrigin==="anonymous"?a.credentials="omit":a.credentials="same-origin",a}function s(l){if(l.ep)return;l.ep=!0;const a=r(l);fetch(l.href,a)}})();function f(t){return t>=1e4?`${(t/1e4).toFixed(2)}万亿`:`${t.toFixed(0)}亿`}function b(t){return t.toFixed(2)}function x(t){return`${t.toFixed(2)}%`}function g(t){return t>=5?"color: #34d399; font-weight: 600;":t>=3?"color: #d4a853; font-weight: 600;":"color: #e1e4e8;"}function y(t){return t===1?"background: #d4a853; color: #1a1d23;":t===2?"background: #8b949e; color: #1a1d23;":t===3?"background: #cd7f32; color: #1a1d23;":"color: #8b949e;"}function m(t,e){return t.length===0?`
      <div class="flex flex-col items-center justify-center py-20 text-secondary">
        <svg class="w-12 h-12 mb-4 opacity-40" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
        </svg>
        <p class="text-sm">暂无数据</p>
      </div>`:`
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
          ${t.map(s=>`
    <tr class="table-row">
      <td class="table-cell text-center" style="width: 60px;">
        <span class="rank-badge" style="${y(s.rank)}">${s.rank}</span>
      </td>
      <td class="table-cell font-medium" style="width: 100px;">${s.code}</td>
      <td class="table-cell font-medium" style="width: 120px;">${s.name}</td>
      <td class="table-cell text-right" style="width: 120px;">${f(s.market_cap)}</td>
      <td class="table-cell text-right" style="width: 100px;">${b(s.latest_price)}</td>
      <td class="table-cell text-right" style="width: 120px;">${s.ttm_dividends.toFixed(4)}</td>
      <td class="table-cell text-right" style="width: 120px;">${s.lfy_dividends.toFixed(4)}</td>
      <td class="table-cell text-right font-semibold" style="width: 100px; ${g(e==="ttm"?s.ttm_yield:s.lfy_yield)}">
        ${x(e==="ttm"?s.ttm_yield:s.lfy_yield)}
      </td>
    </tr>`).join("")}
        </tbody>
      </table>
    </div>`}function v(){return`
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
          ${Array.from({length:8}).map(()=>`
    <tr class="table-row">
      <td class="table-cell text-center" style="width: 60px;"><div class="skeleton-line" style="width: 24px; margin: 0 auto;"></div></td>
      <td class="table-cell" style="width: 100px;"><div class="skeleton-line" style="width: 60px;"></div></td>
      <td class="table-cell" style="width: 120px;"><div class="skeleton-line" style="width: 50px;"></div></td>
      <td class="table-cell text-right" style="width: 120px;"><div class="skeleton-line" style="width: 70px; margin-left: auto;"></div></td>
      <td class="table-cell text-right" style="width: 100px;"><div class="skeleton-line" style="width: 40px; margin-left: auto;"></div></td>
      <td class="table-cell text-right" style="width: 120px;"><div class="skeleton-line" style="width: 50px; margin-left: auto;"></div></td>
      <td class="table-cell text-right" style="width: 120px;"><div class="skeleton-line" style="width: 50px; margin-left: auto;"></div></td>
      <td class="table-cell text-right" style="width: 100px;"><div class="skeleton-line" style="width: 50px; margin-left: auto;"></div></td>
    </tr>`).join("")}
        </tbody>
      </table>
    </div>`}function w(t,e,r,s){const l=r==="ttm"?t?.ttm_ranking:t?.lfy_ranking,a=r==="ttm"?"TTM（过去12个月）":"LFY（最近完整财年）";let n="";e?n=v():s?n=`
      <div class="flex flex-col items-center justify-center py-20 text-secondary">
        <svg class="w-12 h-12 mb-4" style="color: #f87171;" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4.5c-.77-.833-2.694-.833-3.464 0L3.34 16.5c-.77.833.192 2.5 1.732 2.5z" />
        </svg>
        <p class="text-sm" style="color: #f87171;">${s}</p>
        <button onclick="window.location.reload()" class="mt-4 px-4 py-2 rounded text-sm font-medium" style="background: #30363d; color: #e1e4e8; border: 1px solid #4a4f58; cursor: pointer;">
          重新加载
        </button>
      </div>`:l&&l.length>0?n=m(l,r):n=`
      <div class="flex flex-col items-center justify-center py-20 text-secondary">
        <p class="text-sm">暂无排名数据</p>
      </div>`;const u=t?.total_count??0;return l?.length,`
    <div class="app-container">
      <!-- Header -->
      <header class="app-header">
        <div class="header-content">
          <div>
            <h1 class="app-title">A股股息率排名</h1>
            <p class="app-subtitle">市值 > 1000亿人民币 · 股息率 Top 30</p>
          </div>
          <div class="header-meta">
            ${t?`<span class="meta-badge">${u} 家公司符合条件</span>`:""}
            ${t?.data_time?`<span class="meta-time">数据时间: ${t.data_time}</span>`:""}
            <button class="refresh-btn" id="refresh-btn" ${e?"disabled":""}>
              <svg class="refresh-icon ${e?"spinning":""}" width="16" height="16" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
              </svg>
              刷新数据
            </button>
          </div>
        </div>
      </header>

      <!-- Tab Switcher -->
      <div class="tab-bar">
        <button class="tab-btn ${r==="ttm"?"tab-active":""}" data-tab="ttm">
          TTM 股息率
          <span class="tab-hint">过去12个月</span>
        </button>
        <button class="tab-btn ${r==="lfy"?"tab-active":""}" data-tab="lfy">
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
        <span>当前展示：<strong>${a}</strong> 股息率排名 · 股息率 = 每股分红 / 最新股价 × 100%</span>
      </div>

      <!-- Table -->
      <div class="table-container">
        ${n}
      </div>

      <!-- Footer -->
      <footer class="app-footer">
        <span>数据来源：AKShare · 股息率根据实际分红金额自行计算</span>
        <span>仅展示市值 > 1000亿人民币的公司</span>
      </footer>
    </div>`}let h=null,o=!0,c="ttm",i=null;function d(){const t=document.getElementById("app");t&&(t.innerHTML=w(h,o,c,i),k())}function k(){document.querySelectorAll(".tab-btn").forEach(r=>{r.addEventListener("click",()=>{const s=r.dataset.tab;s&&s!==c&&(c=s,d())})});const e=document.getElementById("refresh-btn");e&&e.addEventListener("click",()=>{o||p()})}async function p(){console.log("[DEBUG] 开始获取数据..."),o=!0,i=null,d();try{console.log("[DEBUG] 发送 API 请求到 /api/dividend/rankings");const t=await fetch("/api/dividend/rankings",{signal:AbortSignal.timeout(18e4)});if(console.log(`[DEBUG] API 响应状态: ${t.status} ${t.statusText}`),!t.ok)throw new Error(`HTTP ${t.status}: ${t.statusText}`);const e=await t.json();if(console.log("[DEBUG] API 响应数据:",JSON.stringify({success:e.success,total_count:e.total_count,ttm_count:e.ttm_ranking?.length??0,lfy_count:e.lfy_ranking?.length??0,data_time:e.data_time,message:e.message},null,2)),!e.success)throw new Error(e.message||"数据获取失败");h=e,o=!1,console.log("[DEBUG] 数据加载成功，更新 UI"),d()}catch(t){o=!1,console.error("[DEBUG] 数据获取失败:",t),t instanceof DOMException&&t.name==="TimeoutError"?i="请求超时，数据量较大请稍后重试":t instanceof Error?i=t.message||"网络请求失败":i="未知错误",d()}}function $(){if(!document.getElementById("app")){console.error("App element not found");return}d(),p()}$();
