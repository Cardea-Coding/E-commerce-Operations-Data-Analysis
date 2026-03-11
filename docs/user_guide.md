# 系统使用说明

## 1. 环境准备

1. 安装依赖：`pip install -r requirements.txt`
2. 推荐先用 SQLite 本地演示：
   - PowerShell: `$env:DATABASE_URL='sqlite:///demo.db'`

## 2. 初始化与数据准备

1. 初始化表结构：`flask --app run.py init-db`
2. 生成模拟数据（全量）：`python data/scripts/generate_mock_data.py`
3. 触发一次增量同步：`python data/scripts/run_sync_task.py --source mock_api`

## 3. 启动系统

1. 启动服务：`python run.py`
2. 浏览器访问：`http://127.0.0.1:5000`

## 4. 主要功能操作路径

- **运营看板**
  - 页面顶部选择时间、地区、品类、活动、粒度
  - 点击“应用筛选”查看联动图表与指标卡变化
- **用户画像分析**
  - 通过 `GET /api/users/segments` 查看 RFM 六类分群结果
- **商品诊断分析**
  - 通过 `GET /api/products/diagnosis` 查看热销/滞销/利润/差评原因
- **营销效果分析**
  - 通过 `GET /api/marketing/effectiveness` 对比活动 ROI
- **决策建议**
  - 通过 `GET /api/decision/suggestions` 查看建议 + 原因 + 优先级
- **规则管理**
  - `GET /api/decision/rules` 查看规则
  - `POST /api/decision/rules` 更新规则阈值与策略文本
- **报表导出**
  - `POST /api/reports/export` 直接导出
  - `POST /api/reports/export-by-template` 按模板导出
  - `GET /api/reports/export-logs` 查看导出记录

## 5. 测试与性能观测

1. 自动化测试：`pytest -q`
2. 压测：`python data/scripts/perf_benchmark.py --requests 60 --concurrency 10`
3. 系统监控：
   - `GET /api/system/perf-summary`
   - `POST /api/system/cache-reset`

## 6. 常见问题

- **页面无数据**
  - 先确认已执行模拟数据脚本与同步脚本
- **响应慢**
  - 检查是否使用 SQLite；建议切换 MySQL + Redis
- **导出失败**
  - 检查 `data/exports` 目录写权限
