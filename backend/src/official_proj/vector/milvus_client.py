from pymilvus import connections
from official_proj.vector_db.milvus_schema import (
    create_plot_memory_collection,
)
import time
import uuid


class MilvusClient:

    def __init__(self, host="localhost", port="19530"):
        connections.connect(
            alias="default",
            host=host,
            port=port
        )

        self.collection = create_plot_memory_collection()
        self.collection.load()

    def insert_plot_memory(
        self,
        novel_id: str,
        chapter_number: int,
        content: str,
        embedding: list[float]
    ):
        # ✅ 1. 强校验 embedding
        if not isinstance(embedding, list):
            raise TypeError("embedding must be list[float]")

        if len(embedding) != 768:
            raise ValueError(f"embedding dim error: {len(embedding)} != 768")

        data = {
            "id": str(uuid.uuid4()),
            "novel_id": novel_id,
            "chapter_number": chapter_number,
            "content": content,
            "embedding": embedding,
            "created_at": int(time.time())
        }

        # ✅ 推荐用 insert([dict])，而不是列式
        self.collection.insert([data])
        self.collection.flush()

    def search_plot_memory(
        self,
        novel_id: str,
        query_embedding: list[float],
        top_k: int = 5
    ):
        if len(query_embedding) != 768:
            raise ValueError("query embedding dim mismatch")

        results = self.collection.search(
            data=[query_embedding],
            anns_field="embedding",
            param={
                "metric_type": "IP",
                "params": {"ef": 64}
            },
            limit=top_k,
            expr=f'novel_id == "{novel_id}"',
            output_fields=["content", "chapter_number"]
        )

        return results[0]
if __name__ == "__main__":
    from official_proj.vector_db.milvus_schema import (
        Collection
    )
    MilvusClient()
    col = Collection("plot_memory")
    print(col.schema)