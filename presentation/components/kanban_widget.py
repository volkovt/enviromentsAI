# presentation/views/components/tasks/kanban_widget.py
import logging
from datetime import date

from PyQt5.QtWidgets import QWidget, QListWidget, QListWidgetItem, QHBoxLayout, QLabel, QVBoxLayout, QMessageBox
from PyQt5.QtCore import Qt, QTimer, pyqtSignal

from utils.task_utils import calcular_xp_por_bcp
from utils.utilities import ensure_date

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("[TasksScreen]")

class KanbanWidget(QWidget):
    statusChanged = pyqtSignal()

    def __init__(self, tasks_controller, parent=None):
        super().__init__(parent)
        self.namespace = "Atual"
        self.ctrl = tasks_controller
        self._updating = False
        self._build_ui()
        self.refresh()

    def _build_ui(self):
        layout = QHBoxLayout(self)
        self.cols = {}

        for status in ["A Fazer", "Em Progresso", "Concluídas"]:
            col_layout = QVBoxLayout()
            label = QLabel(status)
            label.setAlignment(Qt.AlignCenter)
            col_layout.addWidget(label)

            col = QListWidget()
            col.setSelectionMode(QListWidget.ExtendedSelection)
            col.setAcceptDrops(True)
            col.setDefaultDropAction(Qt.MoveAction)

            if self.namespace != "Atual" or status == "Concluídas":
                col.setDragEnabled(False)
            else:
                col.setDragEnabled(True)

            col.setObjectName(status)
            col_layout.addWidget(col)
            layout.addLayout(col_layout)
            self.cols[status] = col

            col.model().rowsMoved.connect(self._on_move)
            col.model().rowsRemoved.connect(self._on_move)

    def set_namespace(self, ns: str):
        """Define o namespace ativo e atualiza a view."""
        self.namespace = ns
        self.refresh()
        
    def refresh(self):
        try:
            for col in self.cols.values():
                col.clear()

            for t in self.ctrl.fetch_tasks():
                if t.namespace != self.namespace:
                    continue
                item = QListWidgetItem(t.title)
                item.setData(Qt.UserRole, t.id)
                status = t.status or "A Fazer"
                if status in self.cols:
                    self.cols[status].addItem(item)

        except Exception as e:
            logger.error(f"[KanbanWidget] erro em refresh: {e}")

    def _on_move(self, *args):
        try:
            if self._updating:
                return
            QTimer.singleShot(0, self._process_move)
        except Exception as e:
            logger.error(f"[KanbanWidget] erro agendando atualização: {e}")

    def _process_move(self):
        try:
            self._updating = True
            all_tasks = [t for t in self.ctrl.fetch_tasks() if t.namespace == self.namespace]

            new_completed = []
            for i in range(self.cols["Concluídas"].count()):
                item = self.cols["Concluídas"].item(i)
                tid  = item.data(Qt.UserRole)
                task = next((t for t in all_tasks if t.id == tid), None)
                task.update_date = ensure_date(date.today())
                if task and task.status != "Concluídas":
                    new_completed.append(task)

            if new_completed:
                msg = QMessageBox(self)
                msg.setWindowTitle("Confirmar conclusão")
                msg.setText("Marcar tarefa(s) como concluídas não pode ser desfeito. Deseja continuar?")
                yes = msg.addButton(QMessageBox.Yes)
                no  = msg.addButton(QMessageBox.No)
                msg.setDefaultButton(no)
                msg.exec_()
                if msg.clickedButton() != yes:
                    self.refresh()
                    return

            for status, col in self.cols.items():
                for i in range(col.count()):
                    item = col.item(i)
                    tid  = item.data(Qt.UserRole)
                    task = next((t for t in all_tasks if t.id == tid), None)
                    if task:
                        task.status = status
                        task.done   = (status == "Concluídas")
                        if status == "Concluídas":
                            task.xp = calcular_xp_por_bcp(task.bcp)
                        else:
                            task.xp = 0
                        self.ctrl.update_task(task)

            self.statusChanged.emit()
        except Exception as e:
            logger.error(f"[KanbanWidget] erro em process_move: {e}")
        finally:
            self._updating = False
            self.refresh()
