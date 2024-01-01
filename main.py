from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QPushButton, QFileDialog, QComboBox, QWidget, QLabel, QGroupBox, QProgressDialog
from PySide6.QtCore import Qt, QThread, Signal, QUrl  # Add QUrl import
from spleeter.separator import Separator
from PySide6.QtGui import QDesktopServices
from pathlib import Path

class SpleeterWorker(QThread):
    finished_signal = Signal()

    def __init__(self, parent=None):
        super(SpleeterWorker, self).__init__(parent)
        self.input_audio_path = ""
        self.output_path = ""
        self.num_stems = 2

    def set_parameters(self, input_audio_path, output_path, num_stems):
        self.input_audio_path = input_audio_path
        self.output_path = output_path
        self.num_stems = num_stems

    def run(self):
        separator = Separator(f"spleeter:{self.num_stems}stems")
        separator.separate_to_file(self.input_audio_path, self.output_path)
        self.finished_signal.emit()

class SpleeterGUI(QMainWindow):
    def __init__(self):
        super(SpleeterGUI, self).__init__()
        self.setWindowTitle("Spleeter GUI")

        self.central_widget = QWidget(self)
        self.setCentralWidget(self.central_widget)

        self.layout = QVBoxLayout(self.central_widget)

        self.disclaimer_text = (
            "prompt"
        )
        self.disclaimer_label = QLabel(self.disclaimer_text)
        self.disclaimer_label.setAlignment(Qt.AlignCenter)
        self.disclaimer_label.setStyleSheet("QLabel { color : red; }")
        self.layout.addWidget(self.disclaimer_label)

        self.show_disclaimer_label()

        # Frame for audio file selection
        self.audio_file_groupbox = QGroupBox("选择音频文件", self)
        self.layout.addWidget(self.audio_file_groupbox)

        audio_file_layout = QVBoxLayout(self.audio_file_groupbox)

        self.select_button = QPushButton("Select Audio File", self.audio_file_groupbox)
        self.select_button.clicked.connect(self.select_audio)
        audio_file_layout.addWidget(self.select_button)

        self.selected_file_label = QLabel("Selected file: No file selected", self.audio_file_groupbox)
        audio_file_layout.addWidget(self.selected_file_label)

        # Frame for model selection
        self.model_groupbox = QGroupBox("选择Model", self)
        self.layout.addWidget(self.model_groupbox)

        model_layout = QVBoxLayout(self.model_groupbox)

        self.num_stems_combobox = QComboBox(self.model_groupbox)
        self.num_stems_combobox.addItems(["2 Stems", "4 Stems", "5 Stems"])
        self.num_stems_combobox.setCurrentIndex(0)  # 设置默认选择为 "2 Stems"
        self.num_stems_combobox.currentIndexChanged.connect(self.update_model_description)
        model_layout.addWidget(self.num_stems_combobox)

        self.model_description_label = QLabel("Model Description", self.model_groupbox)
        model_layout.addWidget(self.model_description_label)
        # 设置默认选择后更新模型描述
        self.model_description_label.setText("Vocals (singing voice) / accompaniment separation")

        # Frame for output directory selection
        self.output_dir_groupbox = QGroupBox("选择输出目录", self)
        self.layout.addWidget(self.output_dir_groupbox)

        output_dir_layout = QVBoxLayout(self.output_dir_groupbox)

        self.select_output_button = QPushButton("Select Output Directory", self.output_dir_groupbox)
        self.select_output_button.clicked.connect(self.select_output_directory)
        output_dir_layout.addWidget(self.select_output_button)

        self.selected_output_label = QLabel("Selected output directory: No directory selected", self.output_dir_groupbox)
        output_dir_layout.addWidget(self.selected_output_label)

        self.run_button = QPushButton("Run Spleeter", self)
        self.run_button.clicked.connect(self.run_spleeter)
        self.layout.addWidget(self.run_button)

        # Disable run_button initially
        self.run_button.setEnabled(False)

    def show_disclaimer_label(self):
        disclaimer_text = (
            "If you plan to use Spleeter on copyrighted material, make sure\n"
            "you get proper authorization from right owners beforehand."
        )
        disclaimer_label = QLabel(disclaimer_text)
        disclaimer_label.setAlignment(Qt.AlignCenter)
        self.layout.addWidget(disclaimer_label)

    def select_audio(self):
        default_dir = "."  # 设置默认目录为程序自身目录
        file_path, _ = QFileDialog.getOpenFileName(self, "Select Audio File", default_dir, "Audio Files (*.mp3 *.wav)")
        if file_path:
            print("Selected file:", file_path)
            self.selected_file_label.setText(f"Selected file: {file_path}")

        # Enable or disable run_button based on conditions
        self.update_run_button_state()

    def update_model_description(self, index):
        model_descriptions = [
            "Vocals (singing voice) / accompaniment separation",
            "Vocals / drums / bass / other separation",
            "Vocals / drums / bass / piano / other separation"
        ]
        self.model_description_label.setText(model_descriptions[index])

    def select_output_directory(self):
        output_dir = QFileDialog.getExistingDirectory(self, "Select Output Directory", ".", QFileDialog.ShowDirsOnly)
        if output_dir:
            print("Selected output directory:", output_dir)
            self.selected_output_label.setText(f"Selected output directory: {output_dir}")

        # Enable or disable run_button based on conditions
        self.update_run_button_state()

    def run_spleeter(self):
        input_audio_path = self.selected_file_label.text().split(":")[1].strip()  # 从标签中提取文件路径
        output_path = self.selected_output_label.text().split(":")[1].strip()  # 从标签中提取输出目录路径
        num_stems_str = self.num_stems_combobox.currentText()
        num_stems = int(num_stems_str.split()[0])  # Extract the number from the string

        # Run Spleeter in a separate thread
        self.worker = SpleeterWorker()
        self.worker.set_parameters(input_audio_path, output_path, num_stems)
        self.worker.finished_signal.connect(self.spleeter_finished)
        self.progress_dialog = QProgressDialog("Running Spleeter...", "Cancel", 0, 0, self)
        self.progress_dialog.setWindowTitle("Processing")
        self.progress_dialog.setWindowModality(Qt.WindowModal)
        self.progress_dialog.canceled.connect(self.worker.terminate)
        self.progress_dialog.show()

        self.worker.start()

    def spleeter_finished(self):
        self.progress_dialog.accept()  # Close the progress dialog
        print("Spleeter finished processing")
        # self.selected_output_label.setText("Selected output directory: No directory selected")  # Reset output directory label

        # Enable or disable run_button based on conditions
        self.update_run_button_state()

        # Open the output directory using the default file explorer
        output_path = self.selected_output_label.text().split(":")[1].strip()
        if output_path:
            QDesktopServices.openUrl(QUrl.fromLocalFile(output_path))  # Fix the import here

    def update_run_button_state(self):
        # Enable or disable run_button based on conditions
        input_file_selected = "No file selected" not in self.selected_file_label.text()
        output_dir_selected = "No directory selected" not in self.selected_output_label.text()
        self.run_button.setEnabled(input_file_selected and output_dir_selected)

if __name__ == "__main__":
    app = QApplication([])
    window = SpleeterGUI()
    window.show()
    app.exec()
