# RAG 系统 API 文档

本文档描述文档管理（上传、列表、删除）、索引构建与问答接口。

- 后端直连基础地址：`http://localhost:8000`
- 通过 Nginx 访问时需加前缀：`http://localhost/api`（例如 `http://localhost/api/documents`）

## 文档管理

- 列表文档（GET）
  - 路径：`GET /documents`
  - 说明：返回已上传文档列表
  - 响应示例：
    ```json
    [
      {
        "id": "doc_1728793020_001",
        "filename": "example.pdf",
        "metadata": { "size": 123456 }
      }
    ]
    ```
  - curl：
    ```bash
    curl -X GET "http://localhost:8000/documents"
    # 或通过 Nginx：
    curl -X GET "http://localhost/api/documents"
    ```

- 上传文档（POST）
  - 路径：`POST /documents`
  - Content-Type：`multipart/form-data`
  - 表单字段：
    - `file`（必填）：待上传文件
    - `doc_type`（可选）：文档类型提示（如 `pdf`/`docx`/`md`/`txt`）
    - `source_path`（可选）：来源路径或备注
    - `metadata`（可选）：自定义元数据（字符串或 JSON 字符串）
  - 响应示例：
    ```json
    {
      "doc_id": "doc_1728793020_001",
      "filename": "example.pdf"
    }
    ```
  - curl：
    ```bash
    curl -X POST "http://localhost:8000/documents" \
      -F "file=@/path/to/example.pdf" \
      -F "doc_type=pdf" \
      -F "source_path=/import" \
      -F "metadata={\"category\":\"spec\"}"
    # 或通过 Nginx：
    curl -X POST "http://localhost/api/documents" \
      -F "file=@/path/to/example.pdf"
    ```

- 删除文档（DELETE）
  - 路径：`DELETE /documents/{doc_id}`
  - 说明：按文档 `id` 删除
  - 响应示例：
    ```json
    { "success": true }
    ```
  - curl：
    ```bash
    curl -X DELETE "http://localhost:8000/documents/doc_1728793020_001"
    # 或通过 Nginx：
    curl -X DELETE "http://localhost/api/documents/doc_1728793020_001"
    ```

## 索引构建

- 初始化索引（POST）
  - 路径：`POST /index/init`
  - 说明：对当前文档进行分割、嵌入并存储到向量库
  - 请求体：空或 `{}`（无参数）
  - 响应示例（字段可能随实现调整）：
    ```json
    {
      "success": true,
      "processed_documents": 3,
      "generated_chunks": 128,
      "stored_embeddings": 128,
      "processing_time": 2.37
    }
    ```
  - curl：
    ```bash
    curl -X POST "http://localhost:8000/index/init" -H "Content-Type: application/json" -d '{}'
    # 或通过 Nginx：
    curl -X POST "http://localhost/api/index/init" -H "Content-Type: application/json" -d '{}'
    ```

## 问答接口

- 发送问题（POST）
  - 路径：`POST /query`
  - Content-Type：`application/json`
  - 请求体（部分字段可选）：
    ```json
    {
      "question": "这个系统做什么？",
      "user_profile": null,
      "session_id": "session-001",
      "top_k": 5
    }
    ```
  - 响应示例（字段可能随实现调整）：
    ```json
    {
      "success": true,
      "answer": "该系统支持文档管理、索引构建与问答。",
      "sources": [
        {
          "id": "doc_1728793020_001",
          "filename": "example.pdf",
          "score": 0.83,
          "snippet": "系统支持文档上传与检索..."
        }
      ],
      "processing_time": 0.92,
      "timestamp": "2024-10-22T12:34:56Z"
    }
    ```
  - curl：
    ```bash
    curl -X POST "http://localhost:8000/query" \
      -H "Content-Type: application/json" \
      -d '{
        "question": "这个系统做什么？",
        "top_k": 5
      }'
    # 或通过 Nginx：
    curl -X POST "http://localhost/api/query" \
      -H "Content-Type: application/json" \
      -d '{
        "question": "这个系统做什么？",
        "top_k": 5
      }'
    ```

---

提示与约定
- 通过 Nginx 访问需加 `/api` 前缀；直连后端端口无需该前缀。
- 上传支持常见格式：PDF/DOCX/Markdown/TXT；系统会优先使用内置解析器并设置合理超时。
- 响应字段可能因实现演进而略有变化，以实际返回为准。