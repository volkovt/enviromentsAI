# presentation/views/components/tasks/performance_widget.py

from PyQt5.QtWidgets import QWidget, QVBoxLayout
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
from matplotlib.figure import Figure
from collections import Counter
from datetime import date, timedelta


class PerformanceWidget(QWidget):
    def __init__(self, tasks_controller):
        super().__init__()
        self.ctrl = tasks_controller
        self._build_ui()
        self.plot_stats()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        self.figure = Figure()
        self.canvas = FigureCanvasQTAgg(self.figure)
        layout.addWidget(self.canvas)

    def plot_stats(self, period="dia"):
        # coleta e filtra apenas concluídas
        tasks = [t for t in self.ctrl.fetch_tasks() if t.done]
        if period == "dia":
            keys = [t.due_date for t in tasks]
        else:  # semanal
            keys = [d - timedelta(days=d.weekday()) for d in (t.due_date for t in tasks)]

        counts = Counter(keys)
        dates = sorted(counts.keys())
        values = [counts[d] for d in dates]

        ax = self.figure.subplots()
        ax.clear()
        ax.plot(dates, values)
        ax.set_title("Tarefas Concluídas por " + ("Dia" if period=="dia" else "Semana"))
        ax.set_xlabel("Data")
        ax.set_ylabel("Quantidade")
        self.canvas.draw()
