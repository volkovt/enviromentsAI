#!/usr/bin/env python3
import sys
import logging
from PyQt5.QtCore import QObject, Qt
from PyQt5.QtWidgets import QApplication, QSystemTrayIcon, QMenu, QAction
import qtawesome as qta

from presentation.components.tasks_screen import TasksScreen
from services.notification_manager import NotificationManager
from utils.utilities import get_style_sheet

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("[ApplicationManager]")


class ApplicationManager(QObject):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.app = QApplication(sys.argv)
        self.app.setQuitOnLastWindowClosed(False)
        self.app.setStyleSheet(get_style_sheet())

        self.tray_icon = QSystemTrayIcon(self.app)
        self.tray_icon.setIcon(qta.icon('fa5s.bell', color='white'))
        self.tray_icon.setToolTip("To-Do Dashboard")

        menu = QMenu()
        open_action = QAction("Abrir Tasks", self.app)
        open_action.triggered.connect(self.show_tasks)
        menu.addAction(open_action)

        exit_action = QAction("Sair", self.app)
        exit_action.triggered.connect(self.app.quit)
        menu.addAction(exit_action)

        self.tray_icon.setContextMenu(menu)
        self.tray_icon.show()

        self.notification_manager = NotificationManager(self.app)

        self.tasks_window = None
        self.show_tasks()
        logger.info("[ApplicationManager] To-Do Dashboard iniciado com sucesso!")

    def show_tasks(self):
        """
        Exibe ou esconde a janela de Tasks quando o usuário escolhe no menu.
        """
        try:
            if self.tasks_window and self.tasks_window.isVisible():
                logger.info("TasksScreen já está visível. Escondendo...")
                self.notification_manager.notify(
                    "To-Do Dashboard",
                    "TasksScreen já aberta!",
                    duration=5000
                )
            else:
                if not self.tasks_window:
                    logger.info("Criando instância de TasksScreen.")
                    self.tasks_window = TasksScreen()
                logger.info("Exibindo TasksScreen.")
                self.tasks_window.show()
                self.tasks_window.raise_()
                self.tasks_window.activateWindow()
        except Exception as e:
            logger.error(f"Erro ao exibir TasksScreen: {e}")
            if self.tasks_window:
                self.tasks_window.close()
                self.tasks_window = None

    def run(self):
        sys.exit(self.app.exec_())


if __name__ == '__main__':
    manager = ApplicationManager()
    manager.run()
