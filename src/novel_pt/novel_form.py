from PyQt6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QSpinBox,
    QComboBox,
    QCheckBox,
    QPushButton,
    QFormLayout,
    QFileDialog,
)
from typing import Dict, Optional
from pathlib import Path
from PyQt6.QtCore import Qt

class NovelForm(QDialog):
    """Formulário para adicionar/editar uma novel."""
    def __init__(self, parent=None, novel_data: dict = None):
        super().__init__(parent)
        self.novel_data = novel_data or {}
        self.setWindowTitle("Adicionar/Editar Novel")
        self.setMinimumWidth(500)

        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        # Formulário
        form_layout = QFormLayout()

        # Nome
        self.name_input = QLineEdit()
        self.name_input.setText(self.novel_data.get('name', ''))
        form_layout.addRow("Nome:", self.name_input)

        # URL
        self.url_input = QLineEdit()
        self.url_input.setText(self.novel_data.get('url', ''))
        form_layout.addRow("URL:", self.url_input)

        # URL atual
        self.current_url = QLineEdit()
        self.current_url.setText(self.novel_data.get('current_url', ''))
        form_layout.addRow("URL Atual:", self.current_url)

        # XPath do conteúdo
        self.content_xpath = QLineEdit()
        self.content_xpath.setText(self.novel_data.get('content_xpath', ''))
        self.content_xpath.setPlaceholderText("Ex: //div[@class='chapter-content']")
        form_layout.addRow("XPath do Conteúdo:", self.content_xpath)

        # XPath do próximo capítulo
        self.next_chapter_xpath = QLineEdit()
        self.next_chapter_xpath.setText(self.novel_data.get('next_chapter_xpath', ''))
        self.next_chapter_xpath.setPlaceholderText("Ex: //a[contains(@class, 'next-chapter')]")
        form_layout.addRow("XPath do Próximo Capítulo:", self.next_chapter_xpath)

        # Formato de saída
        self.format_combo = QComboBox()
        self.format_combo.addItems(["DOCX", "TXT"])
        self.format_combo.setCurrentText(self.novel_data.get('format', 'DOCX'))
        form_layout.addRow("Formato de Saída:", self.format_combo)

        # Pasta de saída
        output_layout = QHBoxLayout()
        self.output_input = QLineEdit()
        self.output_input.setText(self.novel_data.get('output_dir', str(Path.home() / 'Documents' / 'Novels Traduzidas')))
        output_button = QPushButton("...")
        output_button.clicked.connect(self.select_output_dir)
        output_layout.addWidget(self.output_input)
        output_layout.addWidget(output_button)
        form_layout.addRow("Pasta de Saída:", output_layout)

        # Capítulo inicial
        self.start_chapter = QSpinBox()
        self.start_chapter.setMinimum(1)
        self.start_chapter.setMaximum(9999)
        self.start_chapter.setValue(self.novel_data.get('start_chapter', 1))
        form_layout.addRow("Capítulo Inicial:", self.start_chapter)

        # Capítulo atual
        self.current_chapter = QSpinBox()
        self.current_chapter.setMinimum(1)
        self.current_chapter.setMaximum(9999)
        self.current_chapter.setValue(self.novel_data.get('current_chapter', 1))
        form_layout.addRow("Capítulo Atual:", self.current_chapter)

        # Tamanho do lote
        self.batch_size = QSpinBox()
        self.batch_size.setMinimum(1)
        self.batch_size.setMaximum(50)
        self.batch_size.setValue(self.novel_data.get('batch_size', 5))
        form_layout.addRow("Capítulos por Lote:", self.batch_size)

        # Mostrar número do capítulo
        self.show_chapter_number = QCheckBox()
        self.show_chapter_number.setChecked(self.novel_data.get('show_chapter_number', True))
        form_layout.addRow("Mostrar Número do Capítulo:", self.show_chapter_number)

        layout.addLayout(form_layout)

        # Botões
        button_layout = QHBoxLayout()
        save_button = QPushButton("Salvar")
        save_button.clicked.connect(self.accept)
        cancel_button = QPushButton("Cancelar")
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(save_button)
        button_layout.addWidget(cancel_button)
        layout.addLayout(button_layout)

    def select_output_dir(self):
        """Abre um diálogo para selecionar a pasta de saída."""
        dir_path = QFileDialog.getExistingDirectory(
            self,
            "Selecionar Pasta de Saída",
            self.output_input.text(),
            QFileDialog.Option.ShowDirsOnly
        )
        if dir_path:
            self.output_input.setText(dir_path)

    def get_novel_data(self) -> Dict:
        """Retorna os dados do formulário em formato de dicionário."""
        return {
            'id': self.novel_data.get('id'),
            'name': self.name_input.text().strip(),
            'url': self.url_input.text().strip(),
            'current_url': self.current_url.text().strip(),
            'content_xpath': self.content_xpath.text().strip(),
            'next_chapter_xpath': self.next_chapter_xpath.text().strip(),
            'format': self.format_combo.currentText(),
            'output_dir': self.output_input.text().strip(),
            'start_chapter': self.start_chapter.value(),
            'current_chapter': self.current_chapter.value(),
            'batch_size': self.batch_size.value(),
            'show_chapter_number': self.show_chapter_number.isChecked(),
            'status': self.novel_data.get('status', 'Pendente')
        }
