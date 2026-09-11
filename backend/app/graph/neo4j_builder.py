from typing import List, Dict, Any, Optional
from app.database.neo4j import get_neo4j_session
from app.core.logging import logger
from app.schemas.graph import (
    KnowledgeGraphExtractionResult,
    GraphNodeResponse,
    GraphEdgeResponse,
    PaperGraphResponse,
    GraphStatsResponse
)


class Neo4jGraphBuilder:
    """
    Neo4j Database Manager for creating nodes, relationships, and querying Knowledge Graphs.
    """

    @classmethod
    async def persist_paper_graph(
        cls,
        paper_id: str,
        paper_title: str,
        graph_data: KnowledgeGraphExtractionResult
    ) -> bool:
        """
        Persists paper node, entity nodes, and relationship edges into Neo4j database using Cypher.
        """
        async with get_neo4j_session() as session:
            # 1. Create/Merge Paper Node
            create_paper_query = """
            MERGE (p:Paper {id: $paper_id})
            ON CREATE SET p.title = $title, p.created_at = timestamp()
            ON MATCH SET p.title = $title
            RETURN p.id
            """
            await session.run(create_paper_query, paper_id=paper_id, title=paper_title)

            # 2. Create/Merge Entity Nodes and LINK to Paper Node
            create_entity_query = """
            MATCH (p:Paper {id: $paper_id})
            MERGE (e:Entity {name: $name})
            ON CREATE SET e.type = $type, e.description = $description, e.created_at = timestamp()
            ON MATCH SET e.type = $type, e.description = COALESCE($description, e.description)
            MERGE (p)-[:MENTIONS]->(e)
            """

            for entity in graph_data.entities:
                await session.run(
                    create_entity_query,
                    paper_id=paper_id,
                    name=entity.name,
                    type=entity.type.value if hasattr(entity.type, 'value') else str(entity.type),
                    description=entity.description or ""
                )

            # 3. Create Directed Relationship Edges between Entities
            for rel in graph_data.relationships:
                rel_type = rel.relation_type.value if hasattr(rel.relation_type, 'value') else str(rel.relation_type)
                
                # Cypher query with dynamic relationship predicate type
                create_rel_query = f"""
                MATCH (src:Entity {{name: $src_name}})
                MATCH (tgt:Entity {{name: $tgt_name}})
                MERGE (src)-[r:{rel_type}]->(tgt)
                ON CREATE SET r.description = $description, r.paper_id = $paper_id
                """
                await session.run(
                    create_rel_query,
                    src_name=rel.source_entity,
                    tgt_name=rel.target_entity,
                    description=rel.description or "",
                    paper_id=paper_id
                )

            logger.info(
                f"Successfully persisted {len(graph_data.entities)} nodes and "
                f"{len(graph_data.relationships)} edges to Neo4j for paper '{paper_title}' ({paper_id})."
            )
            return True

    @classmethod
    async def get_paper_graph(cls, paper_id: str, paper_title: str) -> PaperGraphResponse:
        """
        Fetches full subnetwork of entity nodes and edges associated with a specific paper.
        """
        nodes_dict: Dict[str, GraphNodeResponse] = {}
        edges: List[GraphEdgeResponse] = []

        async with get_neo4j_session() as session:
            # Fetch entities mentioned by paper
            nodes_query = """
            MATCH (p:Paper {id: $paper_id})-[:MENTIONS]->(e:Entity)
            RETURN e.name AS name, e.type AS type, e.description AS description
            """
            nodes_res = await session.run(nodes_query, paper_id=paper_id)
            async for record in nodes_res:
                name = record["name"]
                nodes_dict[name] = GraphNodeResponse(
                    id=name,
                    name=name,
                    type=record["type"] or "CONCEPT",
                    description=record["description"]
                )

            # Fetch relationships between those entities
            edges_query = """
            MATCH (p:Paper {id: $paper_id})-[:MENTIONS]->(src:Entity)
            MATCH (src)-[r]->(tgt:Entity)
            WHERE (p)-[:MENTIONS]->(tgt) AND type(r) <> 'MENTIONS'
            RETURN src.name AS source, tgt.name AS target, type(r) AS rel_type, r.description AS description
            """
            edges_res = await session.run(edges_query, paper_id=paper_id)
            async for record in edges_res:
                edges.append(
                    GraphEdgeResponse(
                        source=record["source"],
                        target=record["target"],
                        relation_type=record["rel_type"],
                        description=record["description"]
                    )
                )

        return PaperGraphResponse(
            paper_id=paper_id,
            paper_title=paper_title,
            total_nodes=len(nodes_dict),
            total_edges=len(edges),
            nodes=list(nodes_dict.values()),
            edges=edges
        )

    @classmethod
    async def get_graph_stats(cls) -> GraphStatsResponse:
        """
        Retrieves global Knowledge Graph statistics from Neo4j.
        """
        total_nodes = 0
        total_rels = 0
        entity_counts: Dict[str, int] = {}
        rel_counts: Dict[str, int] = {}

        async with get_neo4j_session() as session:
            # Count Entity Nodes by Type
            nodes_res = await session.run("MATCH (e:Entity) RETURN e.type AS type, count(e) AS cnt")
            async for record in nodes_res:
                t = record["type"] or "CONCEPT"
                cnt = record["cnt"]
                entity_counts[t] = cnt
                total_nodes += cnt

            # Count Relationship Edges by Type
            rels_res = await session.run("MATCH ()-[r]->() WHERE type(r) <> 'MENTIONS' RETURN type(r) AS rel_type, count(r) AS cnt")
            async for record in rels_res:
                rt = record["rel_type"]
                cnt = record["cnt"]
                rel_counts[rt] = cnt
                total_rels += cnt

        return GraphStatsResponse(
            total_nodes=total_nodes,
            total_relationships=total_rels,
            entity_type_counts=entity_counts,
            relationship_type_counts=rel_counts
        )
