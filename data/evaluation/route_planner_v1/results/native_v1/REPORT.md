# 路由与 Planner 联合盲测结果

模型：`deepseek-chat`；运行方式：`native`。
固定用例 100 条，每条 3 次，共 300 次。

## 主要结果

| 指标 | 结果 |
|---|---:|
| 全项通过 | 164/300（54.7%） |
| 路由准确率 | 71.0% |
| Fast 误入 Deep | 42/120 |
| Deep 误入 Fast | 45/180 |
| Deep 目标完整覆盖率 | 61.1% |
| Deep DAG 结构合法率 | 79.4% |
| 必要先后关系满足率 | 47.2% |
| 独立任务关系满足率 | 57.6% |
| 结构化条件满足率 | 0.0% |
| 推理错误 | 20 |
| 禁止动作被规划 | 3 次 |
| 无依据订单实体 | 0 次 |
| 路由判断 P95 | 0.041 ms |
| 预期 Fast 请求至规划返回 P95（包含误入慢通道） | 2.86 s |
| Deep 请求至规划完成 P95 | 3.79 s |
| 已上报模型 Token | 543796 |

完整通过要求路由、调用证据、目标、实体、依赖、独立性、条件、冗余和禁止动作全部合格。所有目标能力缺口均计入失败，没有跳过。

## 按类别

| 类别 | 次数 | 路由准确率 | 全项通过率 | 目标完整覆盖率 |
|---|---:|---:|---:|---:|
| fast_greeting | 30 | 60.0% | 60.0% | 不适用 |
| fast_knowledge | 60 | 60.0% | 60.0% | 不适用 |
| fast_handoff | 30 | 80.0% | 80.0% | 不适用 |
| deep_sequential | 60 | 90.0% | 70.0% | 90.0% |
| deep_parallel | 45 | 73.3% | 71.1% | 71.1% |
| deep_conditional | 45 | 66.7% | 6.7% | 33.3% |
| deep_mixed | 30 | 60.0% | 30.0% | 30.0% |

## 按能力范围

| 范围 | 次数 | 路由准确率 | 全项通过率 |
|---|---:|---:|---:|
| current_regression | 246 | 70.7% | 66.7% |
| target_capability | 54 | 72.2% | 0.0% |

## 失败归因与结论

本次结果未达到设计方案提出的路由、目标覆盖、依赖、并行与条件分支验收门槛。

1. **路由覆盖不足且缺少组合语义判断。**‘周末客服也上班吗？’等简单问题进入 Deep；含‘政策/规则’的复合请求被提前送入 Fast，后续业务目标丢失。
2. **否定转人工被错误匹配。**‘不要转人工，先查物流，再开票’被判为立即人工转接，属于禁止动作误规划。
3. **顺序约束没有稳定落实到图。**部分计划的 summary 写了‘最后查询物流’，实际物流节点却只依赖查单，没有依赖开票节点。评分使用图结构而非 summary 中的承诺。
4. **输出契约存在冲突。**生产 Schema 向模型提供 CLARIFICATION 类型，但 DAG 校验器要求每个节点严格匹配 READ_TOOL/WRITE_TOOL/KNOWLEDGE_QA，澄清节点因此被拒绝。
5. **结构化条件与业务工具仍有缺口。**TaskPlan 缺少可执行条件字段，库存、余额、报修等工具未完整注册；目标能力验收保留这些失败。

校验错误统计：
- Value error, Task type must match the tool registry：19 次。
- Input should be 'INFORMATION_QUERY', 'TASK_EXECUTION', 'COMPOSITE_TASK', 'KNOWLEDGE_QA', 'CHITCHAT' or 'HUMAN_ESCALATION'：1 次。

建议修复优先级：先处理路由的否定/复合意图，再统一澄清节点契约和任务类型校验，随后补充条件表达与缺失工具，最后优化图依赖。此次测试没有修改生产实现，也没有按答案选择性重跑。

## 三次重复稳定性

所有重复均通过的用例：54/100。
所有重复路由均正确的用例：71/100。

## 盲测与审计

