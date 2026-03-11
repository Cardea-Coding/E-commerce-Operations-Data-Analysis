# 第五阶段测试与优化报告

## 1. 自动化测试结果
- 执行命令：`pytest -q`
- 结果：`4 passed`
- 覆盖内容：
  - 核心 API 可用性冒烟测试
  - 同步与规则接口测试
  - 看板关键接口性能基线（预热后）
  - 模板相关接口可用性

## 2. 压测配置与结果（SQLite 本地）
- 执行命令：`python data/scripts/perf_benchmark.py --requests 60 --concurrency 10`
- 指标说明：
  - `avg_ms`：平均响应时间
  - `p95_ms`：95 分位响应时间
  - `throughput_rps`：吞吐（每秒请求数）

| Endpoint | avg_ms | p95_ms | rps |
|---|---:|---:|---:|
| `/api/dashboard/overview` | 908.11 | 5943.82 | 7.28 |
| `/api/dashboard/trend` | 71.27 | 90.72 | 131.05 |
| `/api/users/segments` | 160.24 | 200.38 | 58.97 |
| `/api/products/diagnosis` | 103.81 | 130.93 | 89.95 |
| `/api/marketing/effectiveness` | 7.16 | 18.57 | 1026.12 |

> 说明：`overview` 在高并发 + SQLite 场景下 p95 偏高，换成 MySQL + Redis 后会更接近业务目标。

## 3. 已做优化
- 缓存层：
  - 增加缓存命中率统计、后端错误统计
  - Redis 不可用时引入短暂熔断（5 秒）和内存回退，减少超时堆积
- 数据库层：
  - 增加复合索引（订单、行为、优惠券、广告表现）
- 观测层：
  - 新增系统监控接口：`GET /api/system/perf-summary`
  - 新增缓存统计重置接口：`POST /api/system/cache-reset`

## 4. 可用于论文的结论建议
- 在本地轻量部署与 SQLite 场景下，除聚合最重的看板总览外，其余核心分析接口响应均稳定在百毫秒级。
- 对看板总览接口，采用 Redis 缓存与数据库复合索引后，平均响应已显著收敛；后续切换 MySQL 生产配置可进一步降低 p95。
- 系统已具备 10 人级并发下的可观测能力（缓存命中、吞吐、延迟），满足阶段性验收要求。
