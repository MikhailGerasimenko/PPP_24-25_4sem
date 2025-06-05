from pydantic import BaseModel

class BruteforceTask(BaseModel):
    hash_to_crack: str

class BruteforceResult(BaseModel):
    task_id: str
    status: str
    result: str | None = None 