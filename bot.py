import logging
import os
import sys
import time
from datetime import datetime
from selenium.webdriver.common.by import By
from selenium.common.exceptions import WebDriverException, NoSuchElementException

from driver.driver import Driver
from iterator.iteration import Interation
from ext.functions import *
from ext.elements import XPATH, CSS

class Bot(Interation):
    """Classe que define um bot para interação automatizada com páginas da web."""

    def __init__(self, log_file=True):
        """
        Inicializa um objeto Bot.

        Args:
            log_file (bool): Define se os registros serão salvos em um arquivo de log (padrão: True).
        """
        self.logger = setup_logging(to_file=True)
        
        self.driver = Driver(
            browser='chrome',
            headless=False,
            incognito=False,
            download_path='',
            desabilitar_carregamento_imagem=False
        ).driver

        self.base_url = 'https://www.oabpr.org.br/servicos-consulta-de-advogados/lista-de-advogados/?nr_inscricao=0&nome=0&cidade=0&especialidade=0&situacao=A'

        super().__init__(self.driver)


    def open_oab(self):
        """Abre a página da OAB."""

        try:
            self.load_page(self.base_url)

            self.wait_for(XPATH['dado'])
            return True
        except Exception as e:
            self.logger.error(f"Erro ao abrir página inicial da OAB.")

    def get_last_page(self) -> int:
        """Retorna a última página da lista de advogados."""

        try:
            last_page = self.find(XPATH['ultima_pagina']).get_attribute('href')
            last_page = last_page.split('pg=')[-1]
            return int(last_page)
        except Exception as e:
            self.logger.error(f"Erro ao obter ultima pagina. {e}")

    def process_page(self, page: int):
        """
        Processa uma página da lista de advogados.

        Args:
            page (int): Número da página a ser processada.
        """

        self.logger.info(f'Processando a página {page}')
        try:
            if page != 1:
                self.load_page(self.base_url + f'&pg={page}')
            advogados = self.find_all(XPATH['dado'])
            
            for advogado in advogados:
                link = advogado.get_attribute('href')
                self.process_advogado(advogado.text, link)

        except Exception as e:
            self.logger.error(f"Erro ao processar página {page}: {e}")

    def is_solved(self):
        """Verifica se o captcha já foi resolvido."""

        time.sleep(2)
        solved = self.find(CSS['solved'], metodo='css').get_attribute('aria-checked')
        if solved == 'true':
            return True
        else:
            return False


    def process_advogado(self, advogado: str, link: str):
        """
        Processa um advogado.

        Args:
            link (str): Link do advogado.
        """

        self.logger.info(f'Processando o advogado {advogado}')
        try:
            self.load_page(link)            
            self.resolve_captcha()
            dados = self.get_values()
            insert_values(dados)

        except Exception as e:
            self.logger.error(f"Erro ao processar advogado {advogado}: {e}")

    def resolve_captcha(self):
        """Resolução do captcha."""
        try:
            iframe = self.find(CSS['reCAPTCHA'], metodo='css')
            self.driver.switch_to.frame(iframe)

            self.find(CSS['body'], metodo='css').click()

            self.driver.switch_to.default_content()
            if not self.is_solved():
                self.logger.info('Resolvendo captcha...')

                iframe_img = self.find(XPATH['iframe'])
                self.driver.switch_to.frame(iframe_img)

                audio_button = self.find(CSS['audio'], metodo='css')
                audio_button.click()

                audio_link = self.find(CSS['audio-source'], metodo='css').get_attribute('src')
                path_mp3, path_wav = get_temps_files()

                text = convert_audio_to_string(audio_link, path_mp3, path_wav)
                input_audio = self.find(CSS['input'], metodo='css')
                input_audio.send_keys(text)
                
                verificar_btn = self.find(CSS['verify_btn'], metodo='css').click()
                time.sleep(2)
                self.driver.switch_to.default_content()

            self.find(CSS['[value="ENVIAR"]'], metodo='css').click()
            self.wait_for(CSS['[value="Imprimir"]'], metodo='css')
        except Exception as e:
            self.logger.error(f"Erro ao resolver captcha: {e}")

    def get_values(self):
        """Retorna os dados do advogado."""

        try:
            self.wait_for(CSS['rows'], metodo='css')
            rows = self.find_all(CSS['rows'], metodo='css')
            dados = [row.find_elements(By.TAG_NAME, 'td')[1].text for row in rows]
            return dados
        except Exception as e:
            self.logger.error(f"Erro ao obter dados do advogado: {e}")
        
