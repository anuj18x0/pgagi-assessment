from typing import Dict
from app.schemas.base import BaseSchema

class HealthStatus(BaseSchema):
    status: str
    version: str

class ReadinessStatus(BaseSchema):
    status: str
    checks: Dict[str, str]
