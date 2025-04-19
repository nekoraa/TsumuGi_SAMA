import sys
from PyQt6.QtWidgets import QApplication, QWidget
from PyQt6.QtGui import QPainter, QColor
from PyQt6.QtCore import Qt


class 圆形窗口(QWidget):
    def __init__(self, 半径=50, 颜色="#FF5733", 窗口大小=(300, 300)):
        super().__init__()
        self.半径 = 半径
        self.颜色 = QColor(颜色)
        self.setFixedSize(*窗口大小)
        self.setWindowTitle("圆形显示")

    def paintEvent(self, 事件):
        画家 = QPainter(self)
        画家.setRenderHint(QPainter.RenderHint.Antialiasing)

        中心点x = self.width() // 2
        中心点y = self.height() // 2

        画家.setBrush(self.颜色)
        画家.setPen(Qt.PenStyle.NoPen)

        画家.drawEllipse(中心点x - self.半径, 中心点y - self.半径,
                         self.半径 * 2, self.半径 * 2)

    def 设置新参数(self, 半径_=50, 颜色_="#FF5733"):
        self.半径 = 半径_
        self.颜色 = QColor(颜色_)
        self.update()


if __name__ == "__main__":
    应用 = QApplication(sys.argv)

    半径 = 80
    颜色 = "#33CC99"
    窗口大小 = (400, 400)

    窗口 = 圆形窗口(半径=半径, 颜色=颜色, 窗口大小=窗口大小)
    窗口.show()

    sys.exit(应用.exec())
