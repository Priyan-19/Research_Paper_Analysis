import asyncio
from app.database.postgres import AsyncSessionLocal
from app.services.paper_service import PaperService
from app.workers.paper_processing import PaperProcessingWorker

async def reprocess_all():
    async with AsyncSessionLocal() as db:
        papers, total = await PaperService.list_papers(db, limit=100)
        print(f"Found {total} paper(s) in PostgreSQL.")
        for paper in papers:
            print(f"Reprocessing paper '{paper.title or paper.filename}' (ID: {paper.id})...")
            res = await PaperProcessingWorker.process_paper(
                paper_id=paper.id,
                file_path=paper.file_path,
                title=paper.title or paper.filename,
                db=db
            )
            print(f"Result for '{paper.filename}':", res)

if __name__ == "__main__":
    asyncio.run(reprocess_all())