- 输入与答案分别存储；推理进程禁止读取答案目录与数据集生成器。
- 模型只接收原始问题、业务上下文、生产系统提示词和生产工具 Schema，不接收答案、类别、标签、评分规则或用例 ID。
- 全部推理完成后生成输出指纹，评分进程随后才读取答案；评分不调用模型。
- 被测生产文件在测试前后指纹一致；没有根据测试答案调整路由或提示词。
- 没有执行业务处理器，仅调用真实 Planner；并行指标评价计划中的独立性，不代表执行器并发。
- 输入 SHA256：`32b618931d387505361957ab49435cb94503cc3f63ce789406151302bf0bdd62`。
- 答案 SHA256：`a7acffed7be4d3d737fa3940cb3c43349c422a9448ee9fad9e8d8d92b6116b4e`。
- 输出 SHA256：`3c95c4356959e92738e0eaf7e6ea63af76f0cd3eb011a41430aa65b173a9ed83`。

## 判定边界

- 通道按实际 fast_route 决策测量。Fast 简单知识描述对象不视作复杂规划；Deep 要有 submit_plan 调用证据。
- 必要依赖按图的可达性判断；允许独立节点交换顺序。明确允许合并的知识目标可共用节点。
- 精确业务实体及已提供参数用代码匹配；政策主题用预先冻结关键词组匹配。没有用另一个模型主观打分。
- 报修、库存、余额等目标在现有注册工具中尚不完整，列入 target_capability，保留失败以表示功能缺口。
- 当前生产计划 Schema 不支持结构化条件；自然语言写到‘如果’不能替代可执行条件。
- 路由 P95 只测 fast_route 函数自身，不含状态库、知识检索或网页回复；不能据此宣称端到端回复达到毫秒级。
- 本结果验证当前版本在该固定集上的表现，不构成独立第三方认证。

## 逐 Case 结果

