from fastapi import APIRouter
from app.api.v1 import health, papers, search, rag, graph, chat, analysis, evaluation

api_v1_router = APIRouter()

# Include endpoint routers
api_v1_router.include_router(health.router)
api_v1_router.include_router(papers.router)
api_v1_router.include_router(search.router)
api_v1_router.include_router(rag.router)
api_v1_router.include_router(graph.router)
api_v1_router.include_router(chat.router)
api_v1_router.include_router(analysis.router)
api_v1_router.include_router(evaluation.router)







