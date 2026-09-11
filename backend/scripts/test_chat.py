import asyncio
from app.database.postgres import AsyncSessionLocal
from app.rag.chat_service import GroundedChatService
from app.schemas.rag import ChatRequest, SearchModeEnum

async def test_chat():
    async with AsyncSessionLocal() as db:
        req = ChatRequest(
            query="What are the main applications and architectural benefits of LangChain?",
            search_mode=SearchModeEnum.HYBRID,
            top_k=5
        )
        print("Testing GroundedChatService...")
        res = await GroundedChatService.generate_grounded_chat(db, req)
        print("==========================================")
        print("ANSWER:")
        print(res.answer)
        print("==========================================")
        print("Execution Time:", res.execution_time_seconds, "s")
        print("Total Citations:", res.total_citations)

if __name__ == "__main__":
    asyncio.run(test_chat())
