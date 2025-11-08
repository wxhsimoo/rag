# API 接口文档

## 概述

婴幼儿营养RAG系统提供RESTful API接口，支持营养咨询、食物推荐、系统管理等功能。

**基础信息：**
- 基础URL: `http://localhost:8000`
- 内容类型: `application/json`
- 字符编码: `UTF-8`

## 认证

当前版本暂不需要认证，后续版本可能会添加API密钥认证。

## 通用响应格式

### 成功响应
```json
{
  "status": "success",
  "data": {...},
  "message": "操作成功"
}
```

### 错误响应
```json
{
  "status": "error",
  "error": {
    "code": "ERROR_CODE",
    "message": "错误描述",
    "details": {...}
  }
}
```

## RAG查询接口

### 1. 营养咨询查询

**接口地址：** `POST /rag/query`

**功能描述：** 基于用户问题和档案，提供个性化的营养咨询回答。

**请求参数：**
```json
{
  "query": "6个月宝宝可以吃什么辅食？",
  "user_profile": {
    "age_months": 6,
    "weight_kg": 7.5,
    "height_cm": 65,
    "allergies": ["鸡蛋", "牛奶"],
    "dietary_preferences": ["有机食品"],
    "health_conditions": [],
    "feeding_history": ["母乳喂养"]
  },
  "conversation_id": "uuid-string",
  "include_sources": true
}
```

**参数说明：**
- `query` (string, 必需): 用户咨询问题
- `user_profile` (object, 可选): 用户档案信息
  - `age_months` (integer): 宝宝月龄
  - `weight_kg` (float): 体重(公斤)
  - `height_cm` (float): 身高(厘米)
  - `allergies` (array): 过敏原列表
  - `dietary_preferences` (array): 饮食偏好
  - `health_conditions` (array): 健康状况
  - `feeding_history` (array): 喂养历史
- `conversation_id` (string, 可选): 对话会话ID
- `include_sources` (boolean, 可选): 是否包含信息来源

**响应示例：**
```json
{
  "answer": "6个月的宝宝可以开始添加辅食了。建议首先添加强化铁米粉...",
  "sources": [
    {
      "content": "6个月是添加辅食的最佳时机...",
      "source": "营养基础知识.md",
      "relevance_score": 0.95
    }
  ],
  "conversation_id": "uuid-string",
  "confidence_score": 0.92,
  "safety_warnings": [
    "请注意观察过敏反应"
  ]
}
```

### 2. 获取对话历史

**接口地址：** `GET /rag/conversation/history`

**功能描述：** 获取指定会话的对话历史记录。

**请求参数：**
- `conversation_id` (query, string): 对话会话ID
- `limit` (query, integer, 可选): 返回记录数量限制，默认20

**响应示例：**
```json
{
  "conversation_id": "uuid-string",
  "messages": [
    {
      "timestamp": "2024-01-15T10:30:00Z",
      "type": "user",
      "content": "6个月宝宝可以吃什么？"
    },
    {
      "timestamp": "2024-01-15T10:30:05Z",
      "type": "assistant",
      "content": "6个月的宝宝可以开始添加辅食..."
    }
  ],
  "total_messages": 10
}
```

### 3. 清除对话历史

**接口地址：** `DELETE /rag/conversation/{conversation_id}`

**功能描述：** 清除指定会话的对话历史。

**路径参数：**
- `conversation_id` (string): 对话会话ID

**响应示例：**
```json
{
  "message": "对话历史已清除",
  "conversation_id": "uuid-string"
}
```

### 4. 获取查询示例

**接口地址：** `GET /rag/examples`

**功能描述：** 获取常见查询示例，帮助用户了解系统功能。

**响应示例：**
```json
{
  "examples": [
    {
      "category": "辅食添加",
      "questions": [
        "6个月宝宝第一次添加辅食应该选择什么？",
        "如何判断宝宝是否准备好吃辅食？"
      ]
    },
    {
      "category": "营养需求",
      "questions": [
        "8个月宝宝每天需要多少铁质？",
        "如何预防宝宝缺钙？"
      ]
    }
  ]
}
```

## 食物推荐接口

### 1. 获取食物推荐

**接口地址：** `POST /food/recommend`

**功能描述：** 根据用户档案和需求，推荐合适的食物。

**请求参数：**
```json
{
  "user_profile": {
    "age_months": 8,
    "weight_kg": 8.2,
    "allergies": ["鸡蛋"],
    "dietary_preferences": ["有机食品"]
  },
  "meal_type": "午餐",
  "nutrition_focus": ["铁质", "蛋白质"],
  "exclude_foods": ["蛋黄"],
  "max_recommendations": 5
}
```

