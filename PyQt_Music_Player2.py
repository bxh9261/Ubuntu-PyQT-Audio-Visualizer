import sys
import numpy as np
from PyQt5.QtWidgets import QApplication, QMainWindow, QFileDialog, QSlider, QHBoxLayout, QPushButton, QVBoxLayout, QWidget, QLabel
from PyQt5.QtMultimedia import QMediaContent, QMediaPlayer
from PyQt5.QtCore import QUrl, Qt, QRect, QThread, pyqtSignal
from mutagen import File
from PyQt5.QtGui import QPainter, QBrush, QColor
import pyaudio
import struct

class MusicPlayer(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Music Player")
        self.setGeometry(100, 100, 800, 500)

        self.player = QMediaPlayer()
        self.player.setVolume(50)

        self.init_ui()

        self.audio_visualizer = AudioVisualizer()
        self.layout.addWidget(self.audio_visualizer)

    def init_ui(self):
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)

        self.play_button = QPushButton("Play")
        self.stop_button = QPushButton("Stop")
        self.open_button = QPushButton("Open")
        self.track_info_label = QLabel("Track Information")
        self.track_info_label.setAlignment(Qt.AlignCenter)

        self.play_button.clicked.connect(self.play_music)
        self.stop_button.clicked.connect(self.stop_music)
        self.open_button.clicked.connect(self.open_music)

        self.slider = QSlider()
        self.slider.setOrientation(1)
        self.slider.setRange(0, 100)

        self.layout = QVBoxLayout()
        button_layout = QHBoxLayout()
        button_layout.addWidget(self.play_button)
        button_layout.addWidget(self.stop_button)
        button_layout.addWidget(self.open_button)

        self.layout.addLayout(button_layout)
        self.layout.addWidget(self.slider)
        self.layout.addWidget(self.track_info_label)

        central_widget.setLayout(self.layout)

        self.slider.valueChanged.connect(self.set_volume)

    def play_music(self):
        if self.player.state() == QMediaPlayer.PlayingState:
            self.player.pause()
        else:
            self.player.play()

        if self.player.state() == QMediaPlayer.PlayingState:
            title, artist = self.get_track_info()
            self.update_track_info(title, artist)

    def stop_music(self):
        self.player.stop()

    def open_music(self):
        options = QFileDialog.Options()
        options |= QFileDialog.ReadOnly
        file_path, _ = QFileDialog.getOpenFileName(self, "Open Music File", "", "Music Files (*.mp3 *.wav);;All Files (*)", options=options)
        if file_path:
            media_content = QMediaContent(QUrl.fromLocalFile(file_path))

            audio_thread = AudioThread(media_content)
            audio_thread.finished.connect(self.audio_finished)
            audio_thread.start()

    def set_volume(self, value):
        self.player.setVolume(value)

    def get_track_info(self):
        file = File(self.player.currentMedia().canonicalUrl().toLocalFile())
        title = file.get('title', 'Unknown Title')
        artist = file.get('artist', 'Unknown Artist')
        return title, artist

    def update_track_info(self, title, artist):
        track_info = f"{title} - {artist}"
        self.track_info_label.setText(track_info)

    def audio_finished(self):
        pass

class AudioThread(QThread):
    finished = pyqtSignal()

    def __init__(self, media_content):
        super().__init__()
        self.media_content = media_content

    def run(self):
        player = QMediaPlayer()
        player.setMedia(self.media_content)
        player.play()

        while player.state() == QMediaPlayer.PlayingState:
            pass

        player.deleteLater()
        self.finished.emit()

class AudioVisualizer(QWidget):
    def __init__(self):
        super().__init__()  # Use super() without double underscores

        self.init_ui()

        self.p = pyaudio.PyAudio()
        self.stream = self.p.open(format=pyaudio.paInt16,
                                 channels=1,
                                 rate=44100,
                                 input=True,
                                 output=True,
                                 frames_per_buffer=1024)

    def init_ui(self):
        self.setGeometry(100, 100, 600, 200)
        self.setStyleSheet("background-color: black")
        self.show()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        audio_data = self.stream.read(1024)
        audio_data = struct.unpack('1024h', audio_data)
        audio_data = np.array(audio_data, dtype='h')

        bar_width = self.width() / len(audio_data)
        bar_height = self.height()

        for i in range(len(audio_data)):
            x = int(i * bar_width)
            bar_rect = QRect(x, bar_height, int(bar_width), int(-audio_data[i] / 2))
            color = QColor(255, 0, 0)
            painter.fillRect(bar_rect, QBrush(color))

        self.update()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    player = MusicPlayer()
    player.show()
    sys.exit(app.exec_())
