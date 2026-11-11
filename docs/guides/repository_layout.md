# 目录迁移说明

本次调整文件位置和入口说明，不改变应用业务算法；封存的 v1 数据、预测和被测源码路径不变。

## 保留的入口

- `run.py`、`start.bat`、`一键启动.bat`、`启动客服系统.bat`。
- `scripts/` 下当前使用的 Agent 回归、盲测、评分与失败分析命令。
- `app/`、`tests/` 与 `data/evaluation/route_planner_v1/` 的既有代码/数据路径。

## 已跟踪文件迁移对照

历史脚本按用途归档；需要使用时从项目根目录通过新模块路径运行。补丁/生成器属于历史材料，不作为自动启动或自动测试的一部分。

| 原路径 | 新路径 |
|---|---|
| `Agent模块重构技术方案.md` | `docs/architecture/agent_refactor_plan.md` |
| `knowledge_base_system_spec.md` | `docs/architecture/system_spec.md` |
| `docs/AGENT_REFACTOR.md` | `docs/guides/agent_runtime.md` |
| `docs/BADCASE_CLOSED_LOOP_SOLUTION.md` | `docs/design/BADCASE_CLOSED_LOOP_SOLUTION.md` |
| `docs/BADCASE_OPTIMIZATION_SPEC.md` | `docs/design/BADCASE_OPTIMIZATION_SPEC.md` |
| `docs/RAG_TO_AGENT_CUSTOMER_SERVICE_PLAN.md` | `docs/design/RAG_TO_AGENT_CUSTOMER_SERVICE_PLAN.md` |
| `docs/SAAS_PRODUCT_AND_SUBSCRIPTION_PLAN.md` | `docs/design/SAAS_PRODUCT_AND_SUBSCRIPTION_PLAN.md` |
| `docs/knowledge_source_sync_design.md` | `docs/design/knowledge_source_sync_design.md` |
| `docs/knowledge_source_sync_features.md` | `docs/design/knowledge_source_sync_features.md` |
| `docs/roles_and_permissions_scheme.md` | `docs/design/roles_and_permissions_scheme.md` |
| `scripts/add_ecommerce_tech_agent.py` | `scripts/legacy/patches/add_ecommerce_tech_agent.py` |
| `scripts/build_frontend.py` | `scripts/legacy/patches/build_frontend.py` |
| `scripts/build_full_updated_frontend.py` | `scripts/legacy/patches/build_full_updated_frontend.py` |
| `scripts/cache_all_retrievals.json` | `data/evaluation/rag_cache/cache_all_retrievals.json` |
| `scripts/check_chunk_uniqueness.py` | `scripts/legacy/diagnostics/check_chunk_uniqueness.py` |
| `scripts/check_chunks.py` | `scripts/legacy/diagnostics/check_chunks.py` |
| `scripts/check_db_all.py` | `scripts/legacy/diagnostics/check_db_all.py` |
| `scripts/check_doc_content.py` | `scripts/legacy/diagnostics/check_doc_content.py` |
| `scripts/check_docs_content.py` | `scripts/legacy/diagnostics/check_docs_content.py` |
| `scripts/check_embeddings.py` | `scripts/legacy/diagnostics/check_embeddings.py` |
| `scripts/check_kb_chunks.py` | `scripts/legacy/diagnostics/check_kb_chunks.py` |
| `scripts/check_meta.py` | `scripts/legacy/diagnostics/check_meta.py` |
| `scripts/check_sec_matching.py` | `scripts/legacy/diagnostics/check_sec_matching.py` |
| `scripts/check_sections.py` | `scripts/legacy/diagnostics/check_sections.py` |
| `scripts/check_tables.py` | `scripts/legacy/diagnostics/check_tables.py` |
| `scripts/compare_content.py` | `scripts/legacy/diagnostics/compare_content.py` |
| `scripts/create_badcase_tables.py` | `scripts/legacy/maintenance/create_badcase_tables.py` |
| `scripts/debug_facts_coverage.py` | `scripts/legacy/diagnostics/debug_facts_coverage.py` |
| `scripts/eval_gt_coverage.py` | `scripts/legacy/rag/eval_gt_coverage.py` |
| `scripts/eval_strategies_summary.py` | `scripts/legacy/rag/eval_strategies_summary.py` |
| `scripts/find_gaokong.py` | `scripts/legacy/diagnostics/find_gaokong.py` |
| `scripts/find_hard_misses.py` | `scripts/legacy/diagnostics/find_hard_misses.py` |
| `scripts/fix_frontend_structure.py` | `scripts/legacy/patches/fix_frontend_structure.py` |
| `scripts/fix_syntax.py` | `scripts/legacy/patches/fix_syntax.py` |
| `scripts/generate_eval_report.py` | `scripts/legacy/rag/generate_eval_report.py` |
| `scripts/generate_evaluation_results.py` | `scripts/legacy/rag/generate_evaluation_results.py` |
| `scripts/init_kbs_and_seed_badcases.py` | `scripts/legacy/maintenance/init_kbs_and_seed_badcases.py` |
| `scripts/inspect_all_facts.py` | `scripts/legacy/diagnostics/inspect_all_facts.py` |
| `scripts/inspect_chunk_sample.py` | `scripts/legacy/diagnostics/inspect_chunk_sample.py` |
| `scripts/inspect_cluster.py` | `scripts/legacy/diagnostics/inspect_cluster.py` |
| `scripts/inspect_dataset_facts.py` | `scripts/legacy/diagnostics/inspect_dataset_facts.py` |
| `scripts/inspect_diffs.py` | `scripts/legacy/diagnostics/inspect_diffs.py` |
| `scripts/inspect_doc05.py` | `scripts/legacy/diagnostics/inspect_doc05.py` |
| `scripts/inspect_eval.py` | `scripts/legacy/diagnostics/inspect_eval.py` |
| `scripts/inspect_misses.py` | `scripts/legacy/diagnostics/inspect_misses.py` |
| `scripts/merge_full_frontend.py` | `scripts/legacy/patches/merge_full_frontend.py` |
| `scripts/patch_backend_badcase.py` | `scripts/legacy/patches/patch_backend_badcase.py` |
| `scripts/patch_documents_api.py` | `scripts/legacy/patches/patch_documents_api.py` |
| `scripts/patch_frontend.py` | `scripts/legacy/patches/patch_frontend.py` |
| `scripts/patch_frontend_comprehensive.py` | `scripts/legacy/patches/patch_frontend_comprehensive.py` |
| `scripts/patch_modal_items.py` | `scripts/legacy/patches/patch_modal_items.py` |
| `scripts/patch_retrieval_results.py` | `scripts/legacy/rag/patch_retrieval_results.py` |
| `scripts/reindex_all_md.py` | `scripts/legacy/maintenance/reindex_all_md.py` |
| `scripts/repair_clusters_data.py` | `scripts/legacy/maintenance/repair_clusters_data.py` |
| `scripts/run_collect_retrievals.py` | `scripts/legacy/rag/run_collect_retrievals.py` |
| `scripts/search_target.py` | `scripts/legacy/diagnostics/search_target.py` |
| `scripts/test_4_fixes_verification.py` | `scripts/legacy/diagnostics/test_4_fixes_verification.py` |
| `scripts/test_badcase_cluster.py` | `scripts/legacy/diagnostics/test_badcase_cluster.py` |
| `scripts/test_badcase_validate.py` | `scripts/legacy/diagnostics/test_badcase_validate.py` |
| `scripts/test_coverage_func.py` | `scripts/legacy/diagnostics/test_coverage_func.py` |
| `scripts/test_doc_api.py` | `scripts/legacy/diagnostics/test_doc_api.py` |
| `scripts/test_fact_extractor.py` | `scripts/legacy/diagnostics/test_fact_extractor.py` |
| `scripts/test_generation_all.py` | `scripts/legacy/diagnostics/test_generation_all.py` |
| `scripts/test_jieba_coverage.py` | `scripts/legacy/diagnostics/test_jieba_coverage.py` |
| `scripts/test_match_logic.py` | `scripts/legacy/diagnostics/test_match_logic.py` |
| `scripts/test_md_chunking.py` | `scripts/legacy/diagnostics/test_md_chunking.py` |
| `scripts/test_model_apis.py` | `scripts/legacy/diagnostics/test_model_apis.py` |
| `scripts/test_permission_rules.py` | `scripts/legacy/diagnostics/test_permission_rules.py` |
| `scripts/test_retrieval_all.py` | `scripts/legacy/diagnostics/test_retrieval_all.py` |
| `scripts/test_search.py` | `scripts/legacy/diagnostics/test_search.py` |
| `scripts/test_single_gen.py` | `scripts/legacy/diagnostics/test_single_gen.py` |
| `scripts/test_single_retrieve.py` | `scripts/legacy/diagnostics/test_single_retrieve.py` |
| `scripts/update_adopt_modal.py` | `scripts/legacy/patches/update_adopt_modal.py` |
| `scripts/update_permissions.py` | `scripts/legacy/patches/update_permissions.py` |
| `scripts/verify_badcase_system.py` | `scripts/legacy/diagnostics/verify_badcase_system.py` |
| `scripts/verify_badcase_v2.py` | `scripts/legacy/diagnostics/verify_badcase_v2.py` |
| `scripts/verify_permissions_complete.py` | `scripts/legacy/diagnostics/verify_permissions_complete.py` |
| `scripts/verify_system_fixes.py` | `scripts/legacy/diagnostics/verify_system_fixes.py` |
| `data/evaluation/extract_questions.py` | `scripts/legacy/rag/extract_questions.py` |

## 本地产物

未跟踪的项目文稿、PPT、渲染图片、提取文本、个人展示资料及对应旧生成器归档到 `local_artifacts/`。该目录不会上传 GitHub；本地 `directory-move-manifest.json` 保存原路径、新路径和移动前 SHA256，可用于核对或恢复。

现有 `.env` 和数据库仍在原位置，避免现有本地运行状态因目录调整而失效。

## 兼容边界

历史脚本的文件路径引用和一个内部模块导入已同步更新；部分工具含固定业务 ID 或直接改写源码的逻辑，不保证所有旧操作适用于当前业务数据。旧 `build_frontend.py` 的语法问题原样归档，应用直接读取 `app/static/` 中的前端。