**参数说明：**
- `user_profile` (object, 必需): 用户档案
- `meal_type` (string, 可选): 餐次类型 (早餐/午餐/晚餐/加餐)
- `nutrition_focus` (array, 可选): 营养重点关注
- `exclude_foods` (array, 可选): 排除的食物
- `max_recommendations` (integer, 可选): 最大推荐数量

**响应示例：**
```json
{
  "recommendations": [
    {
      "food_name": "强化铁米粉",
      "description": "专为婴幼儿设计的强化铁米粉",
      "age_range": "6-12个月",
      "nutrition_labels": ["高铁", "易消化"],
      "meal_types": ["早餐", "午餐"],
      "ingredients": ["大米", "铁", "维生素B1"],
      "preparation": "用温水或奶调成糊状",
      "serving_size": "15-30g",
      "texture": "细腻糊状",
      "allergens": [],
      "safety_notes": ["确保水温适宜"],
      "storage_tips": ["密封保存", "避免潮湿"],
      "nutrition_info": {
        "calories_per_100g": 380,
        "protein_g": 8.5,
        "iron_mg": 25
      },
      "recommendation_score": 0.95,
      "safety_score": 1.0,
      "relevance_score": 0.92,
      "rule_warnings": []
    }
  ],
  "total_found": 15,
  "search_criteria": {
    "age_months": 8,
    "meal_type": "午餐",
    "nutrition_focus": ["铁质", "蛋白质"]
  }
}
```

### 2. 获取食物详情

**接口地址：** `POST /food/detail`

**功能描述：** 获取特定食物的详细信息和安全评估。

**请求参数：**
```json
{
  "food_name": "三文鱼泥",
  "user_profile": {
    "age_months": 7,
    "allergies": []
  }
}
```

**响应示例：**
```json
{
  "food_details": {
    "name": "三文鱼泥",
    "description": "富含DHA的三文鱼泥，促进大脑发育",
    "age_range": "7-18个月",
    "nutrition_info": {
      "calories_per_100g": 208,
      "protein_g": 25.4,
      "dha_mg": 1800
    },
    "preparation_detailed": "详细制作步骤...",
    "storage_detailed": "详细储存方法..."
  },
  "safety_assessment": {
    "age_appropriate": true,
    "allergy_safe": true,
    "safety_score": 0.95,
    "warnings": [],
    "recommendations": ["首次添加时少量尝试"]
  }
}
```

### 3. 获取食物分类

**接口地址：** `GET /food/categories`

**功能描述：** 获取系统中的食物分类信息。

**响应示例：**
```json
{
  "categories": [
    {
      "name": "谷物类",
      "description": "米粉、粥类等主食",
      "age_range": "6个月+",
      "examples": ["强化铁米粉", "小米粥"]
    },
    {
      "name": "蛋白质类",
      "description": "肉类、鱼类、蛋类",
      "age_range": "7个月+",
      "examples": ["鸡肉泥", "三文鱼泥"]
    }
  ]
}
```

### 4. 获取营养指南

**接口地址：** `GET /food/nutrition-guide`

**功能描述：** 获取不同年龄段的营养需求指南。

**请求参数：**
- `age_months` (query, integer, 可选): 特定月龄

**响应示例：**
```json
{
  "age_groups": [
    {
      "age_range": "6-8个月",
      "daily_requirements": {
        "calories": "600-700kcal",
        "protein": "11g",
        "iron": "11mg",
        "calcium": "270mg"
      },
      "key_nutrients": ["铁质", "维生素D"],
      "recommended_foods": ["强化铁米粉", "肉泥"],
      "feeding_frequency": "2-3次辅食 + 母乳/配方奶"
    }
  ]
}
```

## 系统管理接口

### 1. 健康检查

**接口地址：** `GET /system/health`

**功能描述：** 检查系统各组件的健康状态。

