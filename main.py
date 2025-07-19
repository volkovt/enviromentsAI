#!/usr/bin/env python3
import sys
import logging

import docker
from PyQt5.QtCore import QObject
from PyQt5.QtWidgets import QApplication, QSystemTrayIcon, QMenu, QAction
import qtawesome as qta

from presentation.components.kafka.kafka_screen import KafkaScreen
from presentation.components.localstack.localstack_screen import LocalStackScreen
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

        self.screens = {}

        self.tray_icon = QSystemTrayIcon(self.app)
        self.tray_icon.setIcon(qta.icon('fa5s.bell', color='white'))
        self.tray_icon.setToolTip("DockerAI - Gerenciador de containers AI")

        menu = QMenu()
        kafka_action = QAction("Kafka", self.app)
        kafka_action.triggered.connect(lambda: self.open_screen("kafka"))
        menu.addAction(kafka_action)

        localstack_action = QAction("Localstack", self.app)
        localstack_action.triggered.connect(lambda: self.open_screen("localstack"))
        menu.addAction(localstack_action)

        exit_action = QAction("Sair", self.app)
        exit_action.triggered.connect(self.app.quit)
        menu.addAction(exit_action)

        self.tray_icon.setContextMenu(menu)
        self.tray_icon.show()

        self.notification_manager = NotificationManager(self.app)

        # Já abre as duas telas no startup, se quiser
        # self.open_screen("localstack")
        self.open_screen("kafka")

        logger.info("[ApplicationManager] DockerAI iniciado com sucesso!")

    def _check_docker_daemon(self):
        try:
            client = docker.from_env()
            client.ping()
            return True
        except docker.errors.DockerException as e:
            logger.error(f"Erro Docker daemon: {e}")
            return False

    def open_screen(self, key: str):
        """
        Exibe a janela correspondente sem fechar as outras.
        """
        if not self._check_docker_daemon():
            self.notification_manager.notify(
                "Erro",
                "Docker daemon não está rodando. Por favor, inicie o Docker.",
                duration=5000
            )
            return

        try:
            if key in self.screens:
                try:
                    if self.screens[key].isVisible() or True:
                        self.screens[key].show()
                        self.screens[key].raise_()
                        self.screens[key].activateWindow()
                        return
                except RuntimeError:
                    del self.screens[key]

            if key == "localstack":
                logger.info("Criando instância de LocalStackScreen.")
                self.screens[key] = LocalStackScreen()
            elif key == "kafka":
                logger.info("Criando instância de KafkaScreen.")
                self.screens[key] = KafkaScreen()
            else:
                logger.error(f"Chave desconhecida: {key}")
                return

            self.screens[key].show()
            self.screens[key].raise_()
            self.screens[key].activateWindow()

        except Exception as e:
            logger.error(f"Erro ao exibir {key}: {e}")
            self.notification_manager.notify(
                "Erro",
                f"Falha ao exibir {key}: {e}",
                duration=5000
            )
            if key in self.screens:
                try:
                    self.screens[key].close()
                except Exception as close_e:
                    logger.error(f"Erro ao fechar {key}: {close_e}")
                del self.screens[key]

    def run(self):
        sys.exit(self.app.exec_())


if __name__ == '__main__':
    manager = ApplicationManager()
    manager.run()
