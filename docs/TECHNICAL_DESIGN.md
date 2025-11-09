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
  - 嵌入模型：可配置

## 关键流程

### 1) 文档管理
- 上传：`POST /documents`（`multipart/form-data`），写入存储并记录元数据；支持可选字段 `doc_type`/`source_path`/`metadata`。
- 列表：`GET /documents`，返回已上传文档列表与元信息。
- 删除：`DELETE /documents/{doc_id}`，按 `id` 删除对应文件与记录。

### 2) 索引构建
- 入口：`POST /index/init`
- 流程：
  - 加载文档：根据文档类型采用合适的加载器。
  - 分割：根据文档类型采用合适的分割器生成 `chunks`。
  - 嵌入：使用配置的嵌入提供商为 `chunks` 生成向量。
  - 存储：向量写入向量库（默认 FAISS），并返回处理统计信息（文档计数、块数量、耗时等）。
  - 观测：在内存中记录上下文与每次用户查询问题与返回答案的映射。

### 3) 问答接口
- 入口：`POST /query`
- 流程：
- 解析输入：`question`、可选 `user_profile`/`session_id`/`top_k`。
- 检索：对 `question` 进行向量化检索，返回 `top_k` 相关文档片段与得分。
 - Prompt 构建：将检索到的片段与用户问题拼装成提示词，遵循以下策略：
   - 系统提示（System Prompt）：限定角色与安全边界
   - 用户提示（User Prompt）：包含原始 `question` 与选取的片段集合，并附带来源标注。
   - 约束与风格：
     - 优先使用中文回答，结构清晰（要点/步骤/建议）。
     - 禁止编造事实；超出上下文时提示“目前无法确定”。
     - 引用来源时使用可解析标记（如 `[source: <doc_id>#<page>|<filename>]`）。
   - 片段选择与拼接：
     - 使用 `top_k`（默认来自请求或配置 `rag.retrieval.top_k`）。
     - 控制总上下文长度（配置 `rag.retrieval.max_context_length`），超过则截断低分片段或做摘要合并。
     - 相同来源的相邻片段合并以减少重复。
   - 输出规范：返回 `answer`（文本），`sources`（已用来源清单），必要时提供结构化补充字段（如关键要点列表）。
  - 生成：结合检索结果形成答案（及可选结构化响应），返回 `answer`、`sources`、`processing_time`、`timestamp` 等。


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

## 扩展规划
- 检索增强：多索引、混合检索、二阶段 rerank。
- 生成增强：结构化响应、可视化来源片段、流式输出。
- 观测与监控：指标上报、慢查询分析、告警通知。
- 多租户与隔离：按 `session_id` 或工作空间区分数据与索引。