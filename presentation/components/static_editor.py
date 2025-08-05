from PyQt5.QtWidgets import QWidget, QVBoxLayout, QTextEdit
from PyQt5.QtCore import pyqtSignal
import logging

class StaticEditor(QWidget):
    """
    Editor de valor estático para variáveis de ambiente.
    Sobrescreve o método show para receber um valor e exibir o widget corretamente.
    """
    valueChanged = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.txt = QTextEdit()
        self.txt.textChanged.connect(
            lambda: self.valueChanged.emit(self.txt.toPlainText())
        )
        layout = QVBoxLayout(self)
        layout.addWidget(self.txt)

    def show(self, value: str = None):
        """
        Se um valor for passado, carrega-o no editor antes de exibir.
        """
        try:
            if value is not None:
                self.txt.setPlainText(value)
            # Chama explicitamente o show do QWidget
            QWidget.show(self)
        except Exception as e:
            logging.getLogger('StaticEditor').error(
                f"Erro ao exibir valor estático: {e}"
            )
