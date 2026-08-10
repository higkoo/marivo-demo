# 仓库指南

这是一个基于 Marivo 语义层的分析项目，数据源为 2025 年 NYC TLC 黄色出租车数据集。

- 分析前先运行 `make setup`。它会安装 Marivo、下载固定的 2025 年数据集、
  构建 DuckDB 仓库并校验语义层。
- 禁止直接使用 `python`、`pip`、`pytest`、`mypy` 或 `ruff`。请使用 Make
  目标或 `.venv/bin/...`。
- 从 `models/` 下的受治理对象开始分析；不要用临时 SQL 替换语义指标。
- 使用 `import marivo.semantic as ms` 获取精确引用，
  `import marivo.analysis as mv` 进行分析。
- 优先使用渐进式产物读取路径：
  `repr -> show() -> contract() -> to_pandas()`。
- 将 TLC 时间戳视为本地 `America/New_York` 挂钟时间。
- 将政策和天气等解释仅当作观察性说明。Marivo 不会从前后对比或相关性中
  得出因果结论。
- 原始 SQL 仅作为诊断逃生舱。如使用，需在报告前将结果与语义指标对齐。
- 分析过程中不要修改、删除或静默过滤原始数据文件。
- 将本地分析脚本放在 `analysis/` 目录下，并将生成的会话状态
  存放在 `.marivo/` 下，不要提交到 Git。