**响应示例：**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T10:30:00Z",
  "version": "1.0.0",
  "services": {
    "embedding_service": {
      "status": "healthy",
      "response_time_ms": 45
    },
    "vector_store": {
      "status": "healthy",
      "index_size": 1500
    },
    "llm_service": {
      "status": "healthy",
      "model": "gpt-3.5-turbo"
    }
  },
  "system_stats": {
    "memory_usage_mb": 512,
    "cpu_usage_percent": 25,
    "disk_usage_percent": 45
  }
}
```

### 2. 构建索引

**接口地址：** `POST /system/index/build`

**功能描述：** 重新构建向量索引。

**请求参数：**
```json
{
  "source_paths": ["./data/knowledge", "./data/foods"],
  "force_rebuild": false
}
```

**响应示例：**
```json
{
  "status": "success",
  "message": "索引构建完成",
  "stats": {
    "documents_processed": 25,
    "chunks_created": 150,
    "build_time_seconds": 30
  }
}
```

### 3. 获取索引统计

**接口地址：** `GET /system/index/stats`

**功能描述：** 获取向量索引的统计信息。

**响应示例：**
```json
{
  "total_documents": 25,
  "total_chunks": 150,
  "index_size_mb": 12.5,
  "last_updated": "2024-01-15T09:00:00Z",
  "categories": {
    "knowledge": 15,
    "foods": 10
  }
}
```

### 4. 添加文档

**接口地址：** `POST /system/documents/add`

**功能描述：** 向系统添加新文档。

**请求参数：**
```json
{
  "file_path": "./data/knowledge/new_document.md",
  "category": "knowledge",
  "metadata": {
    "author": "营养师",
    "version": "1.0"
  }
}
```

### 5. 删除文档

**接口地址：** `DELETE /system/documents/{document_id}`

**功能描述：** 从系统中删除指定文档。

### 6. 重置缓存

**接口地址：** `POST /system/cache/reset`

**功能描述：** 清空系统缓存。

**请求参数：**
```json
{
  "cache_types": ["embedding", "query"]
}
```

### 7. 获取系统配置

**接口地址：** `GET /system/config`

**功能描述：** 获取系统配置信息（敏感信息已脱敏）。

## 错误码说明

| 错误码 | HTTP状态码 | 描述 |
|--------|------------|------|
| INVALID_REQUEST | 400 | 请求参数无效 |
| UNAUTHORIZED | 401 | 未授权访问 |
| FORBIDDEN | 403 | 禁止访问 |
| NOT_FOUND | 404 | 资源不存在 |
| RATE_LIMITED | 429 | 请求频率超限 |
| INTERNAL_ERROR | 500 | 内部服务器错误 |
| SERVICE_UNAVAILABLE | 503 | 服务不可用 |
| AI_SERVICE_ERROR | 502 | AI服务错误 |
| VALIDATION_ERROR | 422 | 数据验证错误 |

## 使用示例

### Python 示例

```python
import requests
import json

# 基础配置
BASE_URL = "http://localhost:8000"
headers = {"Content-Type": "application/json"}

# 营养咨询示例
def ask_nutrition_question(question, age_months):
    url = f"{BASE_URL}/rag/query"
    data = {
        "query": question,
        "user_profile": {
            "age_months": age_months
        }
    }
    
    response = requests.post(url, json=data, headers=headers)
    return response.json()

# 食物推荐示例
def get_food_recommendations(age_months, meal_type="午餐"):
    url = f"{BASE_URL}/food/recommend"
    data = {
        "user_profile": {
            "age_months": age_months
        },
        "meal_type": meal_type,
        "max_recommendations": 5
    }
    
    response = requests.post(url, json=data, headers=headers)
    return response.json()

# 使用示例
if __name__ == "__main__":
    # 咨询问题
    result = ask_nutrition_question("8个月宝宝可以吃鸡蛋吗？", 8)
    print("咨询回答:", result["answer"])
    
    # 获取推荐
    recommendations = get_food_recommendations(8, "午餐")
    print("推荐食物:", [r["food_name"] for r in recommendations["recommendations"]])
```

### JavaScript 示例

```javascript
const BASE_URL = 'http://localhost:8000';

// 营养咨询
async function askNutritionQuestion(question, ageMonths) {
  const response = await fetch(`${BASE_URL}/rag/query`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      query: question,
      user_profile: {
        age_months: ageMonths
      }
    })
  });
  
  return await response.json();
}

// 食物推荐
async function getFoodRecommendations(ageMonths, mealType = '午餐') {
  const response = await fetch(`${BASE_URL}/food/recommend`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      user_profile: {
        age_months: ageMonths
      },
      meal_type: mealType,
      max_recommendations: 5
    })
  });
  
  return await response.json();
}

// 使用示例
(async () => {
  try {
    const answer = await askNutritionQuestion('6个月宝宝第一次吃什么辅食好？', 6);
    console.log('咨询回答:', answer.answer);
    
    const recommendations = await getFoodRecommendations(6, '午餐');
    console.log('推荐食物:', recommendations.recommendations.map(r => r.food_name));
  } catch (error) {
    console.error('请求失败:', error);
  }
})();
```

## 最佳实践

1. **错误处理**: 始终检查响应状态码和错误信息
2. **用户档案**: 提供完整的用户档案信息以获得更准确的建议
3. **缓存**: 对于相同的查询，可以在客户端进行适当缓存
4. **批量请求**: 避免短时间内大量请求，注意API限流
5. **安全性**: 不要在客户端暴露敏感的API密钥
6. **版本控制**: 关注API版本更新，及时适配新功能

## 更新日志

### v1.0.0 (2024-01-15)
- 初始版本发布
- 支持基础的RAG查询和食物推荐功能
- 提供系统管理接口

### 计划功能
- 用户认证和授权
- 更丰富的营养分析
- 图片识别功能
- 个性化学习能力