from sentence_transformers import SentenceTransformer
from typing import List

class EmbeddingService:
    def __init__(self, model_name: str = "BAAI/bge-base-zh-v1.5"):
        # 模型只在初始化时加载一次
        self.model = SentenceTransformer(model_name)

    def embed(self, text: str) -> List[float]:
        """
        将文本转换为向量（768维）
        """
        embedding = self.model.encode(
            text,
            normalize_embeddings=True  # 推荐：和 IP / cosine 更搭
        )
        return embedding.tolist()

if __name__ == "__main__":
    service = EmbeddingService()
    vec = service.embed("小说主角在第一章遇到了一位神秘的老者")
    print(f"向量长度：{len(vec)}")
