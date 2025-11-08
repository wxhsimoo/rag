from dataclasses import dataclass
from typing import List, Optional, Dict, Any


@dataclass
class PromptDoc:
    content: str
    source: Optional[str] = None


@dataclass
class PromptContext:
    question: str
    docs: List[PromptDoc]
    history_lines: Optional[List[str]] = None
    user_profile: Optional[Dict[str, Any]] = None

