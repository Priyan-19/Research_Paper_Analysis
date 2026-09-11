from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.postgres import get_db
from typing import Optional
from app.analysis.citation_recommender import CitationRecommender
from app.analysis.similarity_detector import SimilarityDetector
from app.analysis.trend_analyzer import TrendAnalyzer
from app.schemas.analysis import (
    CitationRecommendRequest,
    CitationRecommendResponse,
    PaperSimilarityRequest,
    PaperSimilarityResponse,
    TrendOverviewResponse,
    ResearchTrendsResponse
)

router = APIRouter(tags=["Research Analytics Engine"])


@router.post(
    "/citations/recommend",
    response_model=CitationRecommendResponse,
    status_code=status.HTTP_200_OK,
    summary="Recommend Citations for Research Text",
    description="Analyzes a target sentence, paragraph, or claim and recommends relevant papers to cite based on vector similarity and Knowledge Graph concept overlap."
)
async def recommend_citations(
    request: CitationRecommendRequest,
    db: AsyncSession = Depends(get_db)
):
    return await CitationRecommender.recommend_citations(
        db=db,
        statement=request.statement,
        top_k=request.top_k,
        exclude_paper_id=request.exclude_paper_id
    )


@router.post(
    "/similarity/check",
    response_model=PaperSimilarityResponse,
    status_code=status.HTTP_200_OK,
    summary="Research Paper Similarity & Duplicate Detection",
    description="Calculates a multi-factor weighted similarity score across vector embeddings, concepts, methods, and datasets between research papers."
)
async def check_paper_similarity(
    request: PaperSimilarityRequest,
    db: AsyncSession = Depends(get_db)
):
    return await SimilarityDetector.check_paper_similarity(
        db=db,
        source_paper_id=request.source_paper_id,
        target_paper_id=request.target_paper_id,
        top_k=request.top_k
    )


@router.get(
    "/trends/overview",
    response_model=TrendOverviewResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Global Research Intelligence Overview",
    description="Retrieves overall research metrics: paper counts, Knowledge Graph node/edge counts, top concepts, and publication year distribution."
)
async def get_trends_overview(
    db: AsyncSession = Depends(get_db)
):
    return await TrendAnalyzer.get_trends_overview(db=db)


@router.get(
    "/trends/timeline",
    response_model=ResearchTrendsResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Research Concept Timelines & Emerging Topics",
    description="Calculates concept frequency growth timelines, emerging topic spikes, and concept co-occurrence matrices."
)
async def get_trends_timeline(
    min_year: Optional[int] = None,
    db: AsyncSession = Depends(get_db)
):
    return await TrendAnalyzer.get_research_trends(db=db, min_year=min_year)


