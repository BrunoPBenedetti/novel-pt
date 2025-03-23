import sys
from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QLabel,
    QMessageBox,
    QProgressDialog,
    QHeaderView,
    QGridLayout,
    QFrame
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QIcon, QFont
from .config import Config
from .novel_form import NovelForm
from .chapter_manager import ChapterManager
from pathlib import Path

class TranslationWorker(QThread):
    """Worker para executar a tradução em uma thread separada."""
    progress = pyqtSignal(int, str)  # Sinal para atualizar o progresso
    finished = pyqtSignal(str)  # Sinal para indicar que terminou, com o caminho do arquivo
    error = pyqtSignal(str)  # Sinal para indicar erro

    def __init__(self, novel_data: dict, config: 'Config'):
        super().__init__()
        self.novel_data = novel_data
        self.config = config
        self.chapter_manager = ChapterManager(novel_data, self.progress.emit, config)

    def run(self):
        try:
            # Processa os capítulos
            output_file = self.chapter_manager.process_chapters(
                self.novel_data['current_chapter'],
                self.novel_data['batch_size']
            )

            if output_file:
                self.progress.emit(100, f"✅ Tradução concluída! Arquivo salvo em: {output_file}")
                self.finished.emit(output_file)  # Emite o output_file junto com o sinal finished
            else:
                self.error.emit("❌ Não foi possível processar os capítulos.")

        except Exception as e:
            self.error.emit(f"❌ Erro durante a tradução: {str(e)}")