| Case | 类别 | 问题 | 通过次数 | 主要失败项 |
|---|---|---|---:|---|
| rp_4d959720cb18 | deep_parallel | 帮我查 ORD-A001 订单物流，同时查 ORD-B002 订单发票状态，最后汇总给我。 | 2/3 | inference_error:ValidationError；dag:missing_dag；missing_or_wrong_arguments:a,invoice_status_b；false_or_unverifiable_dependency |
| rp_ecc59114683f | deep_conditional | 先查询设备 DEV-100 的报修记录，报修次数大于三次则通知运维，否则创建普通维修工单。 | 0/3 | inference_error:ValidationError；dag:missing_dag；missing_or_wrong_arguments:records,notify,ticket；required_dependency；missing_or_wrong_structured_condition |
| rp_b444efc91c61 | deep_sequential | 请按先后顺序查询 ORD-A001、ORD-B002 这两笔订单的物流，第一笔查完再查第二笔。 | 3/3 | — |
| rp_224934bcb3cd | deep_sequential | 先查订单 ORD-A001 的退款进度，再查这笔订单的详细状态。 | 3/3 | — |
| rp_2ca7c8434b15 | fast_knowledge | 电子发票的申请规则是什么？ | 3/3 | — |
| rp_41f1fc6d994f | deep_parallel | 查一下订单 ORD-A001 的物流，同时介绍通用退货政策，两项可以独立处理。 | 3/3 | — |
| rp_50e54ecba18a | deep_mixed | 你好，帮我查订单 ORD-A001 的物流并开发票，抬头是星海科技有限公司。 | 3/3 | — |
| rp_3b17cf397dde | deep_sequential | 先查看订单 ORD-A001 的物流，再把该订单的地址改为北京市海淀区中关村南大街1号。 | 3/3 | — |
| rp_843f726e380b | fast_handoff | 转人工客服 | 3/3 | — |
| rp_54cb2fda7ef4 | fast_knowledge | 退换货政策是什么？ | 3/3 | — |
| rp_0219b810abce | deep_conditional | 先查订单 ORD-A001，未发货就把地址改为北京市海淀区中关村南大街1号，已发货则只告诉我改派规则。 | 0/3 | route_mismatch；planner_call_contract；missing_or_wrong_arguments:order,address,policy；required_dependency；missing_or_wrong_structured_condition；unmatched_extra_task |
| rp_4867133483cc | fast_knowledge | 退款规则是什么 | 3/3 | — |
| rp_6c23cefce7b5 | deep_parallel | 订单号已确认是 ORD-A001，请独立查询物流并申请发票，抬头是星海科技有限公司，两件事互不等待。 | 3/3 | — |
| rp_94ddaca36c3f | deep_conditional | 如果订单 ORD-A001 还有效就申请退款，原因是拍错了；如果已经取消，就只解释取消后的退款政策。已核实状态在上下文中。 | 0/3 | route_mismatch；planner_call_contract；missing_or_wrong_arguments:policy；unmatched_extra_task |
| rp_bb51265ede5b | fast_greeting | hi | 3/3 | — |
| rp_b4345c06ba76 | deep_sequential | 先查订单 ORD-A001，再开发票，抬头是星海科技有限公司，最后查询这单物流。 | 0/3 | required_dependency |
| rp_fca33e6caabc | fast_greeting | 再见 | 3/3 | — |
| rp_a92e9089d4fa | fast_greeting | 你好 | 3/3 | — |
| rp_2682108b9a50 | fast_greeting | 辛苦了，回头见 | 0/3 | route_mismatch；planner_call_contract |
| rp_48e65f95d024 | deep_sequential | 先核对订单 ORD-A001 的信息，再帮我催件。 | 3/3 | — |
| rp_ff2ea6af7e47 | deep_sequential | 先查订单 ORD-A001 的支付状态，然后告诉我通用开票规则。 | 0/3 | required_dependency |
| rp_9248ab31bb0b | deep_conditional | 如果订单 ORD-A001 已支付就申请退款，未支付就取消；使用已核实状态，退款原因是拍错了。 | 3/3 | — |
| rp_b741512db88e | deep_sequential | 先为订单 ORD-A001 申请退款，原因是拍错了，提交后再查退款进度。 | 3/3 | — |
| rp_9fc90feb3cb2 | fast_knowledge | 请问七天无理由退货政策是什么 | 3/3 | — |
| rp_216e22c29df8 | fast_handoff | 找客服 | 3/3 | — |
| rp_f3c9a0bcc326 | deep_parallel | 分别查退货政策和开票规则，这两项知识查询互不依赖，最后汇总。 | 0/3 | route_mismatch；planner_call_contract；missing_or_wrong_arguments:returns,invoices；false_or_unverifiable_dependency；unmatched_extra_task |
| rp_73e0294340d0 | deep_parallel | 同时查订单 ORD-A001 和 ORD-B002 的完整物流轨迹，最后汇总。 | 3/3 | — |
| rp_19d200aaad0f | deep_parallel | 给订单 ORD-A001 和 ORD-B002 分别开发票，抬头均为星海科技有限公司，两笔独立申请。 | 3/3 | — |
| rp_c210c3533504 | deep_conditional | 先查订单 ORD-A001，状态是 PAID 才开发票，抬头是星海科技有限公司；未支付则取消订单。 | 0/3 | missing_or_wrong_structured_condition |
| rp_bcabb5021055 | deep_conditional | 先查订单 ORD-A001 的退货资格，允许退货才申请退款，原因是拍错了；不允许就只解释售后政策。 | 0/3 | route_mismatch；planner_call_contract；missing_or_wrong_arguments:order,refund,policy；required_dependency；missing_or_wrong_structured_condition；unmatched_extra_task |
| rp_6b4408ead5b3 | deep_mixed | 不要转人工，先查订单 ORD-A001 物流，再开票，抬头是星海科技有限公司。 | 0/3 | route_mismatch；planner_call_contract；dag:missing_dag；missing_or_wrong_arguments:logistics,invoice；required_dependency；forbidden_action |
| rp_9e979d23627a | deep_mixed | 按照退款规则，先查订单 ORD-A001，再帮我申请退款，原因是拍错了。 | 0/3 | route_mismatch；planner_call_contract；missing_or_wrong_arguments:order,refund；required_dependency；unmatched_extra_task |
| rp_7f3aada1120d | deep_mixed | 给订单 ORD-A001 开票，抬头是星海科技有限公司，另外查一下订单 ORD-B002 物流。 | 3/3 | — |
| rp_e3c6e98a6de1 | deep_parallel | 分别查询订单 ORD-A001 的详情、订单 ORD-B002 的退款进度以及售后政策，三个结果一起给我。 | 0/3 | route_mismatch；planner_call_contract；missing_or_wrong_arguments:order,refund_b,policy；false_or_unverifiable_dependency；unmatched_extra_task |
| rp_6c2c1044c92b | deep_conditional | 先查商品 SKU-100 的库存，有库存就创建一笔订单，没有库存就登记到货提醒。 | 0/3 | inference_error:ValidationError；dag:missing_dag；missing_or_wrong_arguments:stock,buy,remind；required_dependency；missing_or_wrong_structured_condition |
| rp_6950a7022ad4 | fast_handoff | 接个真人来聊吧 | 0/3 | route_mismatch；planner_call_contract |
| rp_19f0873bd569 | deep_sequential | 先查订单 ORD-A001 的状态，然后查询这笔订单的物流。 | 3/3 | — |
| rp_9a00cfc2b411 | fast_knowledge | 周末客服也上班吗？ | 0/3 | route_mismatch；planner_call_contract |
| rp_4ff59ba759fc | fast_greeting | 谢谢 | 3/3 | — |
| rp_fc34021231ab | deep_sequential | 先查询订单 ORD-A001，然后开票，发票抬头是星海科技有限公司。 | 3/3 | — |
| rp_06c9c493ee64 | fast_knowledge | 发票可以开公司抬头吗？ | 0/3 | route_mismatch；planner_call_contract |
| rp_87854eb42eda | deep_mixed | 查下我昨天买的服务器订单物流，顺便开专票，如果不想要了政策是怎样 | 0/3 | inference_error:ValidationError；dag:missing_dag；missing_or_wrong_arguments:logistics,invoice,policy |
| rp_f3ea55ef81d9 | deep_parallel | 订单 ORD-A001 的物流、订单 ORD-B002 的退款进度和通用退货政策，三件事分别查询后汇总。 | 0/3 | route_mismatch；planner_call_contract；missing_or_wrong_arguments:logistics,refund_b,policy；false_or_unverifiable_dependency；unmatched_extra_task |
| rp_d4411355b4db | fast_knowledge | 服务器的保修期通常是多久？ | 0/3 | route_mismatch；planner_call_contract |
| rp_8cef2ad9ea89 | fast_knowledge | 请介绍一下售后服务政策 | 3/3 | — |
| rp_02f71b3cc056 | deep_sequential | 先查订单 ORD-A001，查完以后再查订单 ORD-B002。 | 3/3 | — |
| rp_9d98271d137e | fast_handoff | 我要找真人客服 | 3/3 | — |
| rp_84aca05e3f8b | fast_knowledge | 会员积分有效期有多久？ | 0/3 | route_mismatch；planner_call_contract |
| rp_3fb501022db3 | deep_sequential | 先查订单 ORD-A001 的退款进度，完成后再查订单 ORD-B002 的物流。 | 3/3 | — |
| rp_72203a7e57ed | deep_parallel | 同时查询 ORD-A001 和 ORD-B002 的退款审核进度。 | 3/3 | — |
| rp_fca01244e52a | fast_greeting | 早上好，请问在吗？ | 0/3 | route_mismatch；planner_call_contract |
| rp_f6e3d681dbfd | fast_knowledge | 不是要开票，我只问开票规则 | 3/3 | — |
| rp_f58cee566845 | deep_mixed | 帮我查询这个设备的报修记录，生成工单，同时通知运维，还要告诉我保修到期时间 | 0/3 | inference_error:ValidationError；dag:missing_dag；missing_or_wrong_arguments:records,ticket,notify,warranty；required_dependency；false_or_unverifiable_dependency |
| rp_edfd3c62af76 | fast_knowledge | 配送规则是什么 | 3/3 | — |
| rp_a7b9a11a2166 | fast_knowledge | 促销优惠的使用规则是什么 | 3/3 | — |
| rp_595f708ecdb2 | deep_conditional | 如果 SKU-100 有库存就下单，没有就登记提醒；使用刚才已经核实的库存结果。 | 0/3 | inference_error:ValidationError；dag:missing_dag；missing_or_wrong_arguments:buy |
| rp_036f92dc179e | deep_mixed | 先查余额，申请退款，再查看退款到账周期 | 0/3 | inference_error:ValidationError；dag:missing_dag；missing_or_wrong_arguments:balance,refund,policy；required_dependency |
| rp_761dd15fee3e | deep_sequential | 先查订单 ORD-A001 的状态，再开具发票，抬头是星海科技有限公司，之后解释开票政策。 | 0/3 | route_mismatch；planner_call_contract；missing_or_wrong_arguments:order,invoice,policy；required_dependency；unmatched_extra_task |
| rp_f5b650908342 | deep_conditional | 先查我的可退余额，余额不少于100元就对订单 ORD-A001 申请100元退款，原因是拍错了，否则转人工核实。 | 0/3 | route_mismatch；planner_call_contract；dag:missing_dag；missing_or_wrong_arguments:balance,refund,handoff；required_dependency；missing_or_wrong_structured_condition |
| rp_9da3f4de883e | fast_handoff | 不要自动办理业务，帮我转人工 | 3/3 | — |
| rp_d8542119ab1f | deep_parallel | 分别查询订单 ORD-A001 的详细状态与订单 ORD-B002 的物流，互不依赖。 | 3/3 | — |
| rp_389a7be52de5 | deep_sequential | 先查询订单 ORD-A001 的物流，再帮我催一下这笔订单的快递。 | 3/3 | — |
| rp_759af93196fc | fast_handoff | 请帮我接一位人工客服 | 3/3 | — |
| rp_eb50ad3275c1 | deep_mixed | 先查订单 ORD-A001 的状态，再把查询结果交给人工客服。 | 0/3 | route_mismatch；planner_call_contract；dag:missing_dag；missing_or_wrong_arguments:order,handoff；required_dependency |
| rp_efa7fe9160a3 | deep_sequential | 先查订单 ORD-A001，校验订单是否允许退货，再申请退货，原因是拍错了，最后告知退货时效。 | 0/3 | missing_or_wrong_structured_condition |
| rp_435ad0919cb2 | deep_parallel | 并行查订单 ORD-A001、ORD-B002、ORD-C003 的物流，最后汇总三单结果。 | 3/3 | — |
| rp_be44ffd3fedc | fast_handoff | 请呼叫人工 | 3/3 | — |
| rp_cbfef317b970 | fast_knowledge | 退款一般几天到账？ | 0/3 | route_mismatch；planner_call_contract |
| rp_afd5b28d8b4e | deep_parallel | 同时查订单 ORD-A001 的物流和订单 ORD-B002 的退款进度。 | 3/3 | — |
| rp_6e569cd85bef | deep_sequential | 先查订单 ORD-A001，再把收货地址改为北京市海淀区中关村南大街1号，修改后查询这笔订单物流。 | 3/3 | — |
| rp_9d7410c9b34c | deep_sequential | 先查订单 ORD-A001 的详细信息，再取消这笔未支付订单。 | 3/3 | — |
| rp_d36a6d17171d | fast_knowledge | 你们的质保政策是什么 | 3/3 | — |
| rp_3cbd3b6c2959 | fast_knowledge | 不要给我申请退款，只告诉我退款规则 | 3/3 | — |
| rp_c25e424f0893 | deep_mixed | 查昨天那笔订单的物流，也查一下前天那笔订单的退款进度。 | 3/3 | — |
| rp_0c4c84e0deb6 | fast_handoff | 帮我转人工 | 3/3 | — |
| rp_774c927541fd | deep_sequential | 先查订单 ORD-A001，再查订单 ORD-B002，最后只为 ORD-B002 开发票，抬头是星海科技有限公司。 | 3/3 | — |
| rp_668f369511c4 | fast_knowledge | 你们客服上班时间是几点？ | 0/3 | route_mismatch；planner_call_contract |
| rp_4add05c7f092 | deep_sequential | 先给我查退款规则，再查订单 ORD-A001，然后申请退款，原因是拍错了。 | 0/3 | required_dependency |
| rp_36cfc205acdb | deep_conditional | 查询订单 ORD-A001 的物流；只有物流状态是 SHIPPING 才催件，否则只返回查询结果。 | 0/3 | missing_or_wrong_structured_condition |
| rp_4fb98ea1269f | fast_greeting | 多谢你的帮助 | 0/3 | route_mismatch；planner_call_contract |
| rp_f9e86d2906f0 | fast_knowledge | 配送服务覆盖哪些城市？ | 0/3 | route_mismatch；planner_call_contract |
| rp_ecf3ba785586 | fast_handoff | 让人工专员接手这次咨询 | 0/3 | route_mismatch；planner_call_contract |
| rp_6e6be1bbf865 | deep_conditional | 先查设备 DEV-100 的保修状态，在保则创建免费维修工单，过保则生成收费维修报价。 | 0/3 | inference_error:ValidationError；dag:missing_dag；missing_or_wrong_arguments:warranty,repair,quote；required_dependency；missing_or_wrong_structured_condition |
| rp_129d84273d4c | fast_handoff | 直接转人工，不需要机器人处理 | 3/3 | — |
| rp_b2a03103c7d6 | deep_sequential | 先核对订单 ORD-B002，再为这笔订单申请退款，原因是拍错了。 | 3/3 | — |
| rp_98a3ce6b51de | deep_parallel | 独立为订单 ORD-A001 开发票，抬头是星海科技有限公司，并查询订单 ORD-B002 的物流。 | 3/3 | — |
| rp_597942cabeca | deep_sequential | 先查订单 ORD-A001 的详细信息，再查退款进度，最后告诉我售后人工客服的工作时间。 | 0/3 | route_mismatch；planner_call_contract；dag:missing_dag；missing_or_wrong_arguments:order,refund_status,policy；required_dependency |
| rp_c98cfc4cd776 | fast_knowledge | 开票规则是什么 | 3/3 | — |
| rp_fef0d64d08d1 | deep_mixed | 你好，不要开票，帮我查订单 ORD-A001 的物流和退款政策。 | 0/3 | route_mismatch；planner_call_contract；missing_or_wrong_arguments:logistics,policy；unmatched_extra_task |
| rp_98d1f244ce9b | deep_conditional | 先查订单 ORD-A001，如果状态是 PAID 就申请退款，原因是拍错了，否则只说明退款规则。 | 0/3 | route_mismatch；planner_call_contract；missing_or_wrong_arguments:order,refund,policy；required_dependency；missing_or_wrong_structured_condition；unmatched_extra_task |
| rp_af8949d21e30 | fast_knowledge | 账户注销规则是什么 | 3/3 | — |
| rp_ffdcc2c62d1e | deep_parallel | 独立查询订单 ORD-A001 的退款进度和通用开票规则，最后一起告诉我。 | 0/3 | route_mismatch；planner_call_contract；missing_or_wrong_arguments:refund_status,policy；false_or_unverifiable_dependency；unmatched_extra_task |
| rp_839fa72bfd4a | fast_knowledge | 运费一般由谁承担？ | 0/3 | route_mismatch；planner_call_contract |
| rp_08c3cec79213 | fast_greeting | hello | 3/3 | — |
| rp_0268a63384bb | deep_parallel | 一边查订单 ORD-A001 的详情，一边介绍客服服务时间，分别处理后汇总。 | 3/3 | — |
| rp_7107615b7d58 | fast_greeting | 您好 | 3/3 | — |
| rp_b02237b1584a | fast_greeting | 你好呀！ | 0/3 | route_mismatch；planner_call_contract |
| rp_1486bee11fb3 | deep_conditional | 查订单 ORD-A001，如果未支付就取消，如果已支付就申请退款，原因是拍错了。 | 0/3 | missing_or_wrong_structured_condition |
| rp_90f0342ec917 | deep_conditional | 如果 SKU-100 有库存就下单，否则登记到货提醒；库存已核实，请据此安排。 | 0/3 | dag:missing_dag；missing_or_wrong_arguments:remind |
| rp_1e62b499527e | deep_conditional | 查询订单 ORD-A001 是否已经开票，未开票才申请，抬头是星海科技有限公司，已开票则只展示订单信息。 | 0/3 | missing_or_wrong_structured_condition |
