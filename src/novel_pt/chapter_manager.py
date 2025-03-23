import os
import tempfile
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Callable
from datetime import datetime
from .web_scraper import WebScraper
from .translator import Translator
from docx import Document

class ChapterManager:
    def __init__(self, novel_data: Dict, progress_callback: Optional[Callable[[int, str], None]] = None):
        """Inicializa o gerenciador de capítulos."""
        self.novel_data = novel_data
        self.scraper = WebScraper()
        self.translator = Translator()
        self.progress_callback = progress_callback or (lambda x, y: None)

        # Cria diretórios temporários
        self.temp_dir = Path(tempfile.mkdtemp(prefix="novel_pt_"))
        self.raw_dir = self.temp_dir / "raw"
        self.translated_dir = self.temp_dir / "translated"
        self.raw_dir.mkdir()
        self.translated_dir.mkdir()

        self.log("Iniciando processamento de capítulos...")
        self.log(f"Diretório temporário: {self.temp_dir}")

    def log(self, message: str, progress: int = 0):
        """Registra uma mensagem e atualiza o progresso."""
        print(f"[{datetime.now().strftime('%H:%M:%S')}] {message}")
        self.progress_callback(progress, message)

    def download_chapters(self, start_chapter: int, batch_size: int) -> list:
        """Baixa os capítulos da novel."""
        chapters = []
        current_url = self.novel_data['url']
        chapters_downloaded = 0
        next_url = None

        self.log(f"🚀 Iniciando download dos capítulos a partir de: {current_url}")
        self.log(f"📚 Total de capítulos a baixar: {batch_size}")

        while chapters_downloaded < batch_size:
            chapter_num = start_chapter + chapters_downloaded
            self.log(f"📥 Baixando capítulo {chapter_num} ({chapters_downloaded + 1}/{batch_size})...")

            # Obtém o conteúdo do capítulo
            result = self.scraper.get_chapter_content(
                current_url,
                self.novel_data['content_xpath'],
                self.novel_data['next_chapter_xpath']
            )

            if not result['success']:
                self.log(f"❌ Não foi possível obter o conteúdo do capítulo {chapter_num}: {result.get('error', 'Erro desconhecido')}")
                break

            # Adiciona o capítulo à lista
            chapters.append({
                'number': chapter_num,
                'content': result['content'],
                'show_number': self.novel_data['show_chapter_number']
            })
            chapters_downloaded += 1

            # Atualiza a URL atual para o próximo capítulo
            if result.get('next_chapter_url') and chapters_downloaded < batch_size:
                next_url = result['next_chapter_url']
                current_url = next_url
                self.log(f"⏭️ Próximo capítulo: {next_url}")
            else:
                if not result.get('next_chapter_url'):
                    self.log(f"⚠️ Não foi encontrado link para o próximo capítulo")
                break

        # Atualiza a URL do último capítulo no novel_data com a URL do próximo capítulo
        if next_url:
            self.novel_data['last_url'] = next_url
            self.log(f"✅ URL final (próximo capítulo): {next_url}")
        else:
            self.novel_data['last_url'] = current_url
            self.log(f"✅ URL final (último capítulo): {current_url}")

        self.log(f"📊 Total de capítulos baixados: {chapters_downloaded}")

        return chapters

    def translate_chapters(self, chapters: List[Dict]) -> List[Dict]:
        """Traduz os capítulos baixados."""
        translated_chapters = []
        total_chapters = len(chapters)

        self.log(f"🔄 Iniciando tradução de {total_chapters} capítulos...")

        for i, chapter in enumerate(chapters):
            chapter_number = chapter['number']
            progress = 30 + int((i / total_chapters) * 40)  # Tradução ocupa 40% do progresso total
            self.log(f"📝 Traduzindo capítulo {chapter_number}...", progress)

            try:
                # Traduz o conteúdo
                translated_content = self.translator.translate_text(chapter['content'])

                # Adiciona o número do capítulo se necessário
                if chapter['show_number']:
                    translated_content = f"Capítulo {chapter_number}\n\n{translated_content}"

                translated_chapters.append({
                    'number': chapter_number,
                    'content': translated_content,
                    'show_number': chapter['show_number']
                })

                self.log(f"✅ Capítulo {chapter_number} traduzido com sucesso", progress)

            except Exception as e:
                self.log(f"❌ Erro ao traduzir capítulo {chapter_number}: {str(e)}", progress)
                continue

        if not translated_chapters:
            self.log("❌ Nenhum capítulo foi traduzido com sucesso")
        else:
            self.log(f"✅ {len(translated_chapters)} capítulos traduzidos com sucesso")

        return translated_chapters

    def merge_chapters(self, chapters: List[Dict], output_dir: str) -> Optional[str]:
        """Combina os capítulos traduzidos em um único arquivo."""
        if not chapters:
            self.log("❌ Nenhum capítulo para combinar")
            return None

        try:
            # Cria o diretório de saída se não existir
            output_path = Path(output_dir)
            output_path.mkdir(parents=True, exist_ok=True)

            # Gera o nome do arquivo usando o nome da novel e os números dos capítulos
            novel_name = self.novel_data['name']
            first_chapter = chapters[0]['number']
            last_chapter = chapters[-1]['number']

            # Remove caracteres especiais do nome da novel para usar no nome do arquivo
            safe_novel_name = "".join(c for c in novel_name if c.isalnum() or c in (' ', '-', '_')).strip()
            safe_novel_name = safe_novel_name.replace(' ', '_')

            # Constrói o nome do arquivo
            if self.novel_data['format'] == 'DOCX':
                output_file = output_path / f"{safe_novel_name}_cap{first_chapter}-{last_chapter}.docx"
            else:  # TXT
                output_file = output_path / f"{safe_novel_name}_cap{first_chapter}-{last_chapter}.txt"

            self.log(f"📝 Combinando capítulos em: {output_file.name}")

            if self.novel_data['format'] == 'DOCX':
                # Cria um novo documento
                doc = Document()

                # Adiciona o título da novel
                doc.add_heading(novel_name, 0)
                doc.add_paragraph(f"Capítulos {first_chapter} a {last_chapter}")
                doc.add_paragraph()  # Espaço em branco

                # Adiciona cada capítulo
                for chapter in chapters:
                    # Adiciona o número do capítulo se necessário
                    if chapter['show_number']:
                        doc.add_heading(f"Capítulo {chapter['number']}", level=1)

                    # Adiciona o conteúdo do capítulo
                    doc.add_paragraph(chapter['content'])

                    # Adiciona espaço entre capítulos
                    doc.add_paragraph()

                # Salva o documento
                doc.save(output_file)
            else:  # TXT
                with open(output_file, 'w', encoding='utf-8') as f:
                    # Adiciona o cabeçalho
                    f.write(f"{novel_name}\n")
                    f.write(f"Capítulos {first_chapter} a {last_chapter}\n\n")

                    # Adiciona cada capítulo
                    for chapter in chapters:
                        # Adiciona o número do capítulo se necessário
                        if chapter['show_number']:
                            f.write(f"Capítulo {chapter['number']}\n\n")

                        # Adiciona o conteúdo do capítulo
                        f.write(chapter['content'])

                        # Adiciona espaço entre capítulos
                        f.write("\n\n")

            self.log(f"✅ Arquivo final salvo em: {output_file}")
            return str(output_file)

        except Exception as e:
            self.log(f"❌ Erro ao combinar capítulos: {str(e)}")
            return None

    def cleanup(self):
        """Remove os arquivos temporários."""
        try:
            if hasattr(self, 'temp_dir') and self.temp_dir.exists():
                self.log("🧹 Limpando arquivos temporários...", 95)
                shutil.rmtree(self.temp_dir)
                self.log("✅ Arquivos temporários removidos com sucesso", 100)
        except Exception as e:
            self.log(f"⚠️ Erro ao limpar arquivos temporários: {str(e)}")

    def process_chapters(self, start_chapter: int, batch_size: int) -> str:
        """Processa os capítulos da novel."""
        try:
            # Calcula o número total de capítulos a serem traduzidos
            current_chapter = self.novel_data.get('current_chapter', 1)
            end_chapter = self.novel_data.get('end_chapter', current_chapter)
            total_chapters = end_chapter - current_chapter + 1

            # Baixa os capítulos
            chapters = self.download_chapters(current_chapter, batch_size)
            if not chapters:
                return None

            # Traduz os capítulos
            translated_chapters = self.translate_chapters(chapters)

            # Gera o arquivo final
            output_file = self.merge_chapters(translated_chapters, self.novel_data['output_dir'])

            # Atualiza o capítulo atual
            self.novel_data['current_chapter'] = current_chapter + batch_size
            self.config.update_novel(self.novel_data['name'], self.novel_data)

            return output_file

        except Exception as e:
            self.log(f"❌ Erro ao processar capítulos: {str(e)}")
            return None

    def __del__(self):
        """Destrutor para garantir a limpeza dos recursos."""
        try:
            self.cleanup()
        except:
            pass  # Ignora erros no destrutor
