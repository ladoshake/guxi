# AGENTS.md

## 项目概览

A股股息率排名工具——从 akshare 获取 A 股全量数据，筛选市值 > 1000 亿人民币的公司，分别按 TTM 和 LFY 股息率排名展示 Top 30。

## 技术栈

- **前端**: Vite 7 + TypeScript + Tailwind CSS 3（原生 TS，无框架）
- **后端代理**: Express（Node.js，端口 5000）
- **数据后端**: Python FastAPI + akshare（端口 8001）
- **包管理**: pnpm

## 目录结构

```
├── scripts/            # 构建与启动脚本
│   ├── build.sh        # 生产构建
│   ├── dev.sh          # 开发启动（同时启动 Python 后端 + Express）
│   ├── prepare.sh      # 依赖安装
│   └── start.sh        # 生产启动
├── server/
│   ├── python/         # Python 数据后端
│   │   ├── main.py     # FastAPI 应用
│   │   └── requirements.txt
│   ├── routes/         # Express API 路由
│   │   └── index.ts    # 代理路由到 Python 后端
│   ├── server.ts       # Express 入口
│   └── vite.ts         # Vite 中间件
├── src/                # 前端源码
│   ├── index.css       # 全局样式（含组件样式）
│   ├── index.ts        # 入口
│   └── main.ts         # 主逻辑（UI 渲染、数据获取）
├── index.html          # 入口 HTML
├── DESIGN.md           # 设计规范
└── .coze               # 部署配置
```

## 构建与运行

```bash
# 开发
pnpm dev          # 启动 Python 后端 (8001) + Express (5000)

# 生产构建
pnpm build

# 生产运行
pnpm start
```

## API 接口

| 路径 | 方法 | 说明 |
|------|------|------|
| `/api/dividend/rankings` | GET | 获取股息率排名（TTM + LFY 各 Top 30） |
| `/api/dividend/health` | GET | Python 后端健康检查 |
| `/api/health` | GET | Express 健康检查 |

## 股息率计算逻辑

- **TTM 股息率** = 过去 12 个月每股分红总和 / 最新股价 × 100%
- **LFY 股息率** = 最近完整财年每股分红总和 / 最新股价 × 100%
- 数据来源：akshare `stock_fhps_detail_em`（分红数据）+ `stock_zh_a_spot_em`（实时行情）
- 分红数据使用「现金分红-现金分红比例」列（每 10 股派 X 元），除以 10 得到每股分红

## 开发注意事项

- Python 后端端口固定 8001，Express 代理通过 `PYTHON_PORT` 环境变量连接
- 数据获取耗时约 60-90 秒（并发请求 216 只股票的分红数据）
- Express 代理超时设为 120 秒
- 前端使用原生 TypeScript + Tailwind CSS，无 React/Vue 框架
- 样式遵循 DESIGN.md 中的暗色金融终端风格
