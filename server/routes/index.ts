import { Router } from 'express';

const router = Router();

// Python 后端地址
const PYTHON_BACKEND = `http://localhost:${process.env.PYTHON_PORT || '8001'}`;

// 代理股息率排名接口到 Python 后端
router.get('/api/dividend/rankings', async (_req, res) => {
  try {
    const response = await fetch(`${PYTHON_BACKEND}/api/dividend/rankings`, {
      signal: AbortSignal.timeout(180000), // 3分钟超时，数据获取需要时间
    });
    const data = await response.json();
    res.json(data);
  } catch (err) {
    const message = err instanceof Error ? err.message : 'Unknown error';
    console.error('代理股息率排名请求失败:', message);
    res.status(500).json({
      success: false,
      error: '数据获取失败，请稍后重试',
      detail: message,
    });
  }
});

// 健康检查
router.get('/api/dividend/health', async (_req, res) => {
  try {
    const response = await fetch(`${PYTHON_BACKEND}/api/dividend/health`);
    const data = await response.json();
    res.json(data);
  } catch {
    res.json({ status: 'python_backend_unreachable' });
  }
});

// 保留原有路由
router.get('/api/hello', (_req, res) => {
  res.json({
    message: 'A股股息率排名工具',
    timestamp: new Date().toISOString(),
  });
});

router.get('/api/health', (_req, res) => {
  res.json({
    status: 'ok',
    env: process.env.COZE_PROJECT_ENV,
    timestamp: new Date().toISOString(),
  });
});

export default router;
