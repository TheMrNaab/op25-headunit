from PySide6.QtWidgets import QLabel, QApplication
from PySide6.QtCore import QTimer, QPropertyAnimation, Property
from PySide6.QtGui import QPainter

class BlinkingLabel(QLabel):
    def __init__(self, parent=None):
        super(BlinkingLabel, self).__init__(parent)
        self._angle = 0
        self.original_text = ''
        self.blink_timer = QTimer()
        self.blink_timer.timeout.connect(self.toggle_visibility)
        self.is_visible = True

        # Set up the rotation animation
        self.rotation_animation = QPropertyAnimation(self, b"angle")
        self.rotation_animation.setDuration(2000)
        self.rotation_animation.setStartValue(0)
        self.rotation_animation.setEndValue(360)
        self.rotation_animation.setLoopCount(-1)


    def start_blink(self, delay):
        self.original_text = self.text()
        self.blink_timer.start(delay)

    def stop_blink(self):
        self.blink_timer.stop()
        self.setText(self.original_text)
        self.is_visible = True

    def start_rotation(self):
        self.rotation_animation.start()

    def stop_rotation(self):
        self.rotation_animation.stop()

    def toggle_visibility(self):
        self.is_visible = not self.is_visible
        self.setText(self.original_text if self.is_visible else '')

    def set_font_color(self, color):
        self.setStyleSheet(f"color: {color};")

    def get_angle(self):
        return self._angle

    def set_angle(self, angle):
        self._angle = angle
        self.update()  # Trigger a repaint to apply the rotation

    angle = Property(float, get_angle, set_angle)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.translate(self.width() / 2, self.height() / 2)
        painter.rotate(self._angle)
        painter.translate(-self.width() / 2, -self.height() / 2)
        super(BlinkingLabel, self).paintEvent(event)