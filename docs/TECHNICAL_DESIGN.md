# RAG 系统技术方案

## 背景与目标
- 提供轻量级文档检索增强问答能力（RAG），支持 PDF/DOCX/Markdown/TXT 文档管理、索引构建与问答。
- 追求工程可维护性、稳定性与较好的可观测性，适合本地快速试用与容器化部署。

## 总体架构
- 前端：`web/` 目录下的静态页面（`index.html`、`app.js`、`style.css`），通过浏览器直接访问，UI 提供“管理与索引”和“问答”两个标签页。
- 反向代理：`nginx` 容器提供静态文件与反向代理能力，统一入口：
  - 静态资源：`/web/` （`alias /usr/share/nginx/html/`）
  - API 代理：`/api/*` 与核心路径 `/(documents|index|query)` 代理到后端 `backend:8000`
- 后端：`FastAPI` 服务（`src/presentation` 路由层 + `src/application` 应用服务 + `src/infrastructure` 技术实现）。
- 数据与索引：
  - 文档持久化目录：容器 `/app/data` 映射宿主机 `/data`
  - 向量索引：默认 `FAISS`（位于 `/app/data/vector_index`）
  - 嵌入模型：`sentence-transformers`（可配置）

## 关键流程

### 1) 文档管理
- 上传：`POST /documents`（`multipart/form-data`），写入存储并记录元数据；支持可选字段 `doc_type`/`source_path`/`metadata`。
- 列表：`GET /documents`，返回已上传文档列表与元信息。
- 删除：`DELETE /documents/{doc_id}`，按 `id` 删除对应文件与记录。

### 2) 索引构建
- 入口：`POST /index/init`
- 流程：
  - 加载文档：优先内置解析器（PDF/DOCX/Markdown/TXT），失败时回退到第三方解析器；每个文件的加载在独立线程中执行，并设置 `600s` 超时，避免阻塞主事件循环。
  - 分割：根据文档类型采用合适的分割器生成 `chunks`。
  - 嵌入：使用配置的嵌入提供商为 `chunks` 生成向量。
  - 存储：向量写入向量库（默认 FAISS），并返回处理统计信息（文档计数、块数量、耗时等）。
  - 观测：在内存中记录上下文与每次用户查询问题与返回答案的映射。

### 3) 问答接口
- 入口：`POST /query`
- 流程：
  - 解析输入：`question`、可选 `user_profile`/`session_id`/`top_k`。
  - 检索：对 `question` 进行向量化检索，返回 `top_k` 相关文档片段与得分。
  - 生成：结合检索结果形成答案（及可选结构化响应），返回 `answer`、`sources`、`processing_time`、`timestamp` 等。

## 关键技术决策
- 解析器优先级：
  - 内置解析器优先（PDF/DOCX/Markdown/TXT），保障稳定与可控；失败时回退到第三方库（如 `langchain` 相关 Loader）。
- 代理层：
  - `nginx` 统一前端与后端入口；`/web/` 为静态入口，`/api/*` 与核心路径直通后端。
- 数据持久化：
  - 容器内 `/app/data` 挂载到宿主机 `/data`，文档与向量索引均持久化，便于重启与迁移。

## 接口设计摘要
- 文档：
  - `GET /documents` 列表
  - `POST /documents` 上传（`multipart/form-data`）
  - `DELETE /documents/{doc_id}` 删除
- 索引：
  - `POST /index/init` 初始化索引
- 问答：
  - `POST /query` 提问并返回答案与来源
- 通过 `nginx` 访问统一加前缀：`/api`（如 `GET /api/documents`）。

## 部署方案（容器）
- 组件：`backend` + `nginx`
- 构建：
  - `docker compose -f docker/docker-compose.yml build`
- 启动：
  - `docker compose -f docker/docker-compose.yml up -d`
- 访问：
  - 前端：`http://localhost/web/`
  - 后端 API：`http://localhost:8000/`（或经代理 `http://localhost/api`）
- 数据目录：宿主机 `/data` 映射容器 `/app/data`。

## 安全与合规
- 上传大小限制：`client_max_body_size 20m`（`nginx.conf`）。
- 文件类型与路径校验：限制可解析类型，避免目录穿越。
- 日志中不记录敏感内容；如需审计可在后端增加掩码与采样。

## 扩展规划
- 检索增强：多索引、混合检索、二阶段 rerank。
- 生成增强：结构化响应、可视化来源片段、流式输出。
- 观测与监控：指标上报、慢查询分析、告警通知。
- 多租户与隔离：按 `session_id` 或工作空间区分数据与索引。