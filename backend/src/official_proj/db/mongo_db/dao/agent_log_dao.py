# official_proj/db/dao/agent_log_dao.py
import uuid
from datetime import datetime

class AgentLogDAO:
    def __init__(self, mongo):
        self.col = mongo.collection("agent_logs")

    def create(
        self,
        novel_id: str,
        agent_name: str,
        input_summary: str,
        output_summary: str
    ):
        doc = {
            "_id": str(uuid.uuid4()),
            "novel_id": novel_id,
            "agent_name": agent_name,
            "input_summary": input_summary,
            "output_summary": output_summary,
            "created_at": datetime.utcnow()
        }
        self.col.insert_one(doc)
        return doc
