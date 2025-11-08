# 婴幼儿营养RAG系统

一个基于RAG（检索增强生成）技术的婴幼儿营养咨询和食物推荐系统，为家长提供专业、安全、个性化的婴幼儿营养指导。

## 🌟 主要特性

- **智能营养咨询**: 基于专业营养知识库的问答系统
- **个性化食物推荐**: 根据婴幼儿年龄、过敏史、营养需求推荐合适食物
- **营养规则引擎**: 内置专业营养规则，确保推荐的安全性
- **多模态支持**: 支持文本、图片等多种输入方式
- **实时对话**: 支持上下文相关的连续对话
- **安全保障**: 严格的年龄适宜性和过敏原检查

## 🏗️ 系统架构

本系统采用领域驱动设计（DDD）和清洁架构模式：

```
src/
├── domain/           # 领域层 - 核心业务逻辑
│   ├── entities/     # 实体对象
│   ├── value_objects/ # 值对象
│   └── services/     # 领域服务
├── infrastructure/   # 基础设施层
│   ├── ai/          # AI服务提供商
│   ├── storage/     # 数据存储
│   ├── config/      # 配置管理
│   └── utils/       # 工具类
├── application/      # 应用层 - 业务编排
│   ├── services/    # 应用服务
│   └── container.py # 依赖注入容器
└── presentation/     # 表现层 - API接口
    ├── api/         # REST API路由
    └── main.py      # FastAPI应用入口
```

## 🚀 快速开始

### 环境要求

- Python 3.8+
- 8GB+ RAM（推荐）
- 2GB+ 磁盘空间

### 安装步骤

1. **克隆项目**
```bash
git clone <repository-url>
cd baby-nutrition-rag
```

2. **创建虚拟环境**
```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

3. **安装依赖**
```bash
pip install -r requirements.txt
```

4. **配置系统**
```bash
# 复制配置文件模板
cp config.example.yaml config.yaml

# 编辑配置文件，设置API密钥等
nano config.yaml
```

5. **启动系统**
```bash
# 开发模式启动
python run.py --reload

# 生产模式启动
python run.py --workers 4
```

6. **访问系统**
- API文档: http://localhost:8000/docs
- 健康检查: http://localhost:8000/health
- 系统状态: http://localhost:8000/system/health

## 📖 使用指南

### API接口

#### 1. 营养咨询 (RAG查询)

```bash
curl -X POST "http://localhost:8000/rag/query" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "6个月宝宝可以吃什么辅食？",
    "user_profile": {
      "age_months": 6,
      "allergies": [],
      "dietary_preferences": []
    }
  }'
```

#### 2. 食物推荐

```bash
curl -X POST "http://localhost:8000/food/recommend" \
  -H "Content-Type: application/json" \
  -d '{
    "user_profile": {
      "age_months": 8,
      "allergies": ["鸡蛋"],
      "dietary_preferences": ["有机食品"]
    },
    "meal_type": "午餐",
    "nutrition_focus": ["铁质", "蛋白质"],
    "exclude_foods": []
  }'
```

#### 3. 食物详情

```bash
curl -X POST "http://localhost:8000/food/detail" \
  -H "Content-Type: application/json" \
  -d '{
    "food_name": "强化铁米粉",
    "user_profile": {
      "age_months": 6
    }
  }'
```

### 配置说明

主要配置项说明：

```yaml
# AI服务配置
ai_providers:
  embedding:
    provider: "sentence_transformers"  # 嵌入模型提供商
    model: "all-MiniLM-L6-v2"         # 模型名称
  llm:
    provider: "openai"                 # LLM提供商
    model: "gpt-3.5-turbo"            # 模型名称
    api_key: "your-api-key"           # API密钥

# 存储配置
storage:
  documents_path: "./data"            # 文档存储路径
  vector_store:
    type: "faiss"                     # 向量数据库类型
    index_path: "./data/vector_index" # 索引存储路径

# RAG配置
rag:
  retrieval:
    top_k: 5                          # 检索文档数量
    similarity_threshold: 0.7         # 相似度阈值
```

## 🔧 开发指南

### 项目结构详解

- **Domain层**: 包含核心业务实体和规则
  - `Food`: 食物实体
  - `UserProfile`: 用户档案
  - `NutritionRule`: 营养规则

- **Infrastructure层**: 提供技术实现
  - `EmbeddingProvider`: 嵌入服务
  - `LLMProvider`: 大语言模型服务
  - `VectorStore`: 向量数据库

- **Application层**: 业务逻辑编排
  - `RAGPipelineService`: RAG管道服务
  - `FoodRecommendationService`: 食物推荐服务

- **Presentation层**: API接口
  - FastAPI路由和请求/响应模型

### 添加新功能

1. **添加新的营养规则**
```python
# src/domain/services/nutrition_rule_engine.py
def add_custom_rule(self, rule_name: str, rule_func: callable):
    self.rules[rule_name] = rule_func
```

2. **扩展食物数据**
```json
// data/foods/new_foods.json
{
  "name": "新食物",
  "description": "食物描述",
  "age_range": "6-12个月",
  "nutrition_labels": ["高铁", "高蛋白"]
}
```

3. **添加新的API接口**
```python
# src/presentation/api/new_routes.py
@router.post("/new-endpoint")
async def new_endpoint(request: NewRequest):
    # 实现逻辑
    pass
```

### 测试

```bash
# 运行所有测试
pytest

# 运行特定测试
pytest tests/test_food_recommendation.py

# 生成覆盖率报告
pytest --cov=src --cov-report=html
```

### 代码质量

```bash
# 代码格式化
black src/

# 导入排序
isort src/

# 代码检查
flake8 src/

# 类型检查
mypy src/
```

## 📊 监控和运维

### 健康检查

系统提供多层次的健康检查：

```bash
# 基础健康检查
curl http://localhost:8000/health

# 详细系统状态
curl http://localhost:8000/system/health

# 索引统计信息
curl http://localhost:8000/system/index/stats
```

### 日志管理

日志配置在 `config.yaml` 中：

```yaml
monitoring:
  performance:
    enabled: true
    slow_query_threshold_ms: 1000
  health_check:
    enabled: true
    interval_seconds: 60
```

### 性能优化

1. **缓存配置**
```yaml
cache:
  embedding_cache:
    enabled: true
    max_size: 1000
    ttl_seconds: 3600
```

2. **批处理优化**
```yaml
ai_providers:
  embedding:
    batch_size: 32  # 增加批处理大小
```

## 🔒 安全考虑

- **API限流**: 防止滥用
- **输入验证**: 严格的请求参数验证
- **营养安全**: 多层营养规则检查
- **数据隐私**: 不存储个人敏感信息

## 🤝 贡献指南

1. Fork 项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 🆘 支持

如果您遇到问题或有建议，请：

1. 查看 [FAQ](docs/FAQ.md)
2. 搜索现有的 [Issues](../../issues)
3. 创建新的 Issue
4. 联系维护者

## 🙏 致谢

感谢以下开源项目：

- [FastAPI](https://fastapi.tiangolo.com/) - 现代、快速的Web框架
- [Sentence Transformers](https://www.sbert.net/) - 语义嵌入模型
- [FAISS](https://faiss.ai/) - 高效向量搜索
- [LangChain](https://langchain.com/) - LLM应用开发框架

---

**注意**: 本系统提供的营养建议仅供参考，不能替代专业医疗建议。在给婴幼儿添加新食物前，请咨询儿科医生或营养师。