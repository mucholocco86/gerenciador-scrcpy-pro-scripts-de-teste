# =====================================================================
# ARQUIVO: barra_lateral.py (PARTE 1 DE 2 - NOVO CONTAINER EMBUTIDO)
# =====================================================================
import customtkinter as ctk
import threading
import sys
import os

class JanelaGameplayEmbutida(ctk.CTkToplevel):
    def __init__(self, app_principal, serial_dispositivo):
        super().__init__()
        
        self.app = app_principal
        self.serial = serial_dispositivo
        
        # Configurações da Janela Unificada (Largura adaptável para o celular + Barra)
        self.title(f"Espelhamento PRO - {self.serial}")
        self.geometry("510x800") # Tamanho inicial padrão ajustável
        self.resizable(True, True)
        
        # Mantém controle do ID da janela do Scrcpy
        self.scrcpy_hwnd = None
        
        # LAYOUT: Dividido em duas partes principais
        # Lado Esquerdo: Onde a janela do Scrcpy será "engolida" e travada
        self.frame_scrcpy = ctk.CTkFrame(self, fg_color="black", corner_radius=0)
        self.frame_scrcpy.pack(side="left", fill="both", expand=True)
        
        # Lado Direito: A nossa Barra de Ferramentas Gamer fixa de 60px
        self.barra_ferramentas = ctk.CTkFrame(self, width=60, fg_color="#1a1a1a", corner_radius=0)
        self.barra_ferramentas.pack(side="right", fill="y")
        
        # Constrói os botões fixos na barra lateral direita
        self.criar_botoes_painel()
        
        # Dispara o monitor para capturar e embutir a janela do Scrcpy
        self.iniciar_captura_janela()

    def criar_botoes_painel(self):
        """Cria os botões de atalho fixados na lateral direita do container"""
        self.btn_mapa = ctk.CTkButton(self.barra_ferramentas, text="🎮", width=45, height=45, fg_color="#2b2b2b", hover_color="#3a3a3a", font=("Arial", 16))
        self.btn_mapa.pack(pady=10, padx=5)
        
        self.btn_hid = ctk.CTkButton(self.barra_ferramentas, text="⌨️", width=45, height=45, fg_color="#2b2b2b", hover_color="#3a3a3a", font=("Arial", 16))
        self.btn_hid.pack(pady=10, padx=5)
        
        self.btn_config = ctk.CTkButton(self.barra_ferramentas, text="⚙️", width=45, height=45, fg_color="#2b2b2b", hover_color="#3a3a3a", font=("Arial", 16))
        self.btn_config.pack(pady=10, padx=5)
        
        ctk.CTkFrame(self.barra_ferramentas, height=2, width=40, fg_color="gray30").pack(pady=15)
        
        self.btn_tela_off = ctk.CTkButton(self.barra_ferramentas, text="👁️❌", width=45, height=45, fg_color="#2b2b2b", hover_color="#8e44ad", font=("Arial", 12))
        self.btn_tela_off.pack(pady=10, padx=5)
# =====================================================================
# ARQUIVO: barra_lateral.py (PARTE 2 DE 2 - MOTOR DE INCORPORAÇÃO NATIVO)
# =====================================================================
    def iniciar_captura_janela(self):
        """Dispara a busca em segundo plano para embutir a janela do Scrcpy"""
        threading.Thread(target=self._procurar_e_embutir_scrcpy, daemon=True).start()

    def _procurar_e_embutir_scrcpy(self):
        import ctypes
        import time
        
        user32 = ctypes.windll.user32
        
        # Estilos de janela do Windows para manipulação de bordas
        GWL_STYLE = -16
        WS_VISIBLE = 0x10000000
        WS_CHILD = 0x40000000
        WS_BORDER = 0x00800000
        WS_CAPTION = 0x00C00000
        WS_THICKFRAME = 0x00040000
        
        # Função de callback interna para listar janelas do barramento de vídeo
        def checar_janela(hwnd, lParam):
            if user32.IsWindowVisible(hwnd):
                nome_classe = ctypes.create_unicode_buffer(256)
                user32.GetClassNameW(hwnd, nome_classe, 256)
                
                # Procura a classe SDL_app nativa do Scrcpy
                if nome_classe.value == "SDL_app":
                    titulo_janela = ctypes.create_unicode_buffer(256)
                    user32.GetWindowTextW(hwnd, titulo_janela, 256)
                    
                    # Certifica-se de capturar o jogo e não o nosso painel
                    if titulo_janela.value and not "Espelhamento PRO" in titulo_janela.value:
                        self.scrcpy_hwnd = hwnd
                        return False # Para a busca ao encontrar
            return True

        WNDENUMPROC = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.wintypes.HWND, ctypes.wintypes.LPARAM)
        callback = WNDENUMPROC(checar_janela)

        # Loop de busca por até 10 segundos até o Scrcpy carregar completamente
        tentativas = 0
        while not self.scrcpy_hwnd and tentativas < 40:
            user32.EnumWindows(callback, 0)
            time.sleep(0.25)
            tentativas += 1

        if self.scrcpy_hwnd:
            # Captura o identificador numérico interno do frame do Python (CustomTkinter)
            self.update_idletasks()
            python_frame_hwnd = self.frame_scrcpy.winfo_id()
            
            # Remove a barra de título e as bordas originais do Scrcpy para ele virar um bloco liso
            estilo_atual = user32.GetWindowLongW(self.scrcpy_hwnd, GWL_STYLE)
            estilo_limpo = estilo_atual & ~(WS_CAPTION | WS_THICKFRAME | WS_BORDER)
            estilo_limpo |= WS_CHILD # Transforma em uma janela filha
            user32.SetWindowLongW(self.scrcpy_hwnd, GWL_STYLE, estilo_limpo)
            
            # A MÁGICA COMERCIAL: Engole a janela do Scrcpy prendendo-a dentro do frame do Python
            user32.SetParent(self.scrcpy_hwnd, python_frame_hwnd)
            
            # Configura o loop de redimensionamento automático para sincronizar tamanhos
            self._ajustar_tamanhos_em_tempo_real()
            
            # Vincula o fechamento da janela do Python para encerrar o processo do Scrcpy junto
            self.protocol("WM_DELETE_WINDOW", self._fechar_janela_unificada)

    def _ajustar_tamanhos_em_tempo_real(self):
        """Mantém a janela do Scrcpy perfeitamente esticada dentro do frame do Python"""
        import ctypes
        user32 = ctypes.windll.user32
        
        def loop_redimensionamento():
            if self.scrcpy_hwnd and user32.IsWindow(self.scrcpy_hwnd):
                # Captura a largura e altura atual que o frame do Python ganhou na tela
                self.update_idletasks()
                largura_frame = self.frame_scrcpy.winfo_width()
                altura_frame = self.frame_scrcpy.winfo_height()
                
                # Força o Scrcpy a preencher 100% do espaço do frame com atraso zero
                user32.MoveWindow(self.scrcpy_hwnd, 0, 0, largura_frame, altura_frame, True)
                
                # Executa essa sincronização a cada 30 milissegundos
                self.after(30, loop_redimensionamento)
                
        loop_redimensionamento()

    def _fechar_janela_unificada(self):
        """Garante o encerramento do processo oculto ao fechar o container principal"""
        import ctypes
        user32 = ctypes.windll.user32
        if self.scrcpy_hwnd and user32.IsWindow(self.scrcpy_hwnd):
            # Envia uma mensagem nativa de fechamento para o Scrcpy
            WM_CLOSE = 0x0010
            user32.PostMessageW(self.scrcpy_hwnd, WM_CLOSE, 0, 0)
        self.destroy()