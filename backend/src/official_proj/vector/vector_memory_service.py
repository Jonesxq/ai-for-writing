from official_proj.vector_db.embedding_service import EmbeddingService
from official_proj.vector_db.milvus_client import MilvusClient


class VectorMemoryService:
    """
    负责：文本 → embedding → Milvus
    """

    def __init__(self):
        self.embedding_service = EmbeddingService()
        self.milvus_client = MilvusClient()


    def _chunk_text(self, text: str, size: int = 500, overlap: int = 100):
        """
        简单稳定的 chunk 策略（字符级，适合中文）
        """
        chunks = []
        start = 0
        length = len(text)

        while start < length:
            end = start + size
            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)
            start = end - overlap

        return chunks

    def store_chapter(self, chapter: Chapter):
        """
        将章节内容写入 Milvus（多 chunk）
        """
        chunks = self._chunk_text(chapter.content)

        for chunk in chunks:
            embedding = self.embedding_service.embed(chunk)

            self.milvus_client.insert_plot_memory(
                novel_id=chapter.novel_id,
                chapter_number=chapter.chapter_number,
                content=chunk[:2000],  # 防止 VARCHAR 超限
                embedding=embedding
            )