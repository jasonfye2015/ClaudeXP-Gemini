APPLICATION_STYLE = """
QWidget {
    color: #20354b;
    font-family: "Segoe UI";
    font-size: 10pt;
}
QPushButton {
    min-height: 30px;
    padding: 3px 12px;
    border: 1px solid #9eb4c7;
    border-radius: 4px;
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                stop:0 #ffffff, stop:1 #e5edf4);
}
QPushButton:hover {
    border-color: #4e94c8;
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                stop:0 #ffffff, stop:1 #d5e9f8);
}
QPushButton:pressed {
    background: #c9deef;
}
QPushButton:disabled {
    color: #8797a5;
    background: #e5e9ed;
}
QLineEdit, QTextEdit, QComboBox {
    min-height: 28px;
    border: 1px solid #a9bac9;
    border-radius: 3px;
    padding: 3px 7px;
    background: #ffffff;
    selection-background-color: #4b91c5;
}
QGroupBox {
    margin-top: 12px;
    padding: 10px;
    border: 1px solid #c4d4e1;
    border-radius: 7px;
    background: rgba(255, 255, 255, 238);
}
QGroupBox::title {
    subcontrol-origin: margin;
    left: 12px;
    padding: 0 5px;
    color: #315b7d;
    font-weight: 600;
}
QScrollArea, QListWidget {
    border: 1px solid #c4d4e1;
    border-radius: 5px;
    background: #ffffff;
}
QListWidget::item {
    padding: 8px;
}
QListWidget::item:selected {
    color: #173958;
    background: #d9ecfa;
}
"""
