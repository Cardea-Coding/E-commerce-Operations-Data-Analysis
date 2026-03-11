# 电商运营数据分析系统

技术栈：`Python + Flask + MySQL + Redis + Pandas + ECharts`

## 当前完成度（第五阶段已落地）
- 完成四层架构的后端骨架与核心 API
- 完成数据库模型、建表 SQL、模拟数据生成脚本
- 完成核心分析能力：看板指标、RFM 用户分群、商品诊断、营销 ROI、运营建议
- 完成报表工具：自定义指标表达式计算、Excel/PDF 导出
- 完成多源数据接入与同步流水线：
  - 支持 `mock_api` / `taobao_api` / `mysql` 三类数据源适配入口
  - 完成“拉取 -> 清洗 -> 入库 -> 日志”链路
  - 提供手动触发与循环定时脚本
- 完成多维度分析应用层联动看板：
  - 时间/地区/品类/活动/粒度 多维筛选
  - 核心指标卡 + 异常预警展示
  - GMV 趋势、用户分群、地区分布、品类分布
  - 营销活动效果对比表
- 完成运营决策支持深化：
  - 决策规则库配置化（规则可查可改）
  - 智能建议补充原因说明与优先级评分（1-100）
  - 自定义指标模板与报表模板可保存
  - 按模板导出与导出记录追踪
- 完成系统测试与优化：
  - 新增 `tests/` 自动化冒烟与性能基线测试
  - 新增压测脚本 `data/scripts/perf_benchmark.py`（支持并发参数）
  - 新增系统监控接口（缓存命中率、数据量、关键接口单次延迟）
  - 完成常用查询复合索引优化（订单、行为、优惠券、广告）

## 目录结构
- `app/api/`：分析接口层
- `app/services/`：业务与分析逻辑
- `app/utils/`：数据接入与清洗工具
- `data/sql/`：建表脚本
- `data/scripts/`：模拟数据脚本

## 快速启动
1. 安装依赖：
   - `pip install -r requirements.txt`
2. 配置数据库（默认连接在 `config.py`，按需修改账号密码）
3. 初始化并生成模拟数据：
   - `python data/scripts/generate_mock_data.py`
4. 启动服务：
   - `python run.py`

## 已提供接口（示例）
- `GET /health`
- `GET /api/dashboard/overview`
- `GET /api/dashboard/trend`
- `GET /api/users/segments`
- `GET /api/products/diagnosis`
- `GET /api/marketing/effectiveness`
- `GET /api/decision/suggestions`
- `POST /api/reports/custom-metric`
- `POST /api/reports/export`
- `POST /api/data-sync/run`
- `GET /api/data-sync/logs`
- `GET /api/dashboard/dimensions`
- `GET /api/dashboard/drilldown`
- `GET /api/decision/rules`
- `POST /api/decision/rules`
- `GET /api/reports/metric-templates`
- `POST /api/reports/metric-templates`
- `GET /api/reports/report-templates`
- `POST /api/reports/report-templates`
- `POST /api/reports/export-by-template`
- `GET /api/reports/export-logs`
- `GET /api/system/perf-summary`
- `POST /api/system/cache-reset`

## 第二阶段运行方式（数据接入与同步）
1. 初始化数据库表：
   - `flask --app run.py init-db`
2. 手动执行一次同步：
   - `python data/scripts/run_sync_task.py --source mock_api`
3. 每 30 分钟循环同步（模拟实时）：
   - `python data/scripts/run_sync_task.py --source mock_api --loop --interval 30`
4. API 方式触发：
   - `POST /api/data-sync/run`，请求体示例：`{"source":"mock_api","mode":"manual"}`
5. 查看同步日志：
   - `GET /api/data-sync/logs?limit=20`

## 第五阶段运行方式（测试与性能）
1. 运行自动化测试：
   - `pytest -q`
2. 执行压测脚本（默认 120 请求、12 并发）：
   - `python data/scripts/perf_benchmark.py`
3. 自定义压测参数：
   - `python data/scripts/perf_benchmark.py --requests 200 --concurrency 20`
4. 查看系统性能摘要：
   - `GET /api/system/perf-summary`

## 文档说明
- 系统使用说明：`docs/user_guide.md`
- 测试与优化报告：`docs/phase5_test_report.md`

## 扩展方向
1. 接入真实淘宝开放平台签名调用与增量拉取
2. 引入 Celery/APScheduer 做生产级调度与重试
3. 加入权限管理（管理员/运营/访客）与审计日志
4. 增加 Docker 部署与 CI 自动测试流水线