"""Theme tokens -> QSS. Two palettes; 'system' resolves to one of them at runtime."""
from PySide6.QtGui import QPalette
from PySide6.QtWidgets import QApplication

DARK = {
    "bg": "#0F1115",
    "panel": "#171A21",
    "panel_alt": "#1D212B",
    "text": "#E8E6E1",
    "text_dim": "#8A8F98",
    "accent": "#5EEAD4",
    "accent_dim": "#2DD4BF33",
    "border": "#272B35",
    "error": "#F87171",
}

LIGHT = {
    "bg": "#F7F6F3",
    "panel": "#FFFFFF",
    "panel_alt": "#F0EEE9",
    "text": "#1C1E22",
    "text_dim": "#6B6F76",
    "accent": "#0D9488",
    "accent_dim": "#0D948822",
    "border": "#DEDBD3",
    "error": "#DC2626",
}


def resolve_system_theme() -> str:
    """Best-effort OS theme detection via Qt's own palette (no extra dep)."""
    app = QApplication.instance()
    if app is None:
        return "dark"
    window_color = app.palette().color(QPalette.Window)
    # Simple luminance check: dark window color => dark OS theme.
    luminance = 0.299 * window_color.red() + 0.587 * window_color.green() + 0.114 * window_color.blue()
    return "dark" if luminance < 128 else "light"


def tokens_for(theme_name: str) -> dict:
    if theme_name == "system":
        theme_name = resolve_system_theme()
    return DARK if theme_name == "dark" else LIGHT


def build_qss(theme_name: str) -> str:
    t = tokens_for(theme_name)
    return f"""
    QWidget {{
        background: {t['bg']};
        color: {t['text']};
        font-family: -apple-system, "Segoe UI", "Ubuntu", sans-serif;
        font-size: 13px;
    }}
    QLabel#eyebrow {{
        color: {t['text_dim']};
        font-family: "JetBrains Mono", "Consolas", monospace;
        font-size: 11px;
        letter-spacing: 2px;
    }}
    QLabel#title {{
        font-family: "JetBrains Mono", "Consolas", monospace;
        font-size: 20px;
        font-weight: 600;
        color: {t['text']};
    }}
    QLineEdit {{
        background: {t['panel']};
        border: 1px solid {t['border']};
        border-radius: 6px;
        padding: 10px 12px;
        font-family: "JetBrains Mono", "Consolas", monospace;
        font-size: 13px;
        color: {t['text']};
        selection-background-color: {t['accent_dim']};
    }}
    QLineEdit:focus {{
        border: 1px solid {t['accent']};
    }}
    QComboBox {{
        background: {t['panel']};
        border: 1px solid {t['border']};
        border-radius: 6px;
        padding: 8px 10px;
        color: {t['text']};
    }}
    QComboBox QAbstractItemView {{
        background: {t['panel']};
        color: {t['text']};
        selection-background-color: {t['accent_dim']};
        border: 1px solid {t['border']};
    }}
    QPushButton {{
        background: {t['accent']};
        color: {t['bg']};
        border: none;
        border-radius: 6px;
        padding: 11px 18px;
        font-weight: 600;
        font-family: "JetBrains Mono", "Consolas", monospace;
    }}
    QPushButton:hover {{ background: {t['accent']}; }}
    QPushButton:disabled {{
        background: {t['panel_alt']};
        color: {t['text_dim']};
    }}
    QPushButton#ghost {{
        background: transparent;
        color: {t['text_dim']};
        border: 1px solid {t['border']};
        font-weight: 400;
        padding: 8px 12px;
    }}
    QPushButton#ghost:hover {{
        color: {t['text']};
        border: 1px solid {t['text_dim']};
    }}
    QLabel#status {{
        color: {t['text_dim']};
        font-family: "JetBrains Mono", "Consolas", monospace;
        font-size: 12px;
    }}
    QLabel#status[error="true"] {{
        color: {t['error']};
    }}
    QLabel#dirlabel {{
        color: {t['text']};
        background: {t['panel_alt']};
        border: 1px solid {t['border']};
        border-radius: 6px;
        padding: 9px 12px;
        font-family: "JetBrains Mono", "Consolas", monospace;
        font-size: 12px;
    }}
    """
