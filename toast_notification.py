import logging

from PyQt5.QtWidgets import QWidget, QLabel, QVBoxLayout, QHBoxLayout, QGraphicsDropShadowEffect, QPushButton, QFrame, \
    QSizePolicy
from PyQt5.QtGui import QIcon, QColor
from PyQt5.QtCore import Qt, QTimer
import qtawesome as qta

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ToastNotification(QWidget):
    def __init__(self, app_name, icon_path=None, parent=None):
        super().__init__(parent)
        self.app_name = app_name
        self.icon_path = icon_path
        #self.setAttribute(Qt.WA_TranslucentBackground)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)

        self.setStyleSheet("""
               #container {
                   border-radius: 12px;
                   border: 1px solid #3c3c3c;
               }
               #header {
                   border-top-left-radius: 12px;
                   border-top-right-radius: 12px;
               }
               #body {
                   border-bottom-left-radius: 12px;
                   border-bottom-right-radius: 12px;
               }
               #headerTitle {
                   font-size: 11pt;
               }
               #closeButton {
                   font-size: 12pt;
                   border: none;
                   padding: 0;
                   min-width: 24px;
               }
               #bodyTitle {
                   font-weight: bold;
                   font-size: 12pt;
               }
               #bodyMessage {
                   font-size: 11pt;
               }
           """)

        self.container = QWidget(self)
        self.container.setObjectName("container")
        layout = QVBoxLayout(self.container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        header = QWidget(self.container)
        header.setObjectName("header")
        header_layout = QHBoxLayout(header)
        header_layout.setAlignment(Qt.AlignLeft)

        icon = qta.icon("fa5s.robot", color="orange")
        top_icon = QLabel(header)
        pixmap = icon.pixmap(24, 24)
        top_icon.setPixmap(pixmap)
        header_layout.addWidget(top_icon)

        self.lbl_body_title = QLabel(app_name)
        self.lbl_body_title.setObjectName("headerTitle")
        header_layout.addWidget(self.lbl_body_title)
        header_layout.addStretch()

        close_btn = QPushButton("✕", header)
        close_btn.setObjectName("closeButton")
        close_btn.setToolTip("Fechar")
        close_btn.setFlat(True)
        close_btn.clicked.connect(self.close)
        header_layout.addWidget(close_btn)

        layout.addWidget(header)

        separator = QFrame(self.container)
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        separator.setLineWidth(1)
        separator.setStyleSheet("background-color: #555555;")
        separator.setMaximumHeight(1)

        layout.addWidget(separator)

        body = QWidget(self.container)
        body.setObjectName("body")
        body_layout = QHBoxLayout(body)
        body_layout.setContentsMargins(10, 8, 10, 10)
        body_layout.setSpacing(8)

        if icon_path:
            info_icon = QLabel(body)
            pix2 = QIcon(icon_path).pixmap(24, 24)
            info_icon.setPixmap(pix2)
            body_layout.addWidget(info_icon, alignment=Qt.AlignTop)

        text_layout = QVBoxLayout()
        text_layout.setContentsMargins(0, 0, 0, 0)
        text_layout.setSpacing(2)

        body_message_layout = QHBoxLayout()
        body_message_layout.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        body_message_layout.setContentsMargins(10, 0, 40, 0)

        icon = qta.icon("fa5s.info-circle", color="white")
        information_ic_label = QLabel()
        pixmap = icon.pixmap(80, 80)
        information_ic_label.setPixmap(pixmap)
        body_message_layout.addWidget(information_ic_label)
        body_message_layout.setSpacing(30)

        self.lbl_msg = QLabel(body)
        self.lbl_msg.setObjectName("bodyMessage")
        self.lbl_msg.setWordWrap(True)
        body_message_layout.addWidget(self.lbl_msg)

        text_layout.addLayout(body_message_layout)

        body_layout.addLayout(text_layout)
        layout.addWidget(body)

        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(20)
        shadow.setOffset(0, 4)
        shadow.setColor(QColor(0, 0, 0, 150))
        self.container.setGraphicsEffect(shadow)

        self.container.setMinimumWidth(250)
        self.container.setMinimumHeight(250)
        self.container.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.timeout.connect(self.close)

        self.hide()

        self.adjustSize()
        self.container.resize(self.container.sizeHint())
        self.resize(self.container.size())

    def show_notification(self, title: str, message: str, duration: int = 1000):
        """
        Exibe a notificação com título e mensagem, por duração em ms.
        """
        logger.info(f"Exibindo notificação: {title} - {message}")
        self.lbl_body_title.setText(title)
        self.lbl_msg.setText(message)
        self.show()
        self.adjustSize()
        self.container.resize(self.container.sizeHint())
        self.resize(self.container.size())
        self._position()
        self._timer.start(duration)

    def _position(self):
        screen = self.screen().availableGeometry()
        x = screen.right() - self.width() - 20
        y = screen.bottom() - self.height() - 20
        self.move(x, y)

