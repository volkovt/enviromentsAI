from dataclasses import dataclass, field
from typing import Dict, Optional

@dataclass
class EnvironmentVariable:
    enabled: bool
    name: str
    type: str
    value: Optional[str] = ""
    method: Optional[str] = None
    url: Optional[str] = None
    params: Dict[str, str] = field(default_factory=dict)
    headers: Dict[str, str] = field(default_factory=dict)
    body: Optional[str] = ""
    response: Optional[str] = ""
    extract_path: Optional[str] = ""
