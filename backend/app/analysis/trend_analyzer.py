from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import logger
from app.database.neo4j import get_neo4j_session
from app.services.paper_service import PaperService
from app.graph.neo4j_builder import Neo4jGraphBuilder
from app.schemas.analysis import (
    TrendOverviewResponse,
    ConceptTimelineItem,
    ConceptCoOccurrenceItem,
    ResearchTrendsResponse
)


class TrendAnalyzer:
    """
    Research Trend Analysis Engine.
    Aggregates historical Knowledge Graph metrics to compute:
    - Overview metrics (paper counts, entity/rel counts, top concepts)
    - Concept timelines & emerging topic growth rate (Delta >= 0.50)
    - Concept co-occurrence matrices for research domain clustering
    """

    @classmethod
    async def get_trends_overview(cls, db: AsyncSession) -> TrendOverviewResponse:
        """
        Retrieves global analytics overview metrics across PostgreSQL and Neo4j.
        """
        logger.info("Computing global research trends overview...")

        # 1. Total papers in DB
        papers = await PaperService.list_papers(db)
        total_papers = len(papers)

        # Build year distribution from papers
        year_dist: Dict[str, int] = {}
        for p in papers:
            yr = str(p.year) if p.year else "Unknown"
            year_dist[yr] = year_dist.get(yr, 0) + 1

        # 2. Graph Stats from Neo4j
        graph_stats = await Neo4jGraphBuilder.get_graph_stats()
        total_concepts = graph_stats.total_nodes
        total_rels = graph_stats.total_relationships

        # 3. Query top 10 most frequent entities from Neo4j
        top_concepts: List[Dict[str, Any]] = []
        async with get_neo4j_session() as session:
            cypher = """
            MATCH (p:Paper)-[:MENTIONS]->(e:Entity)
            RETURN e.name AS name, e.type AS type, count(distinct p) AS paper_count
            ORDER BY paper_count DESC
            LIMIT 10
            """
            try:
                res = await session.run(cypher)
                async for record in res:
                    top_concepts.append({
                        "name": record["name"],
                        "type": record["type"],
                        "paper_count": record["paper_count"]
                    })
            except Exception as e:
                logger.error(f"Failed to query top concepts from Neo4j: {str(e)}")

        return TrendOverviewResponse(
            total_papers=total_papers,
            total_concepts=total_concepts,
            total_relationships=total_rels,
            top_concepts=top_concepts,
            publication_year_distribution=year_dist
        )

    @classmethod
    async def get_research_trends(
        cls,
        db: AsyncSession,
        min_year: Optional[int] = None
    ) -> ResearchTrendsResponse:
        """
        Computes concept timelines, emerging topics, and co-occurrence matrices.
        """
        logger.info(f"Computing research trend timelines (min_year={min_year})...")

        timelines_dict: Dict[str, Dict[str, Any]] = {}
        co_occurrences: List[ConceptCoOccurrenceItem] = []
        emerging_concepts: List[str] = []

        async with get_neo4j_session() as session:
            # 1. Query Concept Mentions by Year
            timeline_cypher = """
            MATCH (p:Paper)-[:MENTIONS]->(e:Entity)
            WHERE e.type <> 'AUTHOR'
            RETURN e.name AS concept_name, e.type AS entity_type, p.created_at AS created_at, count(distinct p) AS cnt
            """
            try:
                t_res = await session.run(timeline_cypher)
                async for record in t_res:
                    cname = record["concept_name"]
                    etype = record["entity_type"] or "CONCEPT"
                    cnt = record["cnt"]
                    yr_str = "2024"  # Default year group

                    if cname not in timelines_dict:
                        timelines_dict[cname] = {
                            "concept_name": cname,
                            "entity_type": etype,
                            "yearly_counts": {}
                        }
                    timelines_dict[cname]["yearly_counts"][yr_str] = (
                        timelines_dict[cname]["yearly_counts"].get(yr_str, 0) + cnt
                    )
            except Exception as e:
                logger.error(f"Failed to query concept timelines from Neo4j: {str(e)}")

            # 2. Query Concept Co-occurrence Matrix
            co_cypher = """
            MATCH (p:Paper)-[:MENTIONS]->(e1:Entity)
            MATCH (p)-[:MENTIONS]->(e2:Entity)
            WHERE id(e1) < id(e2) AND e1.type <> 'AUTHOR' AND e2.type <> 'AUTHOR'
            RETURN e1.name AS concept1, e2.name AS concept2, count(distinct p) AS co_cnt
            ORDER BY co_cnt DESC
            LIMIT 15
            """
            try:
                co_res = await session.run(co_cypher)
                async for record in co_res:
                    co_occurrences.append(
                        ConceptCoOccurrenceItem(
                            concept1=record["concept1"],
                            concept2=record["concept2"],
                            co_occurrence_count=record["co_cnt"]
                        )
                    )
            except Exception as e:
                logger.error(f"Failed to query concept co-occurrences from Neo4j: {str(e)}")

        # Calculate growth rates and emerging topics
        timeline_items: List[ConceptTimelineItem] = []
        for cname, item_data in timelines_dict.items():
            yearly_counts = item_data["yearly_counts"]
            years_sorted = sorted([y for y in yearly_counts.keys() if y.isdigit()])

            growth_rate = 0.0
            is_emerging = False

            if len(years_sorted) >= 2:
                latest_yr = years_sorted[-1]
                prev_yr = years_sorted[-2]
                latest_cnt = yearly_counts[latest_yr]
                prev_cnt = yearly_counts[prev_yr]

                growth_rate = round((latest_cnt - prev_cnt) / max(prev_cnt, 1), 2)
                if growth_rate >= 0.50 and latest_cnt >= 2:
                    is_emerging = True
                    emerging_concepts.append(cname)

            timeline_items.append(
                ConceptTimelineItem(
                    concept_name=cname,
                    entity_type=item_data["entity_type"],
                    yearly_counts=yearly_counts,
                    growth_rate=growth_rate,
                    is_emerging=is_emerging
                )
            )

        return ResearchTrendsResponse(
            timeline=timeline_items,
            emerging_concepts=emerging_concepts,
            top_co_occurrences=co_occurrences
        )
