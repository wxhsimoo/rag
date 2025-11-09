# 文档检索增强问答（RAG）系统

一个支持文档管理、索引构建与问答的轻量级 RAG 系统。后端基于 FastAPI，前端为纯静态页面（通过 Nginx 提供），支持 PDF / DOCX / Markdown / TXT 文档上传与检索，并提供简单的问答界面。

## 🌟 功能概述
- 文档管理：上传、列表、删除
- 索引构建：对已上传文档进行分割、嵌入与存储
- 问答接口：基于向量检索的问答，返回答案与来源
- 轻量前端：内置“管理与索引”和“问答”两个标签页，可直接浏览器访问
- 稳定性优化：后端加载解析采用线程与超时保护，并记录耗时日志

## 🏗️ 目录结构（简）
```
src/
├── application/       # 应用服务（索引、查询）
├── domain/            # 领域模型与接口
├── infrastructure/    # 加载器、嵌入、存储等实现
└── presentation/      # API 路由与入口
web/                   # 前端静态页面（index.html / app.js / style.css）
docker/                # Dockerfile 与 Compose、Nginx 配置
```

## 🚀 快速启动（Docker）

### 前置条件
- 安装 Docker（20+）与 Docker Compose v2
- 端口可用：`80`（前端）与 `8000`（后端 API）
- 宿主机准备目录 `/data`（用于持久化文档与索引）

### 构建镜像
在项目根目录或 `docker/` 目录执行：

```bash
# 在 docker 目录中
cd docker
docker compose build
```

说明：
- 后端镜像名称：`rag-backend:local`
- 构建使用 `docker/Dockerfile.backend`，启用 pip 缓存与阿里云镜像源以加速

### 启动容器
```bash
# 在 docker 目录中
cd docker
docker compose up -d
```

启动后：
- 前端：`http://localhost/web/`
- 后端 API 文档：`http://localhost:8000/docs`
- 数据持久化：容器 `/app/data` 映射到宿主机 `/data`

## 💡 使用提示
- 建议流程：在“管理与索引”页上传文档后点击“初始化索引”，再到“问答”页提问
- 前端会调用 `/documents`、`/index/init`、`/query` 等接口；Nginx 将 `/api/*` 与核心 API 路径代理到后端
- 外部挂载数据时，确保宿主机 `/data` 目录存在且具备读写权限

## 📖 接口文档
参见完整接口说明文档：[`docs/API.md`](./docs/API.md)