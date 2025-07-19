# presentation/controllers/tasks_controller.py
import json
import re
import uuid
from datetime import datetime, timedelta

from interface.task import Task
from services.local_session_service import LocalSessionService

class TasksController:
    def __init__(self):
        self.db = LocalSessionService()

    def fetch_tasks(self) -> list[Task]:
        items = self.db.scan()
        return [Task.from_dict(i) for i in items]

    def add_task(self, task: Task):
        self.db.put_item(task.to_dict())

    def update_task(self, task: Task):
        self.db.update_item(task.id, task.to_dict())

    def delete_task(self, task_id: str):
        self.db.delete_item(task_id)

    def generate_ia_tasks(self, instruction: str) -> list[Task]:
        # construindo prompt
        prompt = f"""
            Você é um especialista em produtividade e gerenciamento de tarefas.
            Receberá a seguinte instrução do usuário:
            \"\"\"{instruction}\"\"\"
            Responda **apenas** com um JSON válido, no formato:
            {{
              "tasks": [
                {{
                  "title": string,
                  "description": string,
                  "priority": "Alta" | "Média" | "Baixa",
                  "due_date": "YYYY-MM-DD"
                }},
                ...
              ]
            }}
            Não retorne nenhum outro texto ou formatação, apenas o JSON Válido.
        """

        #response = stackspot_ai.chat(prompt)
        response = self.mock_ia_response()
        try:
            data = json.loads(self.extract_markdown_content(response))
            out = []
            for it in data.get("tasks", []):
                t = Task(
                    title=it["title"],
                    description=it.get("description", ""),
                    priority=it.get("priority", "Média"),
                    due_date=datetime.fromisoformat(it["due_date"]).date()
                )
                out.append(t)
            return out
        except json.JSONDecodeError:
            raise ValueError("Resposta da IA não está no formato esperado. Verifique a instrução e tente novamente.")

    def extract_markdown_content(self, text):
        match = re.search(r"```(?:\w+\n)?(.*?)```", text, re.DOTALL)
        if match:
            return match.group(1).strip()
        return text.strip()

    def mock_ia_response(self):
        base_date = datetime(2025, 7, 12)
        tasks = []
        for i in range(5):
            delta = i - 10
            due_date = (base_date + timedelta(days=delta)).strftime("%Y-%m-%d")
            tasks.append({
                "title": f"Tarefa {uuid.uuid4().hex[:8]}",
                "description": f"Descrição da tarefa {i + 1}",
                "priority": ["Alta", "Média", "Baixa"][i % 3],
                "due_date": due_date
            })
        tasks_json = json.dumps({"tasks": tasks}, ensure_ascii=False, indent=2)
        return f"""\n```json\n{tasks_json}\n```\n"""