from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from typing import Optional, Dict, List
import time
import random
from urllib.parse import urljoin
from bs4 import BeautifulSoup
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options

class WebScraper:
    def __init__(self):
        """Inicializa o WebScraper com o driver do Chrome."""
        options = Options()
        options.add_argument('--headless')  # Executa em modo headless
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        options.add_argument('--disable-extensions')
        options.add_argument('--disable-infobars')
        options.add_argument('--disable-notifications')
        options.add_argument('--disable-popup-blocking')
        options.add_argument('--start-maximized')

        # Configura o driver usando webdriver_manager
        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(
            options=options,
            service=service
        )
        self.wait = WebDriverWait(self.driver, 10)  # Timeout de 10 segundos

    def __del__(self):
        """Fecha o driver quando o objeto é destruído."""
        if hasattr(self, 'driver'):
            try:
                self.driver.quit()
            except:
                pass

    def get_page(self, url: str) -> Optional[str]:
        """Obtém o conteúdo HTML de uma página."""
        try:
            # Adiciona um delay aleatório para evitar bloqueios
            time.sleep(random.uniform(1, 3))
            self.driver.get(url)
            # Espera até que o body esteja presente
            self.wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
            return self.driver.page_source
        except Exception as e:
            print(f"Erro ao acessar {url}: {str(e)}")
            return None

    def extract_text(self, html: str, xpath: str) -> Optional[str]:
        """Extrai texto de um elemento usando XPath."""
        try:
            # Converte o HTML para uma árvore XML para usar XPath
            element = self.driver.find_element(By.XPATH, xpath)
            if not element:
                return None

            # Obtém o HTML do elemento e usa BeautifulSoup para extrair o texto
            element_html = element.get_attribute('outerHTML')
            soup = BeautifulSoup(element_html, 'html.parser')

            # Remove scripts e estilos
            for script in soup(["script", "style"]):
                script.decompose()
            return soup.get_text(separator='\n', strip=True)
        except NoSuchElementException:
            print(f"Elemento não encontrado: {xpath}")
            return None
        except Exception as e:
            print(f"Erro ao extrair texto: {str(e)}")
            return None

    def find_next_chapter_url(self, next_chapter_xpath: str) -> Optional[str]:
        """Encontra a URL do próximo capítulo usando XPath e interagindo com o botão."""
        try:
            # Encontra o botão usando XPath
            next_button = self.driver.find_element(By.XPATH, next_chapter_xpath)
            if not next_button:
                return None

            # Obtém a URL atual antes de clicar
            current_url = self.driver.current_url

            # Faz scroll até o botão
            self.driver.execute_script("arguments[0].scrollIntoView(true);", next_button)
            time.sleep(1)  # Pequeno delay para garantir que o botão esteja visível

            # Clica no botão
            next_button.click()

            # Espera a navegação completar
            time.sleep(2)  # Pequeno delay para garantir que a navegação complete

            # Obtém a nova URL
            next_url = self.driver.current_url

            # Volta para a página anterior
            self.driver.back()

            # Espera a navegação voltar completar
            time.sleep(1)

            # Se a URL não mudou, significa que não há próximo capítulo
            if next_url == current_url:
                return None

            return next_url

        except Exception as e:
            print(f"Erro ao encontrar URL do próximo capítulo: {str(e)}")
            return None

    def get_chapter_content(self, url: str, content_xpath: str, next_chapter_xpath: str) -> Dict:
        """Obtém o conteúdo do capítulo e a URL do próximo capítulo."""
        try:
            # Salva a URL atual para uso posterior
            self.current_url = url

            # Obtém o HTML da página
            html = self.get_page(url)
            if not html:
                return {'success': False, 'error': 'Não foi possível obter o conteúdo da página'}

            # Extrai o conteúdo do capítulo
            content = self.extract_text(html, content_xpath)
            if not content:
                return {'success': False, 'error': 'Não foi possível extrair o conteúdo do capítulo'}

            # Encontra o botão do próximo capítulo e obtém sua URL de redirecionamento
            next_chapter_url = self.find_next_chapter_url( next_chapter_xpath)
            if not next_chapter_url:
                return {
                    'success': True,
                    'content': content,
                    'next_chapter_url': None
                }

            return {
                'success': True,
                'content': content,
                'next_chapter_url': next_chapter_url
            }

        except Exception as e:
            return {'success': False, 'error': str(e)}
