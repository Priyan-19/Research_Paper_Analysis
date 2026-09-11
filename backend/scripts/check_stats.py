import asyncio
from app.database.postgres import AsyncSessionLocal
from app.services.paper_service import PaperService
from app.database.neo4j import neo4j_client, get_neo4j_session

async def check():
    async with AsyncSessionLocal() as db:
        papers, total_papers = await PaperService.list_papers(db)
        total_chunks = 0
        for p in papers:
            chunks = await PaperService.get_paper_chunks(db, p.id)
            total_chunks += len(chunks)

    await neo4j_client.connect()
    async with get_neo4j_session() as s:
        res = await s.run("MATCH (src:Entity)-[r]->(tgt:Entity) WHERE type(r) <> 'MENTIONS' RETURN count(r) AS cnt")
        rec = await res.single()
        triples_cnt = rec["cnt"] if rec else 0

    await neo4j_client.close()

    print("==========================================")
    print("CURRENT LIVE DATABASE METRICS:")
    print(f"  * Ingested Research Papers:  {total_papers}")
    print(f"  * PostgreSQL Vector Chunks:  {total_chunks}")
    print(f"  * Live Neo4j Graph Triples:  {triples_cnt}")
    print("==========================================")

if __name__ == "__main__":
    asyncio.run(check())
