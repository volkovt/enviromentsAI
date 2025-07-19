import logging
from datetime import date, timedelta, datetime

from PyQt5.QtGui import QBrush, QKeySequence, QIntValidator, QCursor
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QListWidget,
    QStackedWidget, QLabel, QLineEdit, QTextEdit, QDateEdit, QMessageBox, QListWidgetItem, QComboBox, QShortcut,
    QAbstractItemView, QDialog, QDialogButtonBox, QMenu, QFileDialog, QInputDialog, QSizePolicy,
    QSplitter, QApplication
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QSize
from dateutil.relativedelta import relativedelta
import qtawesome as qta

from controller.tasks_controller import TasksController
from interface.task import Task
from presentation.components.gamification_widget import GamificationWidget
from presentation.components.kanban_widget import KanbanWidget
from presentation.components.timeline_component import TimelineWidget
from services.notification_manager import NotificationManager
from utils.task_utils import calcular_xp_por_bcp

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("[TasksScreen]")

class TasksScreen(QWidget):
    def __init__(self):
        super().__init__()
        self.setObjectName("TasksScreen")
        self.setBaseSize(800, 600)

        self.loader = None
        self.setWindowTitle("To-Do Dashboard")
        self.ctrl = TasksController()
        self.current = Task.new()
        self._build_ui()
        self._update_namespaces()
        self.on_new()
        self.load_tasks()
        self._show_daily_summary()

    def _build_ui(self):
        main = QVBoxLayout(self)
        main.setContentsMargins(10, 10, 10, 10)
        main.setSpacing(10)
        main.setAlignment(Qt.AlignTop)

        nav_layout = QHBoxLayout()

        scr_layout = QHBoxLayout()
        scr_layout.setContentsMargins(0, 0, 0, 0)
        scr_layout.setAlignment(Qt.AlignRight)

        btn_tasks = QPushButton("Tasks")
        btn_tasks.setIcon(qta.icon("fa5s.tasks", color="orange"))
        btn_tasks.setIconSize(QSize(24, 24))
        btn_tasks.setToolTip("Voltar para lista de tarefas")
        btn_tasks.clicked.connect(lambda: self.stack.setCurrentIndex(0))
        scr_layout.addWidget(btn_tasks)

        btn_tl_nav = QPushButton("Timeline")
        btn_tl_nav.setIcon(qta.icon("fa5s.clock", color="orange"))
        btn_tl_nav.setIconSize(QSize(24, 24))
        btn_tl_nav.setToolTip("Visualizar linha do tempo")
        btn_tl_nav.clicked.connect(lambda: self.stack.setCurrentWidget(self.timeline))
        scr_layout.addWidget(btn_tl_nav)

        btn_kb_nav = QPushButton("Kanban")
        btn_kb_nav.setIcon(qta.icon("fa5s.columns", color="orange"))
        btn_kb_nav.setIconSize(QSize(24, 24))
        btn_kb_nav.setToolTip("Visualizar tarefas em Kanban")
        btn_kb_nav.clicked.connect(lambda: self.stack.setCurrentWidget(self.kanban))
        scr_layout.addWidget(btn_kb_nav)

        btn_gm_nav = QPushButton("Metas")
        btn_gm_nav.setIcon(qta.icon("fa5s.trophy", color="orange"))
        btn_gm_nav.setIconSize(QSize(24, 24))
        btn_gm_nav.setToolTip("Visualizar gamificação e metas")
        btn_gm_nav.clicked.connect(lambda: self.stack.setCurrentWidget(self.gamification))
        scr_layout.addWidget(btn_gm_nav)

        filters_layout = QHBoxLayout()
        filters_layout.setAlignment(Qt.AlignLeft)
        filters_layout.setContentsMargins(0, 0, 0, 0)

        self.namespace_filter = QComboBox()
        self.namespace_filter.currentTextChanged.connect(self.load_tasks)
        self.close_btn = QPushButton()
        self.close_btn.setIcon(qta.icon("fa5s.times", color="red"))
        self.close_btn.setIconSize(QSize(24, 24))
        self.close_btn.setToolTip("Encerrar o ciclo atual e iniciar um novo")
        self.close_btn.clicked.connect(self.on_close_cycle)


        self.status_filter = QComboBox()
        self.status_filter.setToolTip("Filtrar por status da tarefa")
        self.status_filter.addItems(["A Fazer", "Em Progresso", "Concluídas"])
        self.status_filter.currentTextChanged.connect(self.load_tasks)

        self.category_filter = QComboBox()
        self.category_filter.addItems(["Todas", "Pessoal", "Trabalho", "Estudo"])
        self.category_filter.currentTextChanged.connect(self.load_tasks)

        self.priority_filter = QComboBox()
        self.priority_filter.addItems(["Todas", "Alta", "Média", "Baixa"])
        self.priority_filter.currentTextChanged.connect(self.load_tasks)

        filters_layout.addWidget(QLabel("Ciclo:"))
        filters_layout.addWidget(self.namespace_filter)
        filters_layout.addWidget(self.close_btn)

        filters_layout.addWidget(QLabel("Status:"))
        filters_layout.addWidget(self.status_filter)
        filters_layout.addSpacing(20)
        filters_layout.addWidget(QLabel("Categoria:"))
        filters_layout.addWidget(self.category_filter)
        filters_layout.addSpacing(20)
        filters_layout.addWidget(QLabel("Prioridade:"))
        filters_layout.addWidget(self.priority_filter)
        filters_layout.addStretch()

        nav_layout.addLayout(filters_layout)
        nav_layout.addLayout(scr_layout)


        main.addLayout(nav_layout)

        left_widget = QWidget()
        left_layout  = QVBoxLayout(left_widget)

        self.list_widget = QListWidget()
        self.list_widget.itemClicked.connect(self.on_select)
        self.list_widget.setSelectionMode(QAbstractItemView.SingleSelection)
        self.list_widget.itemSelectionChanged.connect(self._update_delete_button_state)
        self.list_widget.setContextMenuPolicy(Qt.CustomContextMenu)
        self.list_widget.customContextMenuRequested.connect(self._show_status_menu)
        left_layout .addWidget(self.list_widget, 1)

        left_layout .addWidget(QLabel("Resumo de Tarefas"))
        self.info_summary = QTextEdit()
        self.info_summary.setReadOnly(True)
        self.info_summary.setPlaceholderText("Resumo de tarefas para hoje...")
        self.info_summary.setFixedHeight(200)
        self.info_summary.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.info_summary.setStyleSheet("border: 2px solid #ccc;")
        self.info_summary.setFontPointSize(10)
        self.info_summary.setFontFamily("Arial")
        self.info_summary.setText("Resumo de tarefas para hoje:\n\n- Nenhuma tarefa pendente.")
        left_layout .addWidget(self.info_summary)

        self.stack = QStackedWidget()

        left_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.stack.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        splitter = QSplitter(Qt.Horizontal)
        splitter.setStyleSheet("""
            QSplitter {
                border: 2px solid #aaa;
                border-radius: 6px;
                background: #fafafa;
            }
            QSplitter::handle {
                background: #ccc;
            }
        """)

        splitter.addWidget(left_widget)
        splitter.addWidget(self.stack)
        splitter.setStretchFactor(0, 2)
        splitter.setStretchFactor(1, 2)

        self.splitter = splitter
        main.addWidget(splitter)

        self.detail = QWidget()
        form = QVBoxLayout(self.detail)
        self.stack.addWidget(self.detail)

        btn_layout = QHBoxLayout()
        btn_layout.setContentsMargins(0, 0, 0, 0)
        btn_layout.setSpacing(10)
        btn_layout.setAlignment(Qt.AlignRight)
        new_btn = QPushButton()
        new_btn.setToolTip("Criar nova tarefa")
        new_btn.setIcon(qta.icon("fa5s.plus", color="green"))
        new_btn.clicked.connect(self.on_new)
        btn_layout.addWidget(new_btn)

        ia_btn = QPushButton()
        ia_btn.setIcon(qta.icon("fa5s.robot", color="orange"))
        ia_btn.setToolTip("Criar tarefa a partir de IA")
        ia_btn.clicked.connect(self.on_ia)
        btn_layout.addWidget(ia_btn)

        self.save_button = QPushButton()
        self.save_button.setIcon(qta.icon("fa5s.save", color="orange"))
        self.save_button.setToolTip("Salvar tarefa")
        self.save_button.clicked.connect(self.on_save)
        btn_layout.addWidget(self.save_button)

        self.delete_button = QPushButton()
        self.delete_button.setToolTip("Excluir tarefa")
        self.delete_button.setIcon(qta.icon("fa5s.trash-alt", color="red"))
        self.delete_button.clicked.connect(self.on_delete)
        btn_layout.addWidget(self.delete_button)

        exp_btn = QPushButton()
        exp_btn.setToolTip("Exportar Tasks")
        exp_btn.setIcon(qta.icon("fa5s.download", color="orange"))
        exp_btn.clicked.connect(self.on_export)
        btn_layout.addWidget(exp_btn)

        form.addLayout(btn_layout)

        self.title_edit = QLineEdit()
        self.title_edit.setPlaceholderText("Título")
        self.tags_edit = QLineEdit()
        self.tags_edit.setPlaceholderText("tag1, tag2, tag3")
        self.participants_edit = QLineEdit()
        self.participants_edit.setPlaceholderText("nome1, nome2")
        self.bcp_edit = QLineEdit()
        self.bcp_edit.setPlaceholderText("BCP (apenas números)")
        self.bcp_edit.setValidator(QIntValidator(0, 99999999, self))
        self.desc_edit = QTextEdit()
        self.desc_edit.setPlaceholderText("Descrição")
        self.due_date = QDateEdit(calendarPopup=True)

        self.category_combo = QComboBox()
        self.category_combo.addItems(["Trabalho", "Pessoal", "Estudo"])
        self.priority_combo = QComboBox()
        self.priority_combo.addItems(["Alta", "Média", "Baixa"])
        self.frequency_combo = QComboBox()
        self.frequency_combo.addItems(["Nenhuma", "Diária", "Semanal", "Mensal"])

        form.addWidget(QLabel("Título:"))
        form.addWidget(self.title_edit)
        form.addWidget(QLabel("BCP:"))
        form.addWidget(self.bcp_edit)
        form.addWidget(QLabel("Tags:"))
        form.addWidget(self.tags_edit)
        form.addWidget(QLabel("Participantes:"))
        form.addWidget(self.participants_edit)
        form.addWidget(QLabel("Categoria:"))
        form.addWidget(self.category_combo)
        form.addWidget(QLabel("Prioridade:"))
        form.addWidget(self.priority_combo)
        form.addWidget(QLabel("Frequência:"))
        form.addWidget(self.frequency_combo)
        form.addWidget(QLabel("Descrição:"))
        form.addWidget(self.desc_edit)
        form.addWidget(QLabel("Vencimento:"))
        form.addWidget(self.due_date)

        self.timeline = TimelineWidget(self.ctrl)
        self.stack.addWidget(self.timeline)

        self.kanban = KanbanWidget(self.ctrl)
        self.kanban.statusChanged.connect(self.load_tasks)
        self.stack.addWidget(self.kanban)

        self.gamification = GamificationWidget(self.ctrl)
        self.stack.addWidget(self.gamification)

        self.delete_shortcut = QShortcut(QKeySequence(Qt.Key_Delete), self.list_widget)
        self.delete_shortcut.setContext(Qt.WidgetWithChildrenShortcut)
        self.delete_shortcut.activated.connect(self.delete_selected_tasks)

        self.save_shortcut = QShortcut(QKeySequence("Ctrl+S"), self)
        self.save_shortcut.setContext(Qt.WidgetWithChildrenShortcut)
        self.save_shortcut.activated.connect(self.on_save)

        self.notification_manager = NotificationManager(self)
        self._first_show = True

    def load_tasks(self):
        all_tasks = self.ctrl.fetch_tasks()
        cat = self.category_filter.currentText()
        pri = self.priority_filter.currentText()
        stat = self.status_filter.currentText()
        ns = self.namespace_filter.currentText() or "Atual"

        if ns != "Atual":
            self.close_btn.setEnabled(False)
        else:
            self.close_btn.setEnabled(True)

        self.kanban.set_namespace(ns)
        self.gamification.set_namespace(ns)
        self.timeline.set_namespace(ns)

        def keep(t: Task):
            ok_cat = (cat == "Todas" or t.category == cat)
            ok_pri = (pri == "Todas" or t.priority == pri)
            ok_stat = (t.status == stat)
            ok_ns = (t.namespace == ns)
            return ok_ns and ok_cat and ok_pri and ok_stat

        tasks = [t for t in all_tasks if keep(t)]

        class Loader(QThread):
            tasks_loaded = pyqtSignal(list)

            def run(inner):
                inner.tasks_loaded.emit(tasks)

        try:
            self.loader = Loader()
            self.loader.tasks_loaded.connect(self._populate_list)
            self.loader.start()
        except Exception as e:
            logger.error(f"[TasksScreen] erro ao carregar tarefas: {e}")
            QMessageBox.critical(self, "Erro", "Falha ao carregar tarefas.")

        try:
            today = date.today()
            due_today = [t for t in tasks if not t.done and t.due_date == today]
            if due_today:
                titles = ", ".join(t.title for t in due_today)
                self.notification_manager.notify(
                    "Tarefas para hoje",
                    f"{len(due_today)} pendente(s): {titles}"
                    f" (vencem hoje: {today.strftime('%d/%m/%Y')})",
                    duration=10000,
                )
        except Exception as e:
            logger.error(f"[TasksScreen] erro ao mostrar notificações: {e}")

        self._show_daily_summary()
        if self.gamification:
            self.gamification.refresh()

        if self.timeline:
            self.timeline.refresh()

    def _populate_list(self, tasks: list[Task]):
        self.list_widget.clear()
        for task in tasks:
            try:
                if isinstance(task.update_date, str):
                    update_date = datetime.strptime(task.update_date, "%Y-%m-%d").strftime("%d/%m")
                else:
                    update_date = 'Sem Alterações'
            except Exception as e:
                logger.error(f"[TasksScreen] erro ao formatar update_date: {e}")
                update_date = 'Sem Alterações'

            title = f"[{update_date}] {task.title}"
            item = QListWidgetItem(title)
            item.setData(Qt.UserRole, task.id)

            if not task.status == "Concluídas":
                days_left = (task.due_date - date.today()).days
                if days_left < 0:
                    item.setForeground(QBrush(Qt.red))
                    item.setToolTip(f"Tarefa vencida há {-days_left} dias")
                elif days_left <= 3:
                    item.setForeground(QBrush(Qt.yellow))
                    item.setToolTip("Tarefa vencendo nos próximos 3 dias")
                else:
                    item.setToolTip("Tarefa dentro do prazo")


            self.list_widget.addItem(item)

    def _show_daily_summary(self):
        try:
            self.info_summary.clear()

            all_tasks = [t for t in self.ctrl.fetch_tasks() if t.namespace == "Atual"]
            today      = date.today()
            in_3_days  = today + timedelta(days=3)

            due_soon = [
                t for t in all_tasks
                if not t.done and today <= t.due_date <= in_3_days
            ]

            recurring = []
            for t in all_tasks:
                if not t.status == "Concluídas" and t.frequency not in ("", "Nenhuma"):
                    last = max(t.due_date, today)
                    if t.frequency == "Diária":
                        nxt = last + relativedelta(days=1)
                    elif t.frequency == "Semanal":
                        nxt = last + relativedelta(weeks=1)
                    elif t.frequency == "Mensal":
                        nxt = last + relativedelta(months=1)
                    else:
                        continue
                    if today <= nxt <= in_3_days:
                        recurring.append((t, nxt))

            lines = []
            if due_soon:
                lines.append(f"Tarefas pendentes ({today.strftime('%d/%m/%Y')} – {in_3_days.strftime('%d/%m/%Y')}):")
                lines += [f"- {t.title} (vence em {t.due_date.strftime('%d/%m/%Y')})" for t in due_soon]
            else:
                lines.append("Nenhuma tarefa pendente para os próximos dias.")

            if recurring:
                lines.append("\nRecorrentes previstas:")
                lines += [
                    f"- {t.title} (próxima em {nxt.strftime('%d/%m/%Y')})"
                    for t, nxt in recurring
                ]

            self.info_summary.setText("\n".join(lines))
            logger.info(f"[TasksScreen] resumo diário atualizado com {len(due_soon)} pendentes e {len(recurring)} recorrentes")
        except Exception as e:
            logger.error(f"[TasksScreen] erro em _show_daily_summary: {e}")

    def on_export(self):
        try:
            path, _ = QFileDialog.getSaveFileName(
                self,
                "Exportar Tasks para Excel",
                "",
                "Planilha Excel (*.xlsx)"
            )
            if not path:
                return

            if not path.lower().endswith(".xlsx"):
                path += ".xlsx"

            tasks = [t for t in self.ctrl.fetch_tasks() if t.namespace == self.namespace_filter.currentText()]
            headers = [
                "ID",
                "Título",
                "BCP",
                "Tags",
                "Participantes",
                "Categoria",
                "Prioridade",
                "Frequência",
                "Descrição",
                "Status",
                "Criado",
                "Vencimento",
                "Concluído",
                "XP"
            ]

            from openpyxl import Workbook
            wb = Workbook()
            ws = wb.active
            ws.title = "Tasks"
            ws.append(headers)

            for t in tasks:
                try:
                    create_date = t.create_date.strftime("%d/%m/%Y")
                except Exception as e:
                    logger.error(f"[TasksScreen] erro ao formatar create_date: {e}")
                    create_date = "null"
                try:
                    due_date = t.due_date.strftime("%d/%m/%Y")
                except Exception as e:
                    logger.error(f"[TasksScreen] erro ao formatar due_date: {e}")
                    due_date = "null"
                try:
                    done_date = t.done_date.strftime("%d/%m/%Y")
                except Exception as e:
                    logger.error(f"[TasksScreen] erro ao formatar done_date: {e}")
                    done_date = "null"

                ws.append([
                    t.id,
                    t.title,
                    t.bcp,
                    ";".join(t.tags),
                    ";".join(t.participants),
                    t.category,
                    t.priority,
                    t.frequency or "Nenhuma",
                    t.description,
                    t.status,
                    create_date,
                    due_date,
                    done_date,
                    t.xp
                ])

            wb.save(path)

            QMessageBox.information(
                self,
                "Exportar",
                f"Tarefas exportadas com sucesso para:\n{path}"
            )
            logger.info(f"[TasksScreen] exportado XLSX em {path}")

        except Exception as e:
            logger.error(f"[TasksScreen] erro em on_export: {e}")
            QMessageBox.critical(self, "Erro ao Exportar", "Falha ao exportar tarefas.")

    def _update_delete_button_state(self):
        has_sel = bool(self.list_widget.selectedItems())
        logger.info(f"[TasksScreen] _update_delete_button_state → {has_sel}")
        self.delete_button.setEnabled(has_sel)

    def _show_status_menu(self, pos):
        item = self.list_widget.itemAt(pos)
        if not item:
            return

        task_id = item.data(Qt.UserRole)
        task = next((t for t in self.ctrl.fetch_tasks() if t.id == task_id), None)
        if not task:
            return

        menu = QMenu(self)
        if task.namespace == "Atual":
            status_menu = menu.addMenu("Alterar Status")

            for s in ["A Fazer", "Em Progresso", "Concluídas"]:
                if task.status == "Concluídas" and s != "Concluídas":
                    continue
                action = status_menu.addAction(s)
                action.triggered.connect(
                    lambda checked, tid=task_id, st=s: self._attempt_change_status(tid, st)
                )

        if task.namespace != "Atual":
            copy_menu = menu.addMenu("Copiar Para")
            action = copy_menu.addAction("Atual")
            action.triggered.connect(
                lambda checked, tid=task_id, target_ns="Atual": self._copy_task_to_namespace(tid, target_ns)
            )

        menu.exec_(self.list_widget.mapToGlobal(pos))

    def _copy_task_to_namespace(self, task_id: str, target_namespace: str):
        try:
            orig = next((t for t in self.ctrl.fetch_tasks() if t.id == task_id), None)
            if not orig:
                return

            clone = Task(
                title=orig.title,
                description=orig.description,
                due_date=orig.due_date,
                update_date=None,
                category=orig.category,
                priority=orig.priority,
                frequency=orig.frequency,
                bcp=orig.bcp,
                tags=list(orig.tags),
                participants=list(orig.participants),
                namespace=target_namespace
            )

            self.ctrl.add_task(clone)
            logger.info(f"[TasksScreen] tarefa '{orig.title}' copiada para namespace '{target_namespace}'")

            self._update_namespaces()
            self.load_tasks()
            self.kanban.refresh()
            self.gamification.refresh()
            self.timeline.refresh()

            QMessageBox.information(
                self,
                "Copiar Tarefa",
                f"Tarefa copiada para o ciclo '{target_namespace}'."
            )
        except Exception as e:
            logger.error(f"[TasksScreen] erro ao copiar tarefa: {e}")
            QMessageBox.warning(self, "Erro", "Falha ao copiar a tarefa para outro ciclo.")

    def _attempt_change_status(self, task_id: str, new_status: str):
        task = next((t for t in self.ctrl.fetch_tasks() if t.id == task_id), None)
        if not task:
            return

        if new_status == "Concluídas" and task.status != "Concluídas":
            resp = QMessageBox.question(
                self,
                "Confirmar conclusão",
                "Marcar esta tarefa como concluída é irreversível. Deseja continuar?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            if resp != QMessageBox.Yes:
                return

        def ensure_date(val):
            if isinstance(val, date):
                return val
            if isinstance(val, str):
                try:
                    return datetime.fromisoformat(val).date()
                except Exception as e:
                    logger.error(f"[TasksScreen] erro ao converter data {val} erro: {e}")
                    return date.today()
            return date.today()

        try:
            task.status = new_status
            task.update_date = ensure_date(date.today())
            task.done   = (new_status == "Concluídas")
            task.xp     = calcular_xp_por_bcp(task.bcp) if task.done else 0
            self.ctrl.update_task(task)
        except Exception as e:
            logger.error(f"[TasksScreen] erro ao atualizar tarefa: {e}")
            QMessageBox.warning(self, "Erro", "Não foi possível alterar o status da tarefa.")
            return

        try:
            self.load_tasks()
            self.kanban.refresh()
            self.gamification.refresh()
            self.timeline.refresh()
        except Exception as e:
            logger.error(f"[TasksScreen] erro ao atualizar UI após mudança de status: {e}")
            QMessageBox.warning(self, "Erro", "Falha ao atualizar a interface após mudança de status.")
            self.close()


    def _change_task_status(self, task_id, status):
        try:
            tasks = self.ctrl.fetch_tasks()
            task = next((t for t in tasks if t.id == task_id), None)
            if task:
                task.status = status
                task.done = (status == "Concluídas")
                task.xp =  calcular_xp_por_bcp(task.bcp) if status == "Concluídas" else 0
                self.ctrl.update_task(task)
                self.load_tasks()
                self.kanban.refresh()

            self.gamification.refresh()
            self.timeline.refresh()
        except Exception as e:
            logger.error(f"[TasksScreen] erro ao alterar status via menu: {e}")

    def on_new(self):
        if self.namespace_filter.currentText() != "Atual":
            QMessageBox.warning(self, "Aviso", "Este ciclo não pode ser modificado.")
            return

        self.current = Task.new()
        self._populate_form(self.current)
        self.save_button.setEnabled(True)
        self.list_widget.clearSelection()
        self.delete_button.setEnabled(False)

    def on_select(self, item: QListWidgetItem):
        try:
            task_id = item.data(Qt.UserRole)
            all_tasks = self.ctrl.fetch_tasks()
            self.current = next((t for t in all_tasks if t.id == task_id), None)
            if not self.current:
                logger.warning(f"[TasksScreen] tarefa com ID {task_id} não encontrada")
                raise ValueError(f"Tarefa com ID {task_id} não encontrada")
            self._populate_form(self.current)
            self.save_button.setEnabled(True)
            self.delete_button.setEnabled(bool(self.current.id))
            logger.info(f"[TasksScreen] tarefa selecionada: {self.current.title}")
        except Exception as e:
            logger.error(f"[TasksScreen] erro ao selecionar tarefa: {e}")
            QMessageBox.warning(self, "Erro", "Falha ao carregar os dados da tarefa selecionada.")

    def _populate_form(self, task: Task):
        self.title_edit.setText(task.title)
        self.bcp_edit.setText(str(getattr(task, "bcp", "")))
        self.desc_edit.setPlainText(task.description)
        self.due_date.setDate(task.due_date)
        self.tags_edit.setText(",".join(task.tags))
        self.participants_edit.setText(",".join(task.participants))
        self.category_combo.setCurrentText(task.category or "Trabalho")
        self.priority_combo.setCurrentText(task.priority or "Média")
        self.frequency_combo.setCurrentText(task.frequency or "Nenhuma")

    def on_save(self):
        if self.current is None:
            QMessageBox.warning(self, "Aviso", "Nenhuma tarefa selecionada ou criada.")
            return

        if self.namespace_filter.currentText() != "Atual":
            QMessageBox.warning(self, "Aviso", "Este ciclo não pode ser modificado.")
            return

        self.current.title = self.title_edit.text()
        self.current.description = self.desc_edit.toPlainText()
        self.current.due_date = self.due_date.date().toPyDate()

        self.current.category = self.category_combo.currentText()
        self.current.priority = self.priority_combo.currentText()
        self.current.frequency = self.frequency_combo.currentText()
        self.current.bcp = int(self.bcp_edit.text() or 0)
        self.current.tags = [t.strip() for t in self.tags_edit.text().split(",") if t.strip()]
        self.current.participants = [p.strip() for p in self.participants_edit.text().split(",") if p.strip()]

        existing_tasks = self.ctrl.fetch_tasks()
        existing_ids = [t.id for t in existing_tasks]

        if self.current.id in existing_ids:
            self.ctrl.update_task(self.current)
        else:
            self.ctrl.add_task(self.current)

        self.load_tasks()
        QMessageBox.information(self, "Sucesso", "Tarefa salva!")

    def on_delete(self):
        if self.namespace_filter.currentText() != "Atual":
            QMessageBox.warning(self, "Aviso", "Este ciclo não pode ser modificado.")
            return

        if self.current and self.current.id:
            resp = QMessageBox.question(
                self,
                "Confirmar exclusão",
                f"Tem certeza que deseja excluir a tarefa '{self.current.title}'?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            if resp != QMessageBox.Yes:
                return

            self.ctrl.delete_task(self.current.id)
            QMessageBox.information(self, "Removido", "Tarefa excluída.")
            self.load_tasks()

    def delete_selected_tasks(self):
        items = self.list_widget.selectedItems()
        if not items:
            return

        if self.namespace_filter.currentText() != "Atual":
            QMessageBox.warning(self, "Aviso", "Este ciclo não pode ser modificado.")
            return

        msg = QMessageBox(self)
        msg.setWindowTitle("Confirmar exclusão")
        msg.setText(f"Excluir {len(items)} tarefa(s) selecionada(s)?")
        yes_btn = msg.addButton(QMessageBox.Yes)
        no_btn = msg.addButton(QMessageBox.No)
        msg.setDefaultButton(yes_btn)
        msg.setEscapeButton(no_btn)
        msg.exec_()
        if msg.clickedButton() != yes_btn:
            return

        for item in items:
            task_id = item.data(Qt.UserRole)
            self.ctrl.delete_task(task_id)
            self.list_widget.takeItem(self.list_widget.row(item))

        self.on_new()
        self.load_tasks()

    def on_ia(self):
        if self.namespace_filter.currentText() != "Atual":
            QMessageBox.warning(self, "Aviso", "Este ciclo não pode ser modificado.")
            return

        dlg = IAGenerationDialog(self)
        dlg.setWindowTitle("Gerar Tasks pela IA")
        dlg.setWindowIcon(qta.icon("fa5s.robot", color="orange"))
        dlg.instruction_edit.setPlaceholderText("Descreva o que você precisa automatizar em tasks…")
        dlg.resize(500, 500)
        dlg.instruction_edit.setFocus()
        QShortcut(QKeySequence(Qt.Key_Return), dlg, dlg.accept)
        QShortcut(QKeySequence(Qt.Key_Escape), dlg, dlg.reject)
        dlg.instruction_edit.setAcceptRichText(False)

        if dlg.exec_() != QDialog.Accepted or not dlg.instruction:
            return

        instr = dlg.instruction
        cat = dlg.category
        new_tasks = self.ctrl.generate_ia_tasks(instr)
        if not new_tasks:
            QMessageBox.warning(self, "IA", "Nenhuma task gerada pela IA.")
            return

        for t in new_tasks:
            t.category = cat

        sel_dlg = TaskSelectionDialog(new_tasks, self)
        if sel_dlg.exec_() != QDialog.Accepted:
            return

        for task in sel_dlg.selected_tasks():
            self.ctrl.add_task(task)
        QMessageBox.information(self, "IA", f"{len(sel_dlg.selected_tasks())} tarefas criadas.")
        self.load_tasks()

    def _handle_recurring(self, task: Task):
        try:
            freq = task.frequency
            if freq == "Diária":
                nxt = task.due_date + relativedelta(days=1)
            elif freq == "Semanal":
                nxt = task.due_date + relativedelta(weeks=1)
            elif freq == "Mensal":
                nxt = task.due_date + relativedelta(months=1)
            else:
                return

            new_t = Task(
                title=task.title,
                description=task.description,
                category=task.category,
                priority=task.priority,
                due_date=nxt,
                frequency=freq
            )
            self.ctrl.add_task(new_t)
            logger.info(f"[TasksScreen] criada instância recorrente: {new_t.title} p/ {nxt}")
        except Exception as e:
            logger.error(f"[TasksScreen] erro em _handle_recurring: {e}")

    def _update_namespaces(self):
        all_tasks = self.ctrl.fetch_tasks()
        namespaces = sorted({t.namespace for t in all_tasks})
        if "Atual" not in namespaces:
            namespaces.insert(0, "Atual")
        else:
            namespaces.remove("Atual")
            namespaces.insert(0, "Atual")
        self.namespace_filter.blockSignals(True)
        self.namespace_filter.clear()
        self.namespace_filter.addItems(namespaces)
        self.namespace_filter.blockSignals(False)

    def on_close_cycle(self):
        name, ok = QInputDialog.getText(
            self,
            "Fechar Ciclo",
            "Nome para este ciclo (ex: Sprint 1):"
        )
        if not ok or not name.strip():
            return
        name = name.strip()
        try:
            for t in self.ctrl.fetch_tasks():
                if t.namespace == "Atual":
                    t.namespace = name
                    self.ctrl.update_task(t)
            logger.info(f"[TasksScreen] ciclo 'Atual' renomeado para '{name}'")
        except Exception as e:
            logger.error(f"[TasksScreen] erro em on_close_cycle: {e}")
            QMessageBox.warning(self, "Erro", "Não foi possível encerrar o ciclo.")
            return

        self._update_namespaces()
        self.namespace_filter.setCurrentText("Atual")
        self.load_tasks()

    def showEvent(self, event):
        super().showEvent(event)
        if self._first_show:
            self._first_show = False
            try:
                cursor_pos = QCursor.pos()
                desktop = QApplication.desktop()
                screen_index = desktop.screenNumber(cursor_pos)
                geom = desktop.screenGeometry(screen_index)
                self.setGeometry(geom)
                self.setWindowState(self.windowState() | Qt.WindowMaximized)
            except Exception as e:
                logger.error(f"[TasksScreen] erro ao maximizar janela: {e}")

class IAGenerationDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Gerar Tasks pela IA")
        self.resize(400, 350)

        layout = QVBoxLayout(self)
        # 1) Combo de categoria
        self.category_combo = QComboBox()
        self.category_combo.addItems(["Trabalho", "Pessoal", "Estudo"])
        layout.addWidget(QLabel("Categoria:"))
        layout.addWidget(self.category_combo)

        # 2) Área de texto
        self.instruction_edit = QTextEdit()
        self.instruction_edit.setPlaceholderText("Descreva o que você precisa automatizar em tasks…")
        self.instruction_edit.setAcceptRichText(False)
        layout.addWidget(self.instruction_edit)

        btns = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btns.accepted.connect(self.accept)
        btns.rejected.connect(self.reject)
        layout.addWidget(btns)

    @property
    def instruction(self) -> str:
        return self.instruction_edit.toPlainText().strip()

    @property
    def category(self) -> str:
        return self.category_combo.currentText()


class TaskSelectionDialog(QDialog):
    def __init__(self, tasks: list[Task], parent=None):
        super().__init__(parent)
        self.setWindowTitle("Selecione as Tasks para Criar")
        self.resize(400, 300)
        layout = QVBoxLayout(self)
        self.list_widget = QListWidget()
        for t in tasks:
            item = QListWidgetItem(f"{t.title}  [{t.priority} – due {t.due_date.isoformat()}]")
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            item.setCheckState(Qt.Checked)
            # armazenar o objeto Task no próprio item
            item.setData(Qt.UserRole, t)
            layout.addWidget(self.list_widget)
            self.list_widget.addItem(item)
        btns = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btns.accepted.connect(self.accept)
        btns.rejected.connect(self.reject)
        layout.addWidget(btns)

    def selected_tasks(self) -> list[Task]:
        out = []
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            if item.checkState() == Qt.Checked:
                out.append(item.data(Qt.UserRole))
        return out