# presentation/views/components/tasks/gamification_widget.py
import logging
from collections import Counter
from datetime import date, timedelta

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QProgressBar, QHBoxLayout
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from matplotlib.figure import Figure

from interface.task import Task

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("[TasksScreen]")

import qtawesome as qta

class GamificationWidget(QWidget):
    def __init__(self, tasks_controller, parent=None):
        super().__init__(parent)
        self.namespace = "Atual"
        self.ctrl = tasks_controller
        self._build_ui()
        self.refresh()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        layout_top = QVBoxLayout()
        layout_top.setAlignment(Qt.AlignTop)
        layout_top.addWidget(QLabel("🏆 Gamificação & Metas"))
        layout.addLayout(layout_top)

        self.figure = Figure()
        self.canvas = FigureCanvasQTAgg(self.figure)
        layout_top.addWidget(self.canvas)

        self.lbl_points = QLabel()
        self.lbl_level = QLabel()
        self.level_bar = QProgressBar()
        self.lbl_streak = QLabel()
        self.badge_layout = QHBoxLayout()
        self.badge_layout.setAlignment(Qt.AlignLeft)
        self.badge_layout.setSpacing(10)
        self.badge_layout.setContentsMargins(0, 0, 0, 0)
        self.lbl_daily = QLabel()
        layout_top.addWidget(self.lbl_points)
        layout_top.addWidget(self.lbl_level)
        layout_top.addWidget(self.level_bar)
        layout_top.addWidget(self.lbl_streak)
        layout_top.addWidget(self.lbl_daily)
        layout_top.addLayout(self.badge_layout)

        self.progress   = QProgressBar()
        layout.addWidget(self.progress, alignment=Qt.AlignBottom)

    def set_namespace(self, ns: str):
        """Define o namespace ativo e atualiza a view."""
        self.namespace = ns
        self.refresh()

    def refresh(self):
        try:
            tasks: list[Task] = [t for t in self.ctrl.fetch_tasks() if t.namespace == self.namespace]
            points = sum(t.xp for t in tasks if t.status == "Concluídas")
            total  = len(tasks)
            self.lbl_points.setText(f"Pontos: {points}")
            self.progress.setMaximum(total or 1)
            self.progress.setValue(sum(1 for t in tasks if t.status == "Concluídas"))

            self._plot_xp_evolution()
            self._update_level(points)
            self._update_streak()
            self._update_badges()
            self._update_daily_challenge()

        except Exception as e:
            logger.error(f"[GamificationWidget] erro em refresh: {e}")

    def _plot_xp_evolution(self):
        try:
            self.figure.clear()

            tasks = [t for t in self.ctrl.fetch_tasks() if t.namespace == self.namespace]
            today = date.today()
            last7 = [today - timedelta(days=i) for i in range(6, -1, -1)]
            dates = last7
            values = [
                sum(t.xp for t in tasks if t.status == "Concluídas" and t.done_date == d)
                for d in dates
            ]

            ax = self.figure.subplots()
            ax.clear()
            ax.plot(dates, values)
            ax.set_title("XP Ganho (últimos 7 dias)")
            ax.set_xlabel("Data")
            ax.set_ylabel("XP")
            xticks = [dates[i] for i in range(0, len(dates), 2)]
            ax.set_xticks(xticks)
            ax.set_xticklabels([d.strftime("%d/%m/%Y") for d in xticks], rotation=15, ha="right")
            self.canvas.draw()
        except Exception as e:
            logger.error(f"[GamificationWidget] erro em _plot_xp_evolution: {e}")

    def _update_level(self, points):
        try:
            level = points // 100
            progress = points - (level * 100)

            self.lbl_level.setText(f"Nível: {level}")
            self.level_bar.setMaximum(100)
            self.level_bar.setValue(progress)
        except Exception as e:
            logger.error(f"[GamificationWidget] erro em _update_level: {e}")

    def _update_streak(self):
        try:
            tasks = [t for t in self.ctrl.fetch_tasks() if t.namespace == self.namespace]
            today = date.today()
            streak = 0
            d = today
            while True:
                if any(t.status == "Concluídas" and t.done_date == d for t in tasks):
                    streak += 1
                    d -= timedelta(days=1)
                else:
                    break
            self.lbl_streak.setText(f"Streak atual: {streak} dia(s)")
        except Exception as e:
            logger.error(f"[GamificationWidget] erro em _update_streak: {e}")

    def _update_daily_challenge(self):
        try:
            goal = 2
            tasks = [t for t in self.ctrl.fetch_tasks() if t.namespace == self.namespace]
            today = date.today()
            done_today = sum(1 for t in tasks if t.status == "Concluídas" and t.done_date == today)
            self.lbl_daily.setText(f"Desafio de hoje: {done_today}/{goal}")
        except Exception as e:
            logger.error(f"[GamificationWidget] erro em _update_daily_challenge: {e}")

    def _update_badges(self):
        try:
            for i in reversed(range(self.badge_layout.count())):
                self.badge_layout.itemAt(i).widget().deleteLater()

            tasks = [t for t in self.ctrl.fetch_tasks() if t.namespace == self.namespace]
            today = date.today()
            start_week = today - timedelta(days=today.weekday())
            end_week = start_week + timedelta(days=6)
            completed = sum(
                1 for t in tasks
                if t.status == "Concluídas" and start_week <= t.done_date <= end_week
            )
            badges = []
            badge_info = [
                ("fa5s.medal", 3, "Complete 3 tarefas na semana para ganhar esta medalha"),
                ("fa5s.award", 10, "Complete 5 tarefas na semana para ganhar esta medalha"),
                ("fa5s.fire", 10, "Mantenha um streak de 10 dias para ganhar esta medalha"),
            ]
            for icon_name, min_tasks, tooltip in badge_info:
                if (icon_name == "fa5s.fire" and int(self.lbl_streak.text().split()[2]) >= min_tasks) or \
                        (icon_name != "fa5s.fire" and completed >= min_tasks):
                    lbl = QLabel()
                    lbl.setPixmap(qta.icon(icon_name, color="gold").pixmap(32, 32))
                    lbl.setToolTip(tooltip)
                    self.badge_layout.addWidget(lbl)
        except Exception as e:
            logger.error(f"[GamificationWidget] erro em _update_badges: {e}")