import logging

from PyQt5.QtGui import QCursor
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QApplication
from PyQt5.QtCore import Qt

from controller.kafka.kafka_controller import KafkaController
from presentation.components.kafka.kafka_component import KafkaComponent

logger = logging.getLogger("[ApplicationManager]")

class KafkaScreen(QWidget):
    def __init__(self, port: int = 9092):
        super().__init__()
        self.setBaseSize(800, 600)

        self._first_show = True
        self.setWindowTitle("Gerenciador Kafka")

        self.port = port
        self.controller = KafkaController(lambda: self.port)

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignTop)

        self.kafka_component = KafkaComponent(self.controller, lambda: self.port)
        layout.addWidget(self.kafka_component)

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