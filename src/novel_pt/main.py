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
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QIcon
from .config import Config
from .novel_form import NovelForm
from .chapter_manager import ChapterManager

class TranslationWorker(QThread):
    """Worker para executar a tradução em uma thread separada."""
    progress = pyqtSignal(int, str)  # Sinal para atualizar o progresso
    finished = pyqtSignal()  # Sinal para indicar que terminou
    error = pyqtSignal(str)  # Sinal para indicar erro

    def __init__(self, novel_data: dict):
        super().__init__()
        self.novel_data = novel_data
        self.chapter_manager = ChapterManager(novel_data, self.progress.emit)

    def run(self):
        try:
            # Processa os capítulos
            output_file = self.chapter_manager.process_chapters(
                self.novel_data['current_chapter'],
                self.novel_data['batch_size']
            )

            if output_file:
                self.progress.emit(100, f"✅ Tradução concluída! Arquivo salvo em: {output_file}")
                self.finished.emit()
            else:
                self.error.emit("❌ Não foi possível processar os capítulos.")

        except Exception as e:
            self.error.emit(f"❌ Erro durante a tradução: {str(e)}")

class ActionButton(QPushButton):
    """Botão personalizado para ações na tabela."""
    def __init__(self, text: str, parent=None):
        super().__init__(text, parent)
        self.setFixedSize(80, 25)  # Tamanho fixo para os botões
        self.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 5px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:pressed {
                background-color: #3d8b40;
            }
        """)

class DeleteButton(QPushButton):
    """Botão personalizado para remoção na tabela."""
    def __init__(self, parent=None):
        super().__init__("🗑️", parent)
        self.setFixedSize(30, 25)  # Tamanho fixo para o botão
        self.setStyleSheet("""
            QPushButton {
                background-color: #f44336;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 5px;
            }
            QPushButton:hover {
                background-color: #da190b;
            }
            QPushButton:pressed {
                background-color: #b71c1c;
            }
        """)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.config = Config()
        self.setWindowTitle("Novel-PT - Tradutor de Novels")
        self.setMinimumSize(1000, 600)

        # Widget central
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        # Botão de adicionar
        add_button = QPushButton("+ Adicionar Novel")
        add_button.clicked.connect(self.show_novel_form)
        layout.addWidget(add_button)

        # Tabela de novels
        self.novels_table = QTableWidget()
        self.novels_table.setColumnCount(15)  # Aumentado para 15 colunas
        self.novels_table.setHorizontalHeaderLabels([
            "Traduzir", "Editar", "Remover", "Nome", "URL", "XPath Conteúdo", "XPath Próximo",
            "Formato", "Início", "Atual", "Lote", "Nº Cap", "Pasta", "Status", "Última URL"
        ])

        # Configura o cabeçalho da tabela
        header = self.novels_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        header.setStretchLastSection(True)

        # Ajusta as colunas de ação para um tamanho fixo
        self.novels_table.setColumnWidth(0, 100)  # Coluna Traduzir
        self.novels_table.setColumnWidth(1, 100)  # Coluna Editar
        self.novels_table.setColumnWidth(2, 50)   # Coluna Remover

        layout.addWidget(self.novels_table)

        # Carrega novels salvas
        self.load_saved_novels()

    def load_saved_novels(self):
        """Carrega as novels salvas na tabela."""
        # Limpa a tabela antes de recarregar
        self.novels_table.setRowCount(0)

        for novel in self.config.novels:
            row = self.novels_table.rowCount()
            self.novels_table.insertRow(row)

            # Adiciona os botões de ação primeiro
            translate_btn = ActionButton("Traduzir")
            translate_btn.clicked.connect(lambda checked, r=row: self.start_translation(r))
            self.novels_table.setCellWidget(row, 0, translate_btn)

            edit_btn = ActionButton("Editar")
            edit_btn.clicked.connect(lambda checked, r=row: self.edit_row(r))
            self.novels_table.setCellWidget(row, 1, edit_btn)

            delete_btn = DeleteButton()
            delete_btn.clicked.connect(lambda checked, r=row: self.remove_row(r))
            self.novels_table.setCellWidget(row, 2, delete_btn)

            # Adiciona os dados da novel
            self.novels_table.setItem(row, 3, QTableWidgetItem(novel['name']))
            self.novels_table.setItem(row, 4, QTableWidgetItem(novel['url']))
            self.novels_table.setItem(row, 5, QTableWidgetItem(novel.get('content_xpath', '')))
            self.novels_table.setItem(row, 6, QTableWidgetItem(novel.get('next_chapter_xpath', '')))
            self.novels_table.setItem(row, 7, QTableWidgetItem(novel['format']))
            self.novels_table.setItem(row, 8, QTableWidgetItem(str(novel['start_chapter'])))
            self.novels_table.setItem(row, 9, QTableWidgetItem(str(novel['current_chapter'])))
            self.novels_table.setItem(row, 10, QTableWidgetItem(str(novel['batch_size'])))
            self.novels_table.setItem(row, 11, QTableWidgetItem("Sim" if novel['show_chapter_number'] else "Não"))
            self.novels_table.setItem(row, 12, QTableWidgetItem(novel.get('output_dir', '')))
            self.novels_table.setItem(row, 13, QTableWidgetItem(novel.get('status', 'Pendente')))
            self.novels_table.setItem(row, 14, QTableWidgetItem(novel.get('last_url', '')))

    def edit_row(self, row: int):
        """Edita a novel na linha especificada."""
        novel_data = self.config.get_novel(row)
        if novel_data:
            self.show_novel_form(novel_data)

    def remove_row(self, row: int):
        """Remove a novel na linha especificada."""
        reply = QMessageBox.question(
            self,
            "Confirmar Remoção",
            "Tem certeza que deseja remover esta novel?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            self.novels_table.removeRow(row)
            self.config.remove_novel(row)

    def start_translation(self, row: int):
        """Inicia a tradução da novel na linha especificada."""
        novel_data = self.config.get_novel(row)
        if not novel_data:
            QMessageBox.warning(self, "Erro", "Não foi possível obter os dados da novel.")
            return

        # Verifica se a pasta de saída existe
        output_dir = novel_data.get('output_dir', '')
        if not output_dir:
            QMessageBox.warning(self, "Erro", "Pasta de saída não especificada.")
            return

        # Cria o diálogo de progresso
        progress = QProgressDialog("Traduzindo capítulos...", "Cancelar", 0, 100, self)
        progress.setWindowModality(Qt.WindowModality.ApplicationModal)
        progress.setWindowTitle("Progresso da Tradução")
        progress.setMinimumDuration(0)
        progress.setAutoClose(True)
        progress.setAutoReset(True)
        progress.setCancelButton(None)

        # Usa a última URL se existir, senão usa a URL inicial
        if novel_data.get('last_url'):
            novel_data['url'] = novel_data['last_url']
            progress.setLabelText(f"📍 Continuando da última URL: {novel_data['url']}")

        # Cria e configura o worker
        self.worker = TranslationWorker(novel_data)
        self.worker.progress.connect(lambda value, msg: self.update_progress(progress, value, msg))
        self.worker.finished.connect(lambda: self.translation_finished(row, novel_data, progress))
        self.worker.error.connect(lambda msg: self.translation_error(msg, progress))
        progress.canceled.connect(self.worker.terminate)

        # Inicia a tradução
        self.worker.start()
        progress.exec()

    def show_novel_form(self, novel_data: dict = None):
        """Mostra o formulário para adicionar/editar uma novel."""
        form = NovelForm(self, novel_data)
        if form.exec() == NovelForm.DialogCode.Accepted:
            novel_data = form.get_novel_data()
            if novel_data['name'] and novel_data['url']:
                if novel_data:  # Edição
                    row = self.novels_table.currentRow()
                    if row >= 0:  # Verifica se há uma linha selecionada
                        self.config.update_novel(row, novel_data)
                        self.load_saved_novels()  # Recarrega a tabela para atualizar os botões
                    else:
                        # Se não houver linha selecionada, adiciona como novo
                        self.config.add_novel(novel_data)
                        self.load_saved_novels()
                else:  # Novo livro
                    self.config.add_novel(novel_data)
                    self.load_saved_novels()
            else:
                QMessageBox.warning(self, "Erro", "Nome e URL são obrigatórios.")

    def update_progress(self, progress: QProgressDialog, value: int, message: str):
        """Atualiza o progresso e a mensagem do diálogo."""
        progress.setValue(value)
        progress.setLabelText(message)
        # Mostra o botão de cancelar apenas durante o processo
        if value > 0 and value < 100:
            progress.setCancelButtonText("Cancelar")
        else:
            progress.setCancelButton(None)

    def translation_finished(self, row: int, novel_data: dict, progress: QProgressDialog):
        """Atualiza a interface após a tradução ser concluída."""
        # Atualiza o capítulo atual
        novel_data['current_chapter'] += novel_data['batch_size']
        self.config.update_novel(row, novel_data)
        self.novels_table.setItem(row, 9, QTableWidgetItem(str(novel_data['current_chapter'])))
        self.novels_table.setItem(row, 13, QTableWidgetItem("Concluído"))

        # Fecha o diálogo de progresso
        progress.close()

        # Mostra mensagem de sucesso
        QMessageBox.information(self, "Sucesso", "Tradução concluída com sucesso!")

    def translation_error(self, message: str, progress: QProgressDialog):
        """Exibe mensagem de erro durante a tradução."""
        # Fecha o diálogo de progresso
        progress.close()

        # Mostra mensagem de erro
        QMessageBox.warning(self, "Erro", message)

def init():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
