#!/usr/bin/env python3
import sys
import logging

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication, QWidget, QMainWindow, QVBoxLayout

from controller.environment_controller import EnvironmentController
from presentation.components.environment_screen import EnvironmentWidget
from presentation.components.placeholder_environment_suggestion import (
    PlaceholderSuggestionProvider,
    PlaceholderLineEdit,
)
from services.notification_manager import NotificationManager
from services.variable_service import VariableService
from utils.utilities import get_style_sheet

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("[ApplicationManager]")

class ApplicationManager:
    def __init__(self):
        try:
            self.app = QApplication(sys.argv)
            self.app.setQuitOnLastWindowClosed(False)
            self.app.setStyleSheet(get_style_sheet())

            self.notification_manager = NotificationManager(self.app)

            self.window = QMainWindow()
            self.window.setWindowTitle("Environment Manager")
            self.window.setGeometry(500, 200, 800, 600)

            central = QWidget()
            v_layout = QVBoxLayout(central)

            var_svc = VariableService()
            provider = PlaceholderSuggestionProvider(var_svc)
            self.url_le = PlaceholderLineEdit(provider)
            v_layout.addWidget(self.url_le)

            self.view = EnvironmentWidget()
            self.controller = EnvironmentController(self.view)
            v_layout.addWidget(self.view)

            self.window.setCentralWidget(central)
            self.window.show()

            logger.info("Aplicação iniciada com Environment Screen.")
        except Exception as e:
            logger.error(f"[ApplicationManager] erro ao iniciar a aplicação: {e}")

    def run(self):
        sys.exit(self.app.exec_())


if __name__ == "__main__":
    manager = ApplicationManager()
    manager.run()
