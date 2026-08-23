import customtkinter as ctk
from tkinter import filedialog
from PIL import Image, ImageTk, ImageDraw, ImageFont
from rembg import remove, new_session
import os
import threading
from pathlib import Path

# Drag & Drop
try:
    from tkinterdnd2 import DND_FILES, TkinterDnD
    HAS_DND = True
except ImportError:
    HAS_DND = False

# Configuração visual
ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")

# Modelos disponíveis (nome amigável -> identificador rembg)
MODELOS = {
    "u2net (geral - recomendado)": "u2net",
    "u2netp (leve e rápido)": "u2netp",
    "u2net_human_seg (pessoas)": "u2net_human_seg",
    "isnet-general-use (geral moderno)": "isnet-general-use",
    "isnet-anime (anime / ilustração)": "isnet-anime",
    "silueta (leve)": "silueta",
    "birefnet-general (alta qualidade)": "birefnet-general",
    "birefnet-portrait (retratos)": "birefnet-portrait",
    "birefnet-general-lite (boa qualidade / mais leve)": "birefnet-general-lite",
}


def criar_icone():
    """Gera um ícone simples do aplicativo (magic wand / cut)."""
    size = 256
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Fundo circular azul
    margin = 12
    draw.ellipse([margin, margin, size - margin, size - margin], fill=(30, 100, 200, 255))

    # Círculo interno mais claro
    draw.ellipse([40, 40, size - 40, size - 40], fill=(50, 140, 240, 255))

    # Tesoura / corte estilizado (duas linhas cruzadas + círculo)
    # Linha diagonal 1
    draw.line([(70, 70), (186, 186)], fill="white", width=18)
    # Linha diagonal 2
    draw.line([(186, 70), (70, 186)], fill="white", width=18)
    # Círculo central
    draw.ellipse([100, 100, 156, 156], fill=(30, 100, 200, 255), outline="white", width=8)

    return img


