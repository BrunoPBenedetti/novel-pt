from transformers import MarianMTModel, MarianTokenizer
import torch
from typing import List, Optional
import os
from docx import Document
from datetime import datetime
import nltk

# Garante que o 'punkt' está baixado
nltk.download('punkt')

class Translator:
    def __init__(self):
        """Inicializa o tradutor com o modelo e tokenizer."""
        self.model_name = 'Helsinki-NLP/opus-mt-tc-big-en-pt'  # Modelo para tradução de inglês para português
        self.tokenizer = MarianTokenizer.from_pretrained(self.model_name)
        self.model = MarianMTModel.from_pretrained(self.model_name)
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model.to(self.device)
        self.max_length = self.tokenizer.model_max_length

    def translate_text(self, text: str) -> str:
        """Traduz um texto do inglês para português."""
        try:
            if not text or not text.strip():
                return text

            # Divide o texto em linhas para preservar quebras de linha
            lines = text.split('\n')
            translated_lines = []

            for line in lines:
                if not line.strip():
                    translated_lines.append('')
                    continue

                try:
                    # Divide a linha em sentenças
                    sentences = nltk.tokenize.sent_tokenize(line, language='english')
                    sentences = [sentence.strip() for sentence in sentences if sentence.strip()]

                    # Inicializa variáveis para batching
                    translated_sentences = []
                    current_batch = []
                    current_batch_chars = 0
                    max_chars_per_request = 400

                    # Agrupa sentenças em lotes
                    batches = []
                    for sentence in sentences:
                        sentence_length = len(sentence)
                        if current_batch_chars + sentence_length + 1 <= max_chars_per_request:
                            current_batch.append(sentence)
                            current_batch_chars += sentence_length + 1
                        else:
                            batches.append(current_batch)
                            current_batch = [sentence]
                            current_batch_chars = sentence_length + 1
                    if current_batch:
                        batches.append(current_batch)

                    # Traduz cada lote
                    for batch in batches:
                        try:
                            # Verifica se alguma sentença excede o comprimento máximo
                            tokens = self.tokenizer.tokenize(' '.join(batch))
                            if len(tokens) > self.max_length:
                                # Divide em segmentos menores
                                segments = self.split_long_sentence(' '.join(batch))
                                for segment in segments:
                                    encoded = self.tokenizer(segment, return_tensors="pt", padding=True, truncation=True, max_length=self.max_length).to(self.device)
                                    translated_tokens = self.model.generate(**encoded)
                                    translated_segment = self.tokenizer.decode(translated_tokens[0], skip_special_tokens=True, clean_up_tokenization_spaces=True)
                                    translated_sentences.append(translated_segment)
                            else:
                                # Traduz o lote inteiro
                                encoded = self.tokenizer(' '.join(batch), return_tensors="pt", padding=True, truncation=True, max_length=self.max_length).to(self.device)
                                translated_tokens = self.model.generate(**encoded)
                                translated = self.tokenizer.decode(translated_tokens[0], skip_special_tokens=True, clean_up_tokenization_spaces=True)
                                translated_sentences.append(translated)
                        except Exception as e:
                            print(f"Erro ao traduzir lote: {str(e)}")
                            # Em caso de erro, mantém o texto original
                            translated_sentences.append(' '.join(batch))

                    # Reconstrói a linha com as sentenças traduzidas
                    translated_line = ' '.join(translated_sentences)
                    translated_lines.append(translated_line)

                except Exception as e:
                    print(f"Erro ao processar linha: {str(e)}")
                    # Em caso de erro, mantém a linha original
                    translated_lines.append(line)

            # Reconstrói o texto com as quebras de linha originais
            return '\n'.join(translated_lines)
        except Exception as e:
            print(f"Erro na tradução: {str(e)}")
            return text

    def split_long_sentence(self, sentence: str) -> List[str]:
        """Divide uma sentença longa em segmentos menores."""
        words = sentence.split()
        segments = []
        current_segment = ''
        for word in words:
            if len(self.tokenizer.tokenize(current_segment + ' ' + word)) <= self.max_length:
                current_segment += ' ' + word if current_segment else word
            else:
                segments.append(current_segment)
                current_segment = word
        if current_segment:
            segments.append(current_segment)
        return segments

    def save_chapter(self, content: str, novel_name: str, chapter_number: int,
                    output_dir: str, format: str = "DOCX") -> str:
        """Salva o capítulo traduzido no formato especificado."""
        try:
            # Cria o diretório de saída se não existir
            os.makedirs(output_dir, exist_ok=True)

            # Gera o nome do arquivo
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            if format == "DOCX":
                filename = f"{novel_name}_capitulo_{chapter_number}_{timestamp}.docx"
                filepath = os.path.join(output_dir, filename)

                # Cria o documento
                doc = Document()
                doc.add_paragraph(content)
                doc.save(filepath)
            elif format == "TXT":
                filename = f"{novel_name}_capitulo_{chapter_number}_{timestamp}.txt"
                filepath = os.path.join(output_dir, filename)

                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(content)
            else:
                raise ValueError(f"Formato não suportado: {format}")

            return filepath
        except Exception as e:
            print(f"Erro ao salvar capítulo: {str(e)}")
            return ""

    def translate_chapter(self, content: str, novel_name: str, chapter_number: int,
                         output_dir: str, format: str = "DOCX") -> Optional[str]:
        """Traduz e salva um capítulo."""
        try:
            # Traduz o conteúdo
            translated_content = self.translate_text(content)

            # Adiciona o número do capítulo se necessário
            if chapter_number > 0:
                translated_content = f"Capítulo {chapter_number}\n\n{translated_content}"

            # Salva o capítulo traduzido
            return self.save_chapter(translated_content, novel_name, chapter_number, output_dir, format)
        except Exception as e:
            print(f"Erro ao traduzir capítulo: {str(e)}")
            return None
