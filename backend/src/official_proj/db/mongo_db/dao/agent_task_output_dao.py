import uuid
from datetime import datetime

class AgentTaskOutputDAO:
    def __init__(self, mongo):
        self.col = mongo.collection("agent_task_outputs")

    def create(
        self,
        novel_id: str,
        task_name: str,
        output_type: str,
        raw_output: str | None,
        json_output: dict | list | None
    ) -> dict:
        doc = {
            "_id": str(uuid.uuid4()),
            "novel_id": novel_id,
            "task_name": task_name,
            "output_type": output_type,   # e.g. "TaskOutput"
            "raw_output": raw_output,
            "json_output": json_output,
            "created_at": datetime.utcnow()
        }
        self.col.insert_one(doc)
        return doc
