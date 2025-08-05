from dataclasses import dataclass, field
from typing import Dict, Optional

@dataclass
class EnvironmentVariable:
    enabled: bool
    name: str
    type: str
    content_type: str = "application/json"
    value: Optional[str] = ""
    method: Optional[str] = None
    url: Optional[str] = None
    params: Dict[str, str] = field(default_factory=dict)
    headers: Dict[str, str] = field(default_factory=dict)
    body: Optional[str] = ""
    body_params: Dict[str, str] = field(default_factory=dict)
    response: Optional[str] = ""
    extract_path: Optional[str] = ""
