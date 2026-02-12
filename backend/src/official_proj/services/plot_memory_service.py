# official_proj/services/plot_memory_service.py

class PlotMemoryService:
    def __init__(self, embedding_service, milvus_client):
        self.embedding_service = embedding_service
        self.milvus_client = milvus_client

    #写完一章后：记忆写入 Milvus
    def save_plot_memory(
        self,
        novel_id: str,
        chapter_number: int,
        plot_summary_text: str
    ):
        embedding = self.embedding_service.embed(plot_summary_text)

        self.milvus_client.insert_plot_memory(
            novel_id=novel_id,
            chapter_number=chapter_number,
            content=plot_summary_text,
            embedding=embedding
        )

    #写新章节前：剧情回忆（最关键）
    def recall_relevant_plots(
            self,
            novel_id: str,
            current_chapter_goal: str,
            top_k: int = 5
    ) -> list[dict]:
        query_embedding = self.embedding_service.embed(current_chapter_goal)

        results = self.milvus_client.search_plot_memory(
            novel_id=novel_id,
            query_embedding=query_embedding,
            top_k=top_k
        )

        return [
            {
                "chapter": hit.entity.get("chapter_number"),
                "content": hit.entity.get("content")
            }
            for hit in results
        ]