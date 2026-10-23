"""Portable GOSHMAN desktop entrypoint with CI smoke test."""
from __future__ import annotations
import os
import sys


def run_self_test() -> int:
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    from PySide6.QtCore import QTimer
    from PySide6.QtWidgets import QApplication
    from goshman.gui import Window
    app = QApplication([])
    window = Window()
    QTimer.singleShot(300, app.quit)
    result = app.exec()
    window.close()
    return result


if __name__ == "__main__":
    if "--self-test" in sys.argv[1:]:
        raise SystemExit(run_self_test())
    from goshman.gui import main
    raise SystemExit(main())
