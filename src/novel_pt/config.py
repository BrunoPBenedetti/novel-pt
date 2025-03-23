import os
import json
import uuid
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

        # Inicializa a lista de novels vazia
        self.novels = []

        # Carrega as configurações
        self.config = self._load_config()
        self.novels = self._load_novels()

    def _generate_unique_id(self) -> str:
        """Gera um ID único para uma novel."""
        while True:
            new_id = str(uuid.uuid4())
            # Verifica se o ID já existe
            if not any(novel.get('id') == new_id for novel in self.novels):
                return new_id

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
                novels = json.load(f)
                # Garante que todas as novels tenham um ID
                for novel in novels:
                    if 'id' not in novel:
                        novel['id'] = self._generate_unique_id()
                return novels
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
        novel_data.setdefault('current_url', novel_data.get('url', ''))

        # Gera um ID único se não existir
        if 'id' not in novel_data:
            novel_data['id'] = self._generate_unique_id()

        self.novels.append(novel_data)
        self.save_novels()

    def remove_novel(self, novel_id: str) -> bool:
        """Remove uma novel da configuração pelo ID."""
        try:
            # Encontra o índice da novel
            novel_index = -1
            for i, novel in enumerate(self.novels):
                if novel['id'] == novel_id:
                    novel_index = i
                    break

            if novel_index == -1:
                print(f"❌ Novel com ID '{novel_id}' não encontrada")
                return False

            # Remove a novel
            self.novels.pop(novel_index)
            self.save_novels()
            print(f"✅ Novel removida com sucesso")
            return True

        except Exception as e:
            print(f"❌ Erro ao remover novel: {str(e)}")
            return False

    def update_novel(self, novel_id: str, novel_data: Dict) -> None:
        """Atualiza os dados de uma novel existente pelo ID."""
        # Encontra o índice da novel pelo ID
        for i, novel in enumerate(self.novels):
            if novel['id'] == novel_id:
                # Preserva campos existentes que não estão no novel_data
                current_novel = self.novels[i]
                novel_data.setdefault('current_chapter', current_novel.get('current_chapter', 0))
                novel_data.setdefault('status', current_novel.get('status', 'Pendente'))
                novel_data.setdefault('last_url', current_novel.get('last_url', novel_data.get('url', '')))
                novel_data.setdefault('id', novel_id)  # Mantém o ID original

                self.novels[i] = novel_data
                self.save_novels()
                return

        # Se não encontrou a novel, adiciona como nova
        self.add_novel(novel_data)

    def get_novel(self, novel_id: str) -> Optional[Dict]:
        """Retorna os dados de uma novel pelo ID."""
        for novel in self.novels:
            if novel['id'] == novel_id:
                return novel
        return None
