"""
领域智能体主入口文件

该文件是领域智能体的主入口，包括：
- FastAPI 应用初始化
- API 路由定义
- 工作流调用逻辑
- 错误处理中间件

领域智能体功能：
- Neo4j 知识图谱检索
- 结构化检索
- 替代推理
- SQE 评价
- 可解释推荐
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import time

from .config import settings
from .schemas.request import QueryRequest, RetrievalRequest, RankingRequest
from .schemas.response import QueryResponse, RetrievalResponse, RankingResponse, ErrorResponse
from .graph.workflow import agent_workflow
from .graph.state import AgentState
from .prompts.router_prompt import ROUTER_SYSTEM_PROMPT, ROUTER_USER_PROMPT_TEMPLATE
from .prompts.answer_prompt import ANSWER_SYSTEM_PROMPT, ANSWER_USER_PROMPT_TEMPLATE
from .services.llm_service import llm_service
from .services.retrieval_service import retrieval_service
from .services.ranking_service import ranking_service


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    应用生命周期管理

    启动时初始化资源，关闭时清理资源
    """
    print("领域智能体启动中...")
    yield
    print("领域智能体关闭中...")
    retrieval_service.close()


# 创建 FastAPI 应用
app = FastAPI(
    title="领域智能体 API",
    description="基于 Neo4j 知识图谱和 SQE 评价的烹饪领域智能体",
    version="1.0.0",
    lifespan=lifespan
)

# 配置 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """
    根路径

    返回 API 基本信息
    """
    return {
        "name": "领域智能体 API",
        "version": "1.0.0",
        "description": "基于 Neo4j 知识图谱和 SQE 评价的烹饪领域智能体"
    }


@app.get("/health")
async def health_check():
    """
    健康检查

    返回服务健康状态
    """
    return {
        "status": "healthy",
        "debug": settings.DEBUG
    }


@app.post("/api/query", response_model=QueryResponse)
async def query(request: QueryRequest):
    """
    查询接口

    处理用户查询，返回智能体的回答和推荐

    Args:
        request: 查询请求

    Returns:
        查询响应
    """
    try:
        start_time = time.time()

        # 初始化状态
        initial_state: AgentState = {
            "query": request.query,
            "context": request.context,
            "retrieved_recipes": [],
            "retrieved_ingredients": [],
            "substitute_candidates": [],
            "substitute_reasoning": "",
            "sqe_scores": [],
            "recommendations": [],
            "explanation": "",
            "current_step": "start",
            "error": None
        }

        # 执行工作流
        result = agent_workflow.invoke(initial_state)

        # 计算处理时间
        processing_time = time.time() - start_time

        # 构建响应
        response = QueryResponse(
            query=request.query,
            answer=result.get("explanation", ""),
            recommendations=result.get("recommendations", []),
            explanation=result.get("explanation"),
            sqe_scores=result.get("sqe_scores"),
            sources=["Neo4j知识图谱", "SQE评价系统"],
            processing_time=processing_time
        )

        return response

    except Exception as e:
        if settings.DEBUG:
            print(f"查询处理失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/retrieve", response_model=RetrievalResponse)
async def retrieve(request: RetrievalRequest):
    """
    检索接口

    从知识图谱和向量数据库检索相关信息

    Args:
        request: 检索请求

    Returns:
        检索响应
    """
    try:
        results = retrieval_service.hybrid_retrieval(
            query=request.query,
            retrieval_type=request.retrieval_type,
            filters=request.filters
        )

        response = RetrievalResponse(
            query=request.query,
            results=results,
            total=len(results),
            retrieval_type=request.retrieval_type
        )

        return response

    except Exception as e:
        if settings.DEBUG:
            print(f"检索失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/rank", response_model=RankingResponse)
async def rank(request: RankingRequest):
    """
    排序接口

    基于 SQE 评价对候选推荐进行排序

    Args:
        request: 排序请求

    Returns:
        排序响应
    """
    try:
        ranked_candidates = ranking_service.rank_candidates(
            candidates=request.candidates,
            user_preferences=request.user_preferences
        )

        # 提取 SQE 分数
        sqe_scores = [
            {
                "candidate": c.get("name", "未知"),
                "taste": c.get("taste_score", 0),
                "texture": c.get("texture_score", 0),
                "nutrition": c.get("nutrition_score", 0),
                "total": c.get("total_score", 0)
            }
            for c in ranked_candidates
        ]

        response = RankingResponse(
            ranked_candidates=ranked_candidates,
            sqe_scores=sqe_scores,
            ranking_criteria=request.criteria
        )

        return response

    except Exception as e:
        if settings.DEBUG:
            print(f"排序失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG
    )