class AppRemoverBG(ctk.CTk):
    def __init__(self):
        super().__init__()

        # Ícone da janela
        try:
            self.icone = criar_icone()
            self.icone_tk = ImageTk.PhotoImage(self.icone.resize((64, 64), Image.LANCZOS))
            self.iconphoto(True, self.icone_tk)
        except Exception:
            pass

        self.title("BG Remover - Removedor de Fundo com IA")
        self.geometry("960x720")
        self.resizable(False, False)
        self.minsize(920, 680)

        # Variáveis de estado
        self.caminho_entrada = ""
        self.imagem_original = None
        self.imagem_sem_fundo = None
        self.photo_original = None
        self.photo_resultado = None
        self.processando = False
        self.session = None  # sessão do modelo atual
        self.modelo_atual = "u2net"

        # === TÍTULO ===
        self.label_titulo = ctk.CTkLabel(
            self,
            text="🖼️ Removedor de Fundo com IA",
            font=ctk.CTkFont(size=24, weight="bold")
        )
        self.label_titulo.pack(pady=(16, 6))

        # === FRAME DE CONTROLES (modelo + botões) ===
        self.frame_controles = ctk.CTkFrame(self, fg_color="transparent")
        self.frame_controles.pack(pady=6, fill="x", padx=20)

        # Seleção de modelo
        self.label_modelo = ctk.CTkLabel(
            self.frame_controles,
            text="Modelo:",
            font=ctk.CTkFont(size=13)
        )
        self.label_modelo.pack(side="left", padx=(0, 8))

        self.combo_modelo = ctk.CTkComboBox(
            self.frame_controles,
            values=list(MODELOS.keys()),
            width=320,
            height=36,
            font=ctk.CTkFont(size=13),
            command=self.ao_mudar_modelo
        )
        self.combo_modelo.set("u2net (geral - recomendado)")
        self.combo_modelo.pack(side="left", padx=(0, 20))

        # === FRAME DOS BOTÕES ===
        self.frame_botoes = ctk.CTkFrame(self, fg_color="transparent")
        self.frame_botoes.pack(pady=4)

        self.btn_selecionar = ctk.CTkButton(
            self.frame_botoes,
            text="📂 Selecionar Imagem",
            command=self.selecionar_imagem,
            width=180,
            height=40,
            font=ctk.CTkFont(size=14)
        )
        self.btn_selecionar.pack(side="left", padx=8)

        self.btn_processar = ctk.CTkButton(
            self.frame_botoes,
            text="✨ Remover Fundo",
            command=self.iniciar_remocao,
            state="disabled",
            width=180,
            height=40,
            font=ctk.CTkFont(size=14)
        )
        self.btn_processar.pack(side="left", padx=8)

        self.btn_salvar = ctk.CTkButton(
            self.frame_botoes,
            text="💾 Salvar Resultado",
            command=self.salvar_imagem,
            state="disabled",
            width=180,
            height=40,
            font=ctk.CTkFont(size=14)
        )
        self.btn_salvar.pack(side="left", padx=8)

        # === FRAME DE PRÉ-VISUALIZAÇÃO ===
        self.frame_preview = ctk.CTkFrame(self)
        self.frame_preview.pack(pady=10, padx=20, fill="both", expand=True)

        # --- Preview Original ---
        self.frame_original = ctk.CTkFrame(self.frame_preview)
        self.frame_original.pack(side="left", padx=12, pady=12, fill="both", expand=True)

        self.label_titulo_original = ctk.CTkLabel(
            self.frame_original,
            text="📷 Antes  (arraste a imagem aqui)",
            font=ctk.CTkFont(size=15, weight="bold")
        )
        self.label_titulo_original.pack(pady=(8, 4))

        self.label_preview_original = ctk.CTkLabel(
            self.frame_original,
            text="Nenhuma imagem\n\nArraste e solte aqui\nou clique em Selecionar",
            font=ctk.CTkFont(size=13),
            width=400,
            height=400,
            justify="center"
        )
        self.label_preview_original.pack(pady=6, padx=10)

        # --- Preview Resultado ---
        self.frame_resultado = ctk.CTkFrame(self.frame_preview)
        self.frame_resultado.pack(side="right", padx=12, pady=12, fill="both", expand=True)

        self.label_titulo_resultado = ctk.CTkLabel(
            self.frame_resultado,
            text="✅ Depois",
            font=ctk.CTkFont(size=15, weight="bold")
        )
        self.label_titulo_resultado.pack(pady=(8, 4))

        self.label_preview_resultado = ctk.CTkLabel(
            self.frame_resultado,
            text="Resultado aparecerá aqui",
            font=ctk.CTkFont(size=13),
            width=400,
            height=400
        )
        self.label_preview_resultado.pack(pady=6, padx=10)

        # === STATUS ===
        self.label_status = ctk.CTkLabel(
            self,
            text="Aguardando imagem... Arraste uma foto ou use o botão Selecionar.",
            font=ctk.CTkFont(size=13)
        )
        self.label_status.pack(pady=(2, 12))

        # Configura drag & drop se a biblioteca estiver disponível
        if HAS_DND:
            self._configurar_drag_drop()
        else:
            self.label_status.configure(
                text="Aguardando imagem... (instale tkinterdnd2 para arrastar e soltar)"
            )

    def _configurar_drag_drop(self):
        """Ativa suporte a arrastar e soltar nos painéis de preview."""
        try:
            TkinterDnD.require(self)
            # Registra o label de preview original como alvo de drop
            self.label_preview_original.drop_target_register(DND_FILES)
            self.label_preview_original.dnd_bind("<<Drop>>", self._on_drop)
            # Também no frame original
            self.frame_original.drop_target_register(DND_FILES)
            self.frame_original.dnd_bind("<<Drop>>", self._on_drop)
        except Exception as e:
            print(f"Aviso: não foi possível ativar drag & drop: {e}")

    def _on_drop(self, event):
        """Chamado quando o usuário solta arquivos na área de preview."""
        if self.processando:
            return

        try:
            # event.data pode conter um ou vários caminhos (Tcl list)
            caminhos = self.tk.splitlist(event.data)
            if not caminhos:
                return

            caminho = caminhos[0].strip("{}")  # remove chaves extras do Windows

            # Aceita apenas imagens
            extensoes = {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".gif"}
            if Path(caminho).suffix.lower() not in extensoes:
                self.label_status.configure(
                    text="Arquivo não é uma imagem válida.",
                    text_color=("red", "#e74c3c")
                )
                return

            self.carregar_imagem(caminho)

        except Exception as e:
            self.label_status.configure(
                text=f"Erro ao processar drop: {e}",
                text_color=("red", "#e74c3c")
            )

    def ao_mudar_modelo(self, escolha):
        """Atualiza o modelo selecionado."""
        self.modelo_atual = MODELOS.get(escolha, "u2net")
        self.session = None  # força recriação da sessão na próxima execução
        self.label_status.configure(
            text=f"Modelo alterado para: {escolha}",
            text_color=("gray", "gray70")
        )

    def criar_fundo_xadrez(self, tamanho=(400, 400), celula=14):
        """Cria fundo xadrez para visualizar transparência."""
        img = Image.new("RGBA", tamanho, (255, 255, 255, 255))
        draw = ImageDraw.Draw(img)
        cor1 = (190, 190, 190, 255)
        cor2 = (255, 255, 255, 255)

        for y in range(0, tamanho[1], celula):
            for x in range(0, tamanho[0], celula):
                cor = cor1 if (x // celula + y // celula) % 2 == 0 else cor2
                draw.rectangle([x, y, x + celula, y + celula], fill=cor)
        return img

    def redimensionar_para_preview(self, imagem, tamanho_max=380):
        """Redimensiona mantendo proporção."""
        largura, altura = imagem.size
        if largura == 0 or altura == 0:
            return imagem
        proporcao = min(tamanho_max / largura, tamanho_max / altura)
        nova_largura = max(1, int(largura * proporcao))
        nova_altura = max(1, int(altura * proporcao))
        return imagem.resize((nova_largura, nova_altura), Image.LANCZOS)

    def carregar_imagem(self, caminho):
        """Carrega a imagem a partir de um caminho (usado tanto pelo botão quanto pelo drop)."""
        try:
            self.caminho_entrada = caminho
            nome_arquivo = os.path.basename(caminho)

            self.imagem_original = Image.open(caminho).convert("RGBA")
            imagem_preview = self.redimensionar_para_preview(self.imagem_original.copy())
            self.photo_original = ImageTk.PhotoImage(imagem_preview)
            self.label_preview_original.configure(image=self.photo_original, text="")

            # Limpa resultado anterior
            self.imagem_sem_fundo = None
            self.photo_resultado = None
            self.label_preview_resultado.configure(image=None, text="Resultado aparecerá aqui")

            self.label_status.configure(
                text=f"Selecionado: {nome_arquivo}",
                text_color=("green", "#2ecc71")
            )
            self.btn_processar.configure(state="normal")
            self.btn_salvar.configure(state="disabled")

        except Exception as e:
            self.label_status.configure(
                text=f"Erro ao abrir imagem: {e}",
                text_color=("red", "#e74c3c")
            )

    def selecionar_imagem(self):
        if self.processando:
            return

        caminho = filedialog.askopenfilename(
            title="Selecione uma imagem",
            filetypes=[
                ("Imagens", "*.png *.jpg *.jpeg *.webp *.bmp *.gif"),
                ("Todos os arquivos", "*.*")
            ]
        )
        if caminho:
            self.carregar_imagem(caminho)

    def iniciar_remocao(self):
        if self.processando or not self.caminho_entrada or self.imagem_original is None:
            return

        self.processando = True
        self.btn_selecionar.configure(state="disabled")
        self.btn_processar.configure(state="disabled")
        self.btn_salvar.configure(state="disabled")
        self.combo_modelo.configure(state="disabled")

        self.label_status.configure(
            text=f"Processando com modelo '{self.modelo_atual}'... Aguarde (pode demorar na 1ª vez)",
            text_color=("orange", "#f39c12")
        )
        self.update_idletasks()

        thread = threading.Thread(target=self.remover_fundo, daemon=True)
        thread.start()

    def remover_fundo(self):
        try:
            # Cria ou reutiliza a sessão do modelo
            if self.session is None:
                self.session = new_session(self.modelo_atual)

            resultado = remove(self.imagem_original, session=self.session)
            self.imagem_sem_fundo = resultado

            # Preview com fundo xadrez
            preview = self.redimensionar_para_preview(resultado.copy())
            fundo = self.criar_fundo_xadrez(preview.size)
            composto = Image.alpha_composite(fundo, preview.convert("RGBA"))

            self.photo_resultado = ImageTk.PhotoImage(composto)
            self.after(0, self.atualizar_resultado_ok)

        except Exception as e:
            self.after(0, lambda: self.atualizar_resultado_erro(str(e)))

    def atualizar_resultado_ok(self):
        self.label_preview_resultado.configure(image=self.photo_resultado, text="")
        self.label_status.configure(
            text="Fundo removido com sucesso!",
            text_color=("green", "#2ecc71")
        )
        self.btn_salvar.configure(state="normal")
        self.btn_selecionar.configure(state="normal")
        self.btn_processar.configure(state="normal")
        self.combo_modelo.configure(state="normal")
        self.processando = False

    def atualizar_resultado_erro(self, mensagem):
        self.label_status.configure(
            text=f"Erro ao processar: {mensagem}",
            text_color=("red", "#e74c3c")
        )
        self.btn_selecionar.configure(state="normal")
        self.btn_processar.configure(state="normal")
        self.combo_modelo.configure(state="normal")
        self.processando = False

    def salvar_imagem(self):
        if self.imagem_sem_fundo is None or self.processando:
            return

        caminho_saida = filedialog.asksaveasfilename(
            defaultextension=".png",
            filetypes=[("Imagem PNG", "*.png")],
            title="Salvar imagem sem fundo",
            initialfile="sem_fundo.png"
        )

        if not caminho_saida:
            return

        try:
            self.imagem_sem_fundo.save(caminho_saida, "PNG")
            self.label_status.configure(
                text=f"Salvo em: {os.path.basename(caminho_saida)}",
                text_color=("green", "#2ecc71")
            )
        except Exception as e:
            self.label_status.configure(
                text=f"Erro ao salvar: {e}",
                text_color=("red", "#e74c3c")
            )


if __name__ == "__main__":
    app = AppRemoverBG()
    app.mainloop()
