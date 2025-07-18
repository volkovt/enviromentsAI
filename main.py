#!/usr/bin/env python3
import sys
import keyboard
from PyQt5.QtCore import QTimer, QObject
from PyQt5.QtWidgets import QApplication, QSystemTrayIcon, QMenu, QAction
from PyQt5.QtGui import QIcon
from notification_manager import NotificationManager
from utilities import get_style_sheet

import qtawesome as qta

class GlobalHotkeyNotifier(QObject):
    def _show_notification(self):
        self.manager.notify(
            title="Atalho Pressionado",
            message="Você pressionou Ctrl+K globalmente!",
            duration=2000,
            icon_path=None
        )

    def on_hotkey(self):
        QTimer.singleShot(0, self._show_notification)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        QApplication.setQuitOnLastWindowClosed(False)
        self.app = QApplication(sys.argv)
        self.app.setStyleSheet(get_style_sheet())

        self.tray_icon = QSystemTrayIcon(self.app)
        self.tray_icon.setIcon(qta.icon('fa5s.bell', color='white'))
        self.tray_icon.setToolTip("Hotkey AI – pressione Ctrl+K para notificar")

        menu = QMenu()
        exit_action = QAction("Sair", self.app)
        exit_action.triggered.connect(self.app.quit)
        menu.addAction(exit_action)
        self.tray_icon.setContextMenu(menu)
        self.tray_icon.show()

        self.manager = NotificationManager(parent=self.app)
        self.manager.notify(
            title="Hotkey AI",
            message="Hotkey AI iniciado!",
            duration=3000,
            icon_path=None
        )

        keyboard.add_hotkey('ctrl+k', self.on_hotkey)
        print("[GlobalHotkeyNotifier] Ctrl+K registrado para notificação.")

    def run(self):
        sys.exit(self.app.exec_())


if __name__ == '__main__':
    notifier = GlobalHotkeyNotifier()
    notifier.run()
