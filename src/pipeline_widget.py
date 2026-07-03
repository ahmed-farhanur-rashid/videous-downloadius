"""The pipeline strip: Fetch -> Convert -> Save, rendered as a single track.

This is both the status display and the progress bar - one element, two jobs,
because the download genuinely is a 3-stage pipeline and a generic QProgressBar
would hide that.
"""
from PySide6.QtCore import Qt, QRectF
from PySide6.QtGui import QPainter, QPen, QColor, QFont
from PySide6.QtWidgets import QWidget

STAGES = ["FETCH", "CONVERT", "SAVE"]


class PipelineStrip(QWidget):
    def __init__(self, tokens: dict, parent=None):
        super().__init__(parent)
        self.tokens = tokens
        self.active_stage = -1   # -1 = idle, 0/1/2 = current stage, 3 = done
        self.stage_progress = 0.0  # 0..1 progress within active stage
        self.errored = False
        self.setMinimumHeight(64)

    def set_tokens(self, tokens: dict):
        self.tokens = tokens
        self.update()

    def set_state(self, active_stage: int, stage_progress: float = 0.0, errored: bool = False):
        self.active_stage = active_stage
        self.stage_progress = max(0.0, min(1.0, stage_progress))
        self.errored = errored
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        t = self.tokens
        w, h = self.width(), self.height()
        n = len(STAGES)
        node_r = 7
        track_y = h // 2 - 10
        margin = 30
        usable = w - 2 * margin
        step = usable / (n - 1)

        base_color = QColor(t["border"])
        accent = QColor(t["error"] if self.errored else t["accent"])

        # background track
        pen = QPen(base_color, 3)
        p.setPen(pen)
        p.drawLine(margin, track_y, w - margin, track_y)

        # filled portion
        if self.active_stage >= 0:
            filled_stages = min(self.active_stage, n - 1)
            filled_x = margin + step * filled_stages + step * (self.stage_progress if self.active_stage < n else 0)
            filled_x = min(filled_x, w - margin)
            if self.active_stage >= n:  # fully done
                filled_x = w - margin
            pen = QPen(accent, 3)
            p.setPen(pen)
            p.drawLine(margin, track_y, int(filled_x), track_y)

        font = QFont("JetBrains Mono", 9)
        p.setFont(font)

        for i, label in enumerate(STAGES):
            cx = margin + step * i
            done = self.active_stage > i or self.active_stage >= n
            current = self.active_stage == i
            color = accent if (done or current) else base_color
            p.setBrush(color)
            p.setPen(Qt.NoPen)
            p.drawEllipse(int(cx - node_r), track_y - node_r, node_r * 2, node_r * 2)

            p.setPen(QColor(t["text"]) if (done or current) else QColor(t["text_dim"]))
            rect = QRectF(cx - 50, track_y + 14, 100, 20)
            p.drawText(rect, Qt.AlignHCenter | Qt.AlignTop, label)
