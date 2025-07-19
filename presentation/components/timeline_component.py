from PyQt5.QtWidgets import (
    QWidget, QGraphicsView, QGraphicsScene,
    QVBoxLayout, QGraphicsRectItem, QGraphicsSimpleTextItem,
    QHBoxLayout, QLabel, QDateEdit, QPushButton, QDialog, QTextEdit, QDialogButtonBox
)
from PyQt5.QtCore import Qt, QRectF, QPointF
from PyQt5.QtGui import QBrush, QColor, QPen, QPainter
from datetime import date, timedelta
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("[TimelineWidget]")

class TimelineWidget(QWidget):
    def __init__(self, tasks_controller, parent=None):
        super().__init__(parent)
        self.namespace = "Atual"
        self.ctrl = tasks_controller
        self.start_date = date.today() - timedelta(days=10)
        self.end_date   = date.today()
        self._build_ui()
        self.refresh()

    def _build_ui(self):
        layout = QVBoxLayout(self)

        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("De:"))
        self.date_from = QDateEdit(self.start_date, calendarPopup=True)
        filter_layout.addWidget(self.date_from)
        filter_layout.addWidget(QLabel("Até:"))
        self.date_to   = QDateEdit(self.end_date, calendarPopup=True)
        filter_layout.addWidget(self.date_to)
        btn_apply = QPushButton("Aplicar")
        btn_apply.clicked.connect(self.refresh)
        filter_layout.addWidget(btn_apply)
        layout.addLayout(filter_layout)

        self.view  = QGraphicsView()
        self.view.setRenderHints(self.view.renderHints() | QPainter.Antialiasing)
        self.scene = QGraphicsScene()
        self.view.setScene(self.scene)

        self.view.setDragMode(QGraphicsView.ScrollHandDrag)
        layout.addWidget(self.view)

        zoom_layout = QHBoxLayout()
        btn_zoom_in  = QPushButton("+")
        btn_zoom_out = QPushButton("–")
        btn_zoom_in.clicked.connect(lambda: self.view.scale(1.2,1))
        btn_zoom_out.clicked.connect(lambda: self.view.scale(1/1.2,1))
        zoom_layout.addWidget(btn_zoom_in)
        zoom_layout.addWidget(btn_zoom_out)
        layout.addLayout(zoom_layout)

    def set_namespace(self, ns: str):
        """Define o namespace ativo e atualiza a view."""
        self.namespace = ns
        self.refresh()

    def refresh(self):
        try:
            self.scene.clear()
            df = self.date_from.date().toPyDate()
            dt = self.date_to.date().toPyDate()
            days = (dt - df).days or 1
            for i in range(days+1):
                x = i * 100
                pen = QPen(QColor('#DDD'))
                self.scene.addLine(x, 0, x, 500, pen)
                lbl = QGraphicsSimpleTextItem((df + timedelta(days=i)).strftime('%d/%m'))
                lbl.setPos(x+2, 0)
                self.scene.addItem(lbl)
            idx_today = (date.today() - df).days
            if 0 <= idx_today <= days:
                pen = QPen(QColor('red'), 2)
                x0 = idx_today * 100
                self.scene.addLine(x0, 0, x0, 500, pen)

            tasks = [
                t for t in self.ctrl.fetch_tasks()
                if t.namespace == self.namespace
                and df <= t.done_date <= dt
            ]
            lanes = {}
            lane_h = 50
            for t in tasks:
                lane = t.category or 'Outros'
                if lane not in lanes:
                    lanes[lane] = len(lanes)
                y = 30 + lanes[lane] * lane_h

                x = (t.done_date - df).days * 100
                width = 80
                color = {'Alta':'#F88','Média':'#FEA','Baixa':'#8F8'}.get(t.priority, '#AAA')
                rect = QGraphicsRectItem(QRectF(x, y, width, 20))
                rect.setBrush(QBrush(QColor(color)))
                rect.setPen(QPen(Qt.NoPen))
                rect.setToolTip(f"{t.title}\n{t.description}")
                rect.setData(0, t.id)
                self.scene.addItem(rect)

                txt = QGraphicsSimpleTextItem(t.title)
                txt.setPos(x+2, y+2)
                self.scene.addItem(txt)

                rect.mousePressEvent = lambda ev, tid=t.id: self._show_task_detail(tid)

            self.scene.setSceneRect(0,0, (days+1)*100, (len(lanes)+1)*lane_h + 20)
        except Exception as e:
            logger.error(f"[TimelineWidget] erro em refresh: {e}")

    def _show_task_detail(self, task_id):
        t = next((x for x in [t for t in self.ctrl.fetch_tasks() if t.namespace == self.namespace] if x.id==task_id), None)
        if not t:
            return
        dlg = QDialog(self)
        dlg.setWindowTitle(t.title)
        v = QVBoxLayout(dlg)
        info = QTextEdit()
        info.setReadOnly(True)
        info.setPlainText(
            f"Título: {t.title}\n"
            f"Categoria: {t.category}\n"
            f"Prioridade: {t.priority}\n"
            f"Vencimento: {t.due_date}\n"
            f"Completado: {t.done_date}\n\n"
            f"{t.description}"
        )
        v.addWidget(info)
        btns = QDialogButtonBox(QDialogButtonBox.Ok)
        btns.accepted.connect(dlg.accept)
        v.addWidget(btns)
        dlg.exec_()
