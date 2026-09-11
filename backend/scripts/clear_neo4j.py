import asyncio
from app.database.neo4j import neo4j_client, get_neo4j_session

async def clear_graph():
    await neo4j_client.connect()
    async with get_neo4j_session() as session:
        await session.run("MATCH (n) DETACH DELETE n")
        print("SUCCESS: Deleted all nodes, relationships, and triples from Neo4j Knowledge Graph!")
    await neo4j_client.close()

if __name__ == "__main__":
    asyncio.run(clear_graph())
