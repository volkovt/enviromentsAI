# core/domain/entities/task.py

import uuid
from dataclasses import dataclass, field, asdict
from datetime import date, datetime

from utils.utilities import ensure_date

@dataclass
class Task:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    title: str = ""
    description: str = ""
    create_date: date = field(default_factory=date.today)
    update_date: date | None = field(default=None)
    due_date: date = field(default_factory=date.today)
    done_date: date = field(default_factory=date.today)
    done: bool = False

    category: str = ""
    priority: str = ""
    frequency: str = ""
    xp: int = 0
    bcp: int = 0
    tags: list[str] = field(default_factory=list)
    participants: list[str] = field(default_factory=list)
    status: str = "A Fazer"
    namespace: str = "Atual"

    @staticmethod
    def new() -> "Task":
        """
        Cria uma nova Task com ID e data de vencimento padrão (hoje).
        """
        return Task()

    @staticmethod
    def from_dict(data: dict) -> "Task":
        due = data.get("due_date")
        if isinstance(due, str):
            due = datetime.fromisoformat(due).date()
        return Task(
            id=data.get("id", str(uuid.uuid4())),
            title=data.get("title", ""),
            description=data.get("description", ""),
            create_date=ensure_date(data.get("create_date", date.today())),
            update_date=data.get("update_date", None),
            due_date=due or date.today(),
            done_date=date.today(),
            done=data.get("done", False),
            category=data.get("category", ""),
            priority=data.get("priority", ""),
            frequency=data.get("frequency", ""),
            bcp=data.get("bcp", 0),
            xp=data.get("xp", 0),
            tags=data.get("tags", []),
            participants=data.get("participants", []),
            status=data.get("status", "A Fazer"),
            namespace=data.get("namespace", "Atual")
        )

    def to_dict(self) -> dict:
        """
        Converte a Task para um dict compatível com persistência em DynamoDB,
        serializando a data em ISO format.
        """
        d = asdict(self)
        d["create_date"] = self.create_date.isoformat()
        d["update_date"] = ensure_date(self.update_date) if self.update_date else None
        d["due_date"] = self.due_date.isoformat()
        d["done_date"] = self.done_date.isoformat()
        d["namespace"] = self.namespace

        return d

    def toggle(self) -> None:
        """
        Marca/desmarca como concluída.
        """
        self.done = not self.done

