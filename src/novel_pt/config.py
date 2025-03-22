import os
import json
from pathlib import Path
from typing import Dict, List, Optional

class Config:
    def __init__(self):
        # Define o diretório de dados do aplicativo
        if os.name == 'nt':  # Windows
            self.app_dir = Path(os.getenv('APPDATA')) / 'Novel-PT'
        else:  # Linux/Mac
            self.app_dir = Path.home() / '.config' / 'novel-pt'

        # Cria o diretório se não existir
        self.app_dir.mkdir(parents=True, exist_ok=True)

        # Arquivo de configuração
        self.config_file = self.app_dir / 'config.json'
        self.novels_file = self.app_dir / 'novels.json'

        # Carrega as configurações
        self.config = self._load_config()
        self.novels = self._load_novels()

    def _load_config(self) -> Dict:
        """Carrega as configurações gerais do aplicativo."""
        if self.config_file.exists():
            with open(self.config_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {
            'output_dir': str(Path.home() / 'Documents' / 'Novels Traduzidas'),
            'default_format': 'DOCX',
            'default_batch_size': 5,
            'show_chapter_number': True,
        }

    def _load_novels(self) -> List[Dict]:
        """Carrega a lista de novels salvas."""
        if self.novels_file.exists():
            with open(self.novels_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return []

    def save_config(self) -> None:
        """Salva as configurações gerais do aplicativo."""
        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump(self.config, f, indent=4, ensure_ascii=False)

    def save_novels(self) -> None:
        """Salva a lista de novels."""
        with open(self.novels_file, 'w', encoding='utf-8') as f:
            json.dump(self.novels, f, indent=4, ensure_ascii=False)

    def add_novel(self, novel_data: Dict) -> None:
        """Adiciona uma nova novel à lista."""
        # Adiciona campos padrão se não existirem
        novel_data.setdefault('current_chapter', novel_data.get('start_chapter', 0))
        novel_data.setdefault('status', 'Pendente')
        novel_data.setdefault('last_url', novel_data.get('url', ''))

        self.novels.append(novel_data)
        self.save_novels()

    def remove_novel(self, index: int) -> None:
        """Remove uma novel da lista pelo índice."""
        if 0 <= index < len(self.novels):
            self.novels.pop(index)
            self.save_novels()

    def update_novel(self, index: int, novel_data: Dict) -> None:
        """Atualiza os dados de uma novel existente."""
        if 0 <= index < len(self.novels):
            # Preserva campos existentes que não estão no novel_data
            current_novel = self.novels[index]
            novel_data.setdefault('current_chapter', current_novel.get('current_chapter', 0))
            novel_data.setdefault('status', current_novel.get('status', 'Pendente'))
            novel_data.setdefault('last_url', current_novel.get('last_url', novel_data.get('url', '')))

            self.novels[index] = novel_data
            self.save_novels()

    def get_novel(self, index: int) -> Optional[Dict]:
        """Retorna os dados de uma novel pelo índice."""
        if 0 <= index < len(self.novels):
            return self.novels[index]
        return None
