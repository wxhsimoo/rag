#!/usr/bin/env python3
"""
RAG查询测试脚本

通过调用DDDServiceFactory创建RAGPipelineService，完成问答查询的完整流程。
"""

import asyncio
from pathlib import Path
from loguru import logger

# 导入配置管理器
from src.infrastructure.config.config_manager import get_config_manager
# 导入DDD服务工厂
from src.presentation.service_factory import DDDServiceFactory
# 导入用户档案相关类
from src.domain.entities.qa_context import UserProfile


async def main():
    """主函数 - 执行RAG查询测试流程"""
    try:
        logger.info("开始RAG查询测试流程")
        
        # 步骤1：加载配置
        logger.info("步骤1：加载系统配置")
        config_manager = get_config_manager("config.yaml")
        config = config_manager.get_config()
        
        # 验证配置
        if not config_manager.validate_config():
            logger.error("配置验证失败，退出程序")
            return
            
        logger.info(f"配置加载成功 - 嵌入服务提供商: {config.ai_providers.embedding.provider}")
        logger.info(f"LLM服务提供商: {config.ai_providers.llm.provider}")
        logger.info(f"向量存储类型: {config.storage.vector_store.type}")
        
        # 步骤2：初始化服务工厂和RAG管道服务
        logger.info("步骤2：初始化DDD服务工厂")
        service_factory = DDDServiceFactory(config)
        
        # 通过工厂创建应用层RAG管道服务
        logger.info("创建RAGPipelineService实例")
        rag_pipeline_service = service_factory.create_application_rag_pipeline_service()
        
        # 步骤3：创建测试用户档案
        logger.info("步骤3：创建测试用户档案")
        user_profile = UserProfile(
            user_id="test_user_001",
            baby_age_months=8,  # 8个月宝宝
            baby_name="小宝",
            known_allergens=["鸡蛋", "牛奶"],  # 过敏原
            dietary_preferences=["有机食品", "少盐"],  # 饮食偏好
            feeding_history=["母乳喂养6个月", "已添加米粉"],
            special_needs=["容易过敏"]
        )
        
        logger.info(f"用户档案创建完成 - 宝宝年龄: {user_profile.baby_age_months}个月")
        logger.info(f"过敏原: {', '.join(user_profile.known_allergens)}")
        logger.info(f"饮食偏好: {', '.join(user_profile.dietary_preferences)}")
        
        # 步骤4：执行RAG查询测试
        logger.info("步骤4：开始RAG查询测试")
        
        # 测试问题列表
        test_questions = [
            # "介绍一下深圳"
            "8个月宝宝可以吃什么辅食？",
            # "如何制作适合8个月宝宝的蔬菜泥？",
            # "宝宝对鸡蛋过敏，有什么替代的蛋白质来源？",
            # "8个月宝宝一天的辅食安排应该是怎样的？"
        ]
        
        session_id = "test_session_001"
        
        for i, question in enumerate(test_questions, 1):
            logger.info(f"\n{'='*60}")
            logger.info(f"测试问题 {i}: {question}")
            logger.info(f"{'='*60}")
            
            try:
                # 调用RAG查询
                result = await rag_pipeline_service.query(
                    question=question,
                    user_profile=user_profile,
                    session_id=session_id,
                    top_k=5,
                    include_context=True
                )
                
                # 输出查询结果
                if result['success']:
                    logger.info("查询成功！")
                    logger.info(f"处理时间: {result['processing_time']:.2f} 秒")
                    logger.info(f"相关文档数量: {len(result['sources'])}")
                    
                    print(f"\n问题: {question}")
                    print(f"\n回答:\n{result['answer']}")
                    
                    # 显示结构化响应（如果有）
                    if result.get('structured_response'):
                        print(f"\n结构化响应: {result['structured_response']}")
                    
                    # 显示相关文档来源
                    print(f"\n参考来源:")
                    for j, source in enumerate(result['sources'], 1):
                        print(f"{j}. 相似度: {source['score']:.3f}")
                        print(f"   内容: {source['content']}")
                        if source.get('metadata'):
                            print(f"   元数据: {source['metadata']}")
                        print()
                    
                else:
                    logger.error(f"查询失败: {result.get('error', '未知错误')}")
                    print(f"\n问题: {question}")
                    print(f"错误: {result.get('error', '未知错误')}")
                
            except Exception as e:
                logger.error(f"查询过程中发生错误: {e}")
                print(f"\n问题: {question}")
                print(f"错误: {str(e)}")
            
            # 添加延迟，避免API调用过于频繁
            if i < len(test_questions):
                logger.info("等待2秒后继续下一个查询...")
                await asyncio.sleep(2)
        
        # 步骤5：测试对话历史功能
        logger.info(f"\n{'='*60}")
        logger.info("步骤5：测试对话历史功能")
        logger.info(f"{'='*60}")
        
        try:
            # 获取对话历史
            history = await rag_pipeline_service.get_conversation_history(
                session_id=session_id,
                limit=10
            )
            
            logger.info(f"对话历史记录数量: {len(history)}")
            print(f"\n对话历史:")
            for msg in history:
                print(f"[{msg['timestamp']}] {msg['role']}: {msg['content'][:100]}...")
            
        except Exception as e:
            logger.error(f"获取对话历史失败: {e}")
        
        # 完成统计
        logger.info(f"\n{'='*60}")
        logger.info("RAG查询测试完成！")
        logger.info(f"测试问题数量: {len(test_questions)}")
        logger.info(f"会话ID: {session_id}")
        logger.info(f"用户档案: {user_profile.baby_age_months}个月宝宝")
        logger.info(f"{'='*60}")
        
    except Exception as e:
        logger.error(f"RAG查询测试过程中发生错误: {e}")
        raise


if __name__ == "__main__":
    # 配置日志
    logger.add(
        "logs/rag_query_test.log",
        rotation="10 MB",
        retention="7 days",
        level="INFO",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {name}:{function}:{line} - {message}"
    )
    
    # 运行主程序
    asyncio.run(main())