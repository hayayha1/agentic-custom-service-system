# 路由与 Planner 联合评测集 v1

100 条固定用例：Fast-Path 40 条，Deep-Path 60 条。Deep 包含顺序依赖 20 条、并行关系 15 条、条件分支 15 条、混合与路由边界 10 条。

本目录的输入、答案和被测生产源码指纹在生成时冻结。已有版本不可由生成器覆盖；修改问题、答案或工具契约应发布新版本。

## 文件

- `inputs.jsonl`：仅包含随机 Case ID、用户问题与业务上下文，没有路由标签、DAG 标准答案或判定规则。Case ID 不进入模型请求。
- `private/answer_key.jsonl`：离线评分使用的标准答案，禁止推理进程读取。
- `manifest.json`：输入、答案、生成器与生产源码的 SHA256，以及各类用例数量。
- `../../../scripts/build_route_planner_dataset.py`：数据集作者脚本，不被推理进程导入。

## 运行顺序

在项目根目录运行，先推理、后评分。推理输出目录必须是新目录，防止覆盖已有原始记录。

```powershell
python -m scripts.run_route_planner_blind --mode native --repeats 3 --concurrency 3 --output scratch/route-planner-native-v1
python -m scripts.score_route_planner --run-dir scratch/route-planner-native-v1
```

推理进程只调用现有 `GoalPlanner`，不调用订单、退款、开票等业务处理器。不注入测试专用提示词、标准计划或模拟模型答案。模型使用项目已有原生工具调用协议与生产工具注册表。

缺少模型凭证时，native 模式直接失败，不会静默降级为离线结果。网络连接失败、超时、模型输出不符合 Schema 等均保留为原始错误，不按答案选择性补测。

## 盲测边界

推理进程使用 Python 文件审计钩子，拦截对 `private` 答案目录、历史 `results` 目录与数据集生成器的读取。模型请求投影保存在 `predictions.jsonl`，不记录 API Key 或授权请求头。

全部推理结束后生成 `inference_seal.json`，记录起止时间、源文件指纹、输入与原始输出指纹。评分器验证运行完整、文件未变、所有 Case 重复次数齐全、模型请求没有标签字段后，才加载答案。

该机制证明被测模型没有读取答案；数据集由本次工作编制，不宣称属于独立第三方认证集。

首轮真实模型结果已归档至 `results/native_v1/REPORT.md`，包含 300 次预测的原始记录与指纹。

## 结果

- `predictions.jsonl`：逐次预测、调用证据、无密钥请求投影和模型原始结构化输出。
- `inference_seal.json`：推理封存与文件读取审计。
- `report.json`：总指标、分类指标、逐 Case 与逐次判定。
- `REPORT.md`：可阅读的完整测试报告。
- `case_results.csv`：100 条用例的逐项结果，可直接筛选失败原因。

评分只检查路由与计划。图中无依赖不等于执行器已经并发运行；规划写操作不等于已经获得授权或真实提交业务。报修、库存、余额、条件字段等当前能力缺口单列为目标能力，失败不会被跳过或记为通过。