class NovelCard(QFrame):
    def __init__(self, novel_data, main_window, parent=None):
        super().__init__(parent)
        self.novel_data = novel_data
        self.main_window = main_window
        self.setup_ui()

    def setup_ui(self):
        self.setFrameStyle(QFrame.Shape.StyledPanel | QFrame.Shadow.Raised)
        self.setStyleSheet("""
            QFrame {
                background-color: white;
                border-radius: 10px;
                padding: 20px;
                margin: 10px;
                border: 1px solid #e0e0e0;
            }
            QFrame:hover {
                background-color: #e3f2fd;
                border: 1px solid #2196F3;
            }
            QLabel {
                color: #333;
                padding: 5px;
            }
            QLabel:hover {
                background-color: white;
                color: black;
                border: 1px solid #2196F3;
            }
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: 5px;
                font-size: 10px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton#deleteButton {
                background-color: #f44336;
            }
            QPushButton#deleteButton:hover {
                background-color: #da190b;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Título
        title = QLabel(self.novel_data.get('name', 'Sem nome'))
        title.setFont(QFont('Arial', 14, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setWordWrap(True)
        layout.addWidget(title)

        # Capítulo atual
        current_chapter = self.novel_data.get('current_chapter', 1)
        chapter_label = QLabel(f"Capítulo atual: {current_chapter}")
        chapter_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        chapter_label.setFont(QFont('Arial', 12))
        layout.addWidget(chapter_label)

        # Botões
        button_layout = QHBoxLayout()
        button_layout.setSpacing(5)
        button_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        translate_btn = QPushButton("Traduzir")
        translate_btn.clicked.connect(lambda: self.main_window.start_translation(self.novel_data))
        translate_btn.setFixedSize(70, 25)
        button_layout.addWidget(translate_btn)

        edit_btn = QPushButton("Editar")
        edit_btn.clicked.connect(lambda: self.main_window.edit_novel(self.novel_data))
        edit_btn.setFixedSize(50, 25)
        button_layout.addWidget(edit_btn)

        delete_btn = QPushButton("Excluir")
        delete_btn.setObjectName("deleteButton")
        delete_btn.clicked.connect(lambda: self.main_window.delete_novel(self.novel_data['id']))
        delete_btn.setFixedSize(50, 25)
        button_layout.addWidget(delete_btn)

        layout.addLayout(button_layout)

        # Ajusta o tamanho do card
        self.setMinimumSize(400, 250)
        self.setMaximumSize(400, 250)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.config = Config()
        self.setWindowTitle("Novel-PT - Tradutor de Novels")
        self.setMinimumSize(1200, 800)

        # Widget central
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Layout principal
        layout = QVBoxLayout(central_widget)
        layout.setSpacing(20)
        layout.setContentsMargins(20, 20, 20, 20)

        # Título
        title = QLabel("Novel-PT - Tradutor de Novels")
        title.setFont(QFont('Arial', 24, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        layout.addWidget(title)

        # Grid de cards
        self.cards_grid = QGridLayout()
        self.cards_grid.setSpacing(20)
        layout.addLayout(self.cards_grid)

        # Botão de adicionar
        add_button = QPushButton("+ Adicionar Novel")
        add_button.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 5px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
        """)
        add_button.clicked.connect(self.show_novel_form)
        layout.addWidget(add_button)

        # Carrega novels salvas
        self.load_saved_novels()

    def load_saved_novels(self):
        """Carrega as novels salvas e cria os cards."""
        # Limpa o grid existente
        while self.cards_grid.count():
            item = self.cards_grid.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # Adiciona os cards
        for i, novel_data in enumerate(self.config.novels):
            row = i // 3  # 3 cards por linha
            col = i % 3
            card = NovelCard(novel_data, self, self)
            self.cards_grid.addWidget(card, row, col)

    def edit_novel(self, novel_data):
        """Edita uma novel existente."""
        form = NovelForm(self, novel_data)
        if form.exec() == NovelForm.DialogCode.Accepted:
            novel_data = form.get_novel_data()
            if novel_data['name'] and novel_data['url']:
                self.config.update_novel(novel_data['id'], novel_data)
                self.load_saved_novels()
            else:
                QMessageBox.warning(self, "Erro", "Nome e URL são obrigatórios.")

    def delete_novel(self, novel_id: str):
        """Remove uma novel."""
        try:
            # Obtém o nome da novel para a mensagem de confirmação
            novel = self.config.get_novel(novel_id)
            if not novel:
                return

            # Confirma a exclusão
            reply = QMessageBox.question(
                self,
                "Confirmar Exclusão",
                f"Tem certeza que deseja excluir a novel '{novel['name']}'?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )

            if reply == QMessageBox.StandardButton.Yes:
                # Remove a novel do config
                if self.config.remove_novel(novel_id):
                    # Atualiza a interface
                    self.load_saved_novels()
                    QMessageBox.information(
                        self,
                        "Sucesso",
                        f"Novel '{novel['name']}' removida com sucesso!"
                    )
                else:
                    QMessageBox.warning(
                        self,
                        "Erro",
                        f"Não foi possível remover a novel '{novel['name']}'."
                    )
        except Exception as e:
            QMessageBox.critical(
                self,
                "Erro",
                f"Erro ao remover novel: {str(e)}"
            )

    def show_novel_form(self):
        """Mostra o formulário para adicionar uma nova novel."""
        form = NovelForm(self)
        if form.exec() == NovelForm.DialogCode.Accepted:
            novel_data = form.get_novel_data()
            if novel_data['name'] and novel_data['url']:
                self.config.add_novel(novel_data)
                self.load_saved_novels()
            else:
                QMessageBox.warning(self, "Erro", "Nome e URL são obrigatórios.")

    def start_translation(self, novel_data):
        """Inicia o processo de tradução."""
        try:
            # Cria o diretório de saída se não existir
            output_dir = Path('output')
            output_dir.mkdir(exist_ok=True)

            # Calcula o número total de capítulos a serem traduzidos
            current_chapter = novel_data.get('current_chapter', 1)
            end_chapter = novel_data.get('end_chapter', current_chapter)
            total_chapters = end_chapter - current_chapter + 1

            # Configura o progresso
            self.progress_dialog = QProgressDialog(
                "Baixando e traduzindo capítulos...",
                "Cancelar",
                0,
                total_chapters,
                self
            )
            self.progress_dialog.setWindowTitle("Progresso da Tradução")
            self.progress_dialog.setWindowModality(Qt.WindowModality.ApplicationModal)
            self.progress_dialog.setMinimumDuration(0)
            self.progress_dialog.setAutoClose(False)
            self.progress_dialog.setAutoReset(False)
            self.progress_dialog.show()

            # Cria e inicia a thread de tradução
            self.translation_thread = TranslationWorker(novel_data, self.config)
            self.translation_thread.progress.connect(self.update_progress)
            self.translation_thread.finished.connect(self.translation_finished)
            self.translation_thread.error.connect(self.translation_error)
            self.translation_thread.start()

        except Exception as e:
            QMessageBox.critical(self, 'Erro', f'Erro ao iniciar tradução: {str(e)}')

    def update_progress(self, value, message):
        """Atualiza a barra de progresso."""
        self.progress_dialog.setValue(value)
        self.progress_dialog.setLabelText(message)

    def translation_finished(self, output_file):
        """Processa o final da tradução."""
        self.progress_dialog.close()
        QMessageBox.information(
            self,
            'Tradução Concluída',
            f'Tradução concluída com sucesso!\nArquivo salvo em: {output_file}'
        )
        self.load_saved_novels()  # Recarrega os cards para atualizar o capítulo atual

    def translation_error(self, error_message):
        """Processa erros durante a tradução."""
        self.progress_dialog.close()
        QMessageBox.critical(self, 'Erro', f'Erro durante a tradução: {error_message}')

def init():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
