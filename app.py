import customtkinter as ctk
from tkinter import filedialog
from PIL import Image, ImageTk, ImageDraw
from rembg import remove
import os
import threading

# Configuração visual
ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")


class AppRemoverBG(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("BG Remover - Removedor de Fundo com IA")
        self.geometry("920x680")
        self.resizable(False, False)
        self.minsize(900, 650)

        # Variáveis de estado
        self.caminho_entrada = ""
        self.imagem_original = None
        self.imagem_sem_fundo = None
        self.photo_original = None
        self.photo_resultado = None
        self.processando = False

        # === TÍTULO ===
        self.label_titulo = ctk.CTkLabel(
            self,
            text="🖼️ Removedor de Fundo com IA",
            font=ctk.CTkFont(size=24, weight="bold")
        )
        self.label_titulo.pack(pady=(18, 8))

        # === FRAME DOS BOTÕES ===
        self.frame_botoes = ctk.CTkFrame(self, fg_color="transparent")
        self.frame_botoes.pack(pady=8)

        self.btn_selecionar = ctk.CTkButton(
            self.frame_botoes,
            text="📂 Selecionar Imagem",
            command=self.selecionar_imagem,
            width=190,
            height=42,
            font=ctk.CTkFont(size=14)
        )
        self.btn_selecionar.pack(side="left", padx=8)

        self.btn_processar = ctk.CTkButton(
            self.frame_botoes,
            text="✨ Remover Fundo",
            command=self.iniciar_remocao,
            state="disabled",
            width=190,
            height=42,
            font=ctk.CTkFont(size=14)
        )
        self.btn_processar.pack(side="left", padx=8)

        self.btn_salvar = ctk.CTkButton(
            self.frame_botoes,
            text="💾 Salvar Resultado",
            command=self.salvar_imagem,
            state="disabled",
            width=190,
            height=42,
            font=ctk.CTkFont(size=14)
        )
        self.btn_salvar.pack(side="left", padx=8)

        # === FRAME DE PRÉ-VISUALIZAÇÃO ===
        self.frame_preview = ctk.CTkFrame(self)
        self.frame_preview.pack(pady=12, padx=20, fill="both", expand=True)

        # --- Preview Original ---
        self.frame_original = ctk.CTkFrame(self.frame_preview)
        self.frame_original.pack(side="left", padx=12, pady=12, fill="both", expand=True)

        self.label_titulo_original = ctk.CTkLabel(
            self.frame_original,
            text="📷 Antes",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        self.label_titulo_original.pack(pady=(8, 4))

        self.label_preview_original = ctk.CTkLabel(
            self.frame_original,
            text="Nenhuma imagem selecionada",
            font=ctk.CTkFont(size=13),
            width=380,
            height=380
        )
        self.label_preview_original.pack(pady=6, padx=10)

        # --- Preview Resultado ---
        self.frame_resultado = ctk.CTkFrame(self.frame_preview)
        self.frame_resultado.pack(side="right", padx=12, pady=12, fill="both", expand=True)

        self.label_titulo_resultado = ctk.CTkLabel(
            self.frame_resultado,
            text="✅ Depois",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        self.label_titulo_resultado.pack(pady=(8, 4))

        self.label_preview_resultado = ctk.CTkLabel(
            self.frame_resultado,
            text="Resultado aparecerá aqui",
            font=ctk.CTkFont(size=13),
            width=380,
            height=380
        )
        self.label_preview_resultado.pack(pady=6, padx=10)

        # === STATUS ===
        self.label_status = ctk.CTkLabel(
            self,
            text="Aguardando imagem...",
            font=ctk.CTkFont(size=13)
        )
        self.label_status.pack(pady=(4, 14))

    def criar_fundo_xadrez(self, tamanho=(380, 380), celula=12):
        """Cria um fundo xadrez para visualizar transparência."""
        img = Image.new("RGBA", tamanho, (255, 255, 255, 255))
        draw = ImageDraw.Draw(img)
        cor1 = (200, 200, 200, 255)
        cor2 = (255, 255, 255, 255)

        for y in range(0, tamanho[1], celula):
            for x in range(0, tamanho[0], celula):
                cor = cor1 if (x // celula + y // celula) % 2 == 0 else cor2
                draw.rectangle([x, y, x + celula, y + celula], fill=cor)
        return img

    def redimensionar_para_preview(self, imagem, tamanho_max=360):
        """Redimensiona mantendo proporção."""
        largura, altura = imagem.size
        if largura == 0 or altura == 0:
            return imagem
        proporcao = min(tamanho_max / largura, tamanho_max / altura)
        nova_largura = max(1, int(largura * proporcao))
        nova_altura = max(1, int(altura * proporcao))
        return imagem.resize((nova_largura, nova_altura), Image.LANCZOS)

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
        if not caminho:
            return

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

    def iniciar_remocao(self):
        if self.processando or not self.caminho_entrada or self.imagem_original is None:
            return

        self.processando = True
        self.btn_selecionar.configure(state="disabled")
        self.btn_processar.configure(state="disabled")
        self.btn_salvar.configure(state="disabled")

        self.label_status.configure(
            text="Processando com IA... Aguarde (pode demorar na 1ª vez)",
            text_color=("orange", "#f39c12")
        )
        self.update_idletasks()

        # Roda a remoção em thread separada para não travar a interface
        thread = threading.Thread(target=self.remover_fundo, daemon=True)
        thread.start()

    def remover_fundo(self):
        try:
            resultado = remove(self.imagem_original)
            self.imagem_sem_fundo = resultado

            # Prepara preview com fundo xadrez para mostrar transparência
            preview = self.redimensionar_para_preview(resultado.copy())
            fundo = self.criar_fundo_xadrez(preview.size)
            composto = Image.alpha_composite(fundo, preview.convert("RGBA"))

            self.photo_resultado = ImageTk.PhotoImage(composto)

            # Atualiza a interface na thread principal
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
        self.processando = False

    def atualizar_resultado_erro(self, mensagem):
        self.label_status.configure(
            text=f"Erro ao processar: {mensagem}",
            text_color=("red", "#e74c3c")
        )
        self.btn_selecionar.configure(state="normal")
        self.btn_processar.configure(state="normal")
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
