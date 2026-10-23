"""Small cost/rate card and cancellable collector worker."""
import threading
import time
from PySide6.QtCore import QThread, Signal, QTimer, Qt
from PySide6.QtWidgets import QWidget, QLabel, QVBoxLayout, QHBoxLayout
from usage_metrics import Collector, presentation
from typography import FONT_CSS


class MetricsThread(QThread):
    ready = Signal(object)

    def __init__(self, state, parent=None):
        super().__init__(parent)
        self.stop = threading.Event()
        self.wake = threading.Event()
        self.state = state

    def run(self):
        previous = None
        try:
            from codex_connection import data_home
            collector = Collector(self.state, self.stop.is_set, codex_home=data_home())
        except Exception:
            self.ready.emit(dict(error=True))
            return
        while not self.stop.is_set():
            self.wake.clear()
            started = time.monotonic()
            try:
                previous = collector.poll()
                value = previous
            except Exception:
                value = dict(previous or {}, error=True)
            if not self.stop.is_set():
                self.ready.emit(value)
            self.wake.wait(max(1, 10 - (time.monotonic() - started)))


class UsageMetrics(QWidget):
    HEIGHT = 67

    def __init__(self, snapshot=None, parent=None):
        super().__init__(parent)
        self.setObjectName('usage_metrics')
        self.setFixedHeight(self.HEIGHT)
        self.setStyleSheet('QWidget#usage_metrics{background:#f5f2f7;border-radius:7px;}')
        self.snapshot = snapshot
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 4, 8, 3)
        layout.setSpacing(0)
        row = QHBoxLayout()
        row.setSpacing(8)
        self.titles, self.values = [], []
        for _ in range(2):
            column = QVBoxLayout()
            column.setSpacing(0)
            title, value = QLabel(), QLabel()
            title.setStyleSheet(FONT_CSS + 'font-size:10px;color:#857c91;')
            value.setStyleSheet(FONT_CSS + 'font-size:13px;font-weight:600;color:#393343;')
            column.addWidget(title)
            column.addWidget(value)
            row.addLayout(column, 1)
            self.titles.append(title)
            self.values.append(value)
        layout.addLayout(row)
        self.note = QLabel()
        self.note.setStyleSheet(FONT_CSS + 'font-size:9px;color:#857c91;')
        layout.addWidget(self.note)
        self.timer = QTimer(self)
        self.timer.setInterval(10000)
        self.timer.timeout.connect(self.refresh)
        self.refresh()

    def set_snapshot(self, snapshot):
        self.snapshot = snapshot
        self.refresh()

    def refresh(self):
        data = presentation(self.snapshot)
        self.titles[0].setText('今日估算 · USD')
        self.titles[1].setText(data['rate_title'])
        self.values[0].setText(data['cost'])
        self.values[1].setText(data['rate'])
        self.note.setText(data['note'])
        self.setToolTip(data['tooltip'])
        self.setAccessibleName('今日估算 ' + data['cost'] + '；' + data['rate_title'] + ' ' + data['rate'])
        self.setAccessibleDescription(data['tooltip'])

    def showEvent(self, event):
        super().showEvent(event)
        self.refresh()
        self.timer.start()

    def hideEvent(self, event):
        self.timer.stop()
        super().hideEvent(event)
