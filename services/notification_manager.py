import collections
from PyQt5.QtCore import QObject
from presentation.components.toast.toast_notification import ToastNotification

class NotificationManager(QObject):
    """
    Gerencia uma fila de notificações do tipo ToastNotification.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self._queue = collections.deque()
        self._current = None

    def notify(self, title: str, message: str, duration: int = 1000, icon_path: str = None):
        """
        Adiciona uma notificação à fila e, se nada estiver sendo exibido,
        dispara imediatamente.
        """
        self._queue.append((title, message, duration, icon_path))
        if not self._current:
            self._show_next()

    def _show_next(self):
        if not self._queue:
            return

        title, message, duration, icon_path = self._queue.popleft()
        toast = ToastNotification("Digibot", icon_path=icon_path)
        self._current = toast

        toast._timer.timeout.connect(self._on_toast_closed)

        toast.show_notification(title, message, duration)

    def _on_toast_closed(self):
        """
        Chamado quando o toast atual fecha: libera e exibe o próximo da fila.
        """
        if self._current:
            try:
                self._current._timer.timeout.disconnect(self._on_toast_closed)
            except Exception:
                pass
            self._current = None

        if self._queue:
            self._show_next()