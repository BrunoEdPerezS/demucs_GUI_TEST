from PySide6.QtWidgets import QApplication, QMainWindow, QLabel, QLineEdit, QPushButton, QFileDialog, QVBoxLayout, QHBoxLayout, QWidget, QProgressBar, QMessageBox, QDialog
from PySide6.QtCore import Qt, QEvent, QThread, Signal
from PySide6.QtGui import QPixmap, QIcon
import demucs.separate
import subprocess

class ProgressDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Progreso")
        self.setFixedSize(300, 100)

        layout = QVBoxLayout()
        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)
        layout.addWidget(self.progress_bar)

        self.setLayout(layout)

    def update_progress(self, value):
        self.progress_bar.setValue(value)

class DemucsWorker(QThread):
    progress = Signal(int)
    finished = Signal()

    def __init__(self, fuente, salida):
        super().__init__()
        self.fuente = fuente
        self.salida = salida

    def run(self):
        process = subprocess.Popen(
            [
                "python", "-m", "demucs.separate",
                "--float32", "--clip-mode=rescale",
                "--two-stems", "guitar",
                "-n", "htdemucs_6s",
                self.fuente,
                "-o", self.salida
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8"  # Fix UnicodeDecodeError by setting encoding to utf-8
        )

        for line in process.stdout:
            if "%" in line:  # Parse progress percentage from output
                try:
                    progress = int(line.split("%")[0].strip())
                    self.progress.emit(progress)
                except ValueError:
                    continue

        process.wait()
        self.finished.emit()

class DemucsGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Demucs GUI")
        self.setGeometry(100, 100, 400, 300)
        self.setFixedSize(400, 300)  # Make the window non-resizable

        # Set the window icon
        self.setWindowIcon(QIcon("icon.png"))  # Replace "icon.png" with your icon file name

        self.setStyleSheet("""
            QMainWindow {
                background-color: #1e1e1e;
            }
            QLabel {
                color: #d4d4d4;
                font-size: 14px;
            }
            QLineEdit {
                background-color: #2d2d2d;
                color: #d4d4d4;
                border: 1px solid #3c3c3c;
                padding: 4px;
            }
            QPushButton {
                background-color: #3c3c3c;
                color: #d4d4d4;
                border: 1px solid #3c3c3c;
                padding: 6px;
            }
            QPushButton:hover {
                background-color: #444444;
            }
            QPushButton:pressed {
                background-color: #555555;
            }
            QProgressBar {
                background-color: #2d2d2d;
                border: 1px solid #3c3c3c;
                text-align: center;
                color: #d4d4d4;
            }
            QProgressBar::chunk {
                background-color: #f0c674;
            }
            QDialog {
                background-color: #1e1e1e;
            }
        """)

        self.fuente = None
        self.salida = None

        # Main layout
        layout = QVBoxLayout()

        # Drag-and-drop area for WAV file
        self.drag_label = QLabel("CARGAR ARCHIVO WAV")
        self.drag_label.setAlignment(Qt.AlignCenter)
        self.drag_label.setStyleSheet("border: 2px dashed #f0c674; padding: 20px; font-size: 16px;")
        self.drag_label.setAcceptDrops(True)
        self.drag_label.installEventFilter(self)
        self.drag_label.mousePressEvent = self.open_file_dialog  # Add click functionality
        layout.addWidget(self.drag_label)

        # Output directory selection
        output_layout = QHBoxLayout()  # Change to horizontal layout
        self.output_field = QLineEdit()
        self.output_field.setPlaceholderText("Ruta de salida")
        output_layout.addWidget(self.output_field)

        self.browse_button = QPushButton("Explorar")  # Define browse_button before using it
        self.browse_button.clicked.connect(self.browse_output_directory)
        output_layout.addWidget(self.browse_button)

        layout.addLayout(output_layout)  # Add horizontal layout to main layout

        # Label to display the name of the loaded file
        self.file_name_label = QLabel("")
        self.file_name_label.setAlignment(Qt.AlignCenter)
        self.file_name_label.setStyleSheet("color: #f0c674; font-size: 12px; padding: 4px;")
        self.file_name_label.setFixedHeight(self.browse_button.sizeHint().height())  # Match height to "Explorar" button
        layout.addWidget(self.file_name_label)

        # Image to display when a file is loaded
        self.loaded_image = QPixmap("loaded_image.png")  # Ensure the image file is named "loaded_image.png"

        # Execute button
        self.execute_button = QPushButton("EJECUTAR")
        self.execute_button.clicked.connect(self.execute_command)
        layout.addWidget(self.execute_button)

        # Set main widget
        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

    def open_file_dialog(self, event):
        file_path, _ = QFileDialog.getOpenFileName(self, "Seleccionar archivo WAV", "", "Archivos WAV (*.wav)")
        if file_path:
            self.fuente = file_path
            file_name = file_path.split("/")[-1]  # Extract the file name
            file_name = f"Archivo cargado: {file_name}"
            self.drag_label.setPixmap(self.loaded_image.scaled(self.drag_label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation))
            self.file_name_label.setText(file_name)  # Update the file name label

    def eventFilter(self, source, event):
        if source == self.drag_label and event.type() == QEvent.Drop:
            if event.mimeData().hasUrls():
                file_path = event.mimeData().urls()[0].toLocalFile()
                if file_path.endswith(".wav"):
                    self.fuente = file_path
                    file_name = file_path.split("/")[-1]  # Extract the file name
                    self.drag_label.setPixmap(self.loaded_image.scaled(self.drag_label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation))
                    self.file_name_label.setText(file_name)  # Update the file name label
                else:
                    self.drag_label.setText("Por favor, cargue un archivo .wav")
            return True
        elif source == self.drag_label and event.type() == QEvent.DragEnter:
            event.accept()
            return True
        return super().eventFilter(source, event)

    def browse_output_directory(self):
        directory = QFileDialog.getExistingDirectory(self, "Seleccionar carpeta de salida")
        if directory:
            self.salida = directory
            self.output_field.setText(directory)

    def execute_command(self):
        if self.fuente and self.salida:
            self.progress_dialog = ProgressDialog(self)
            self.progress_dialog.show()

            self.worker = DemucsWorker(self.fuente, self.salida)
            self.worker.progress.connect(self.progress_dialog.update_progress)
            self.worker.finished.connect(self.process_finished)
            self.worker.start()
        else:
            QMessageBox.warning(self, "Advertencia", "Por favor, cargue un archivo .wav y seleccione una carpeta de salida.")  # Show warning dialog

    def process_finished(self):
        self.progress_dialog.close()
        QMessageBox.information(self, "Proceso Finalizado", "El proceso ha terminado con éxito.")

if __name__ == "__main__":
    app = QApplication([])
    window = DemucsGUI()
    window.show()
    app.exec()
    window = DemucsGUI()
    window.show()
    app.exec()
    window = DemucsGUI()
    window.show()
    app.exec()
    window = DemucsGUI()
    window.show()
    app.exec()
