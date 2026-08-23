import customtkinter as ctk
from tkinter import filedialog
from PIL import Image, ImageTk, ImageDraw
from rembg import remove, new_session
import os
import threading
from pathlib import Path
import io

# Drag & Drop
try:
    from tkinterdnd2 import DND_FILES, TkinterDnD
    HAS_DND = True
except ImportError:
    HAS_DND = False

# Configuração visual
ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")

# Modelos disponíveis
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

EXTENSOES = {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".gif"}


def criar_icone():
    """Gera um ícone simples do aplicativo."""
    size = 256
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    margin = 12
    draw.ellipse([margin, margin, size - margin, size - margin], fill=(30, 100, 200, 255))
    draw.ellipse([40, 40, size - 40, size - 40], fill=(50, 140, 240, 255))
    draw.line([(70, 70), (186, 186)], fill="white", width=18)
    draw.line([(186, 70), (70, 186)], fill="white", width=18)
    draw.ellipse([100, 100, 156, 156], fill=(30, 100, 200, 255), outline="white", width=8)
    return img


class AppRemoverBG(ctk.CTk):
    def __init__(self):
        super().__init__()

        # Ícone
        try:
            self.icone = criar_icone()
            self.icone_tk = ImageTk.PhotoImage(self.icone.resize((64, 64), Image.LANCZOS))
            self.iconphoto(True, self.icone_tk)
        except Exception:
            pass

        self.title("BG Remover - Removedor de Fundo com IA")
        self.geometry("980x800")
        self.resizable(False, False)
        self.minsize(940, 760)

        # Estado
        self.caminho_entrada = ""
        self.imagem_original = None
        self.imagem_sem_fundo = None
        self.photo_original = None
        self.photo_resultado = None
        self.processando = False
        self.session = None
        self.modelo_atual = "u2net"
        self.fila_batch = []
        self.indice_batch = 0
        self.pasta_saida_batch = ""

        # === TÍTULO ===
        self.label_titulo = ctk.CTkLabel(
            self,
            text="🖼️ Removedor de Fundo com IA",
            font=ctk.CTkFont(size=24, weight="bold")
        )
        self.label_titulo.pack(pady=(12, 4))

        # === CONTROLES (modelo) ===
        self.frame_controles = ctk.CTkFrame(self, fg_color="transparent")
        self.frame_controles.pack(pady=4, fill="x", padx=20)

        self.label_modelo = ctk.CTkLabel(
            self.frame_controles,
            text="Modelo:",
            font=ctk.CTkFont(size=13)
        )
        self.label_modelo.pack(side="left", padx=(0, 8))

        self.combo_modelo = ctk.CTkComboBox(
            self.frame_controles,
            values=list(MODELOS.keys()),
            width=340,
            height=34,
            font=ctk.CTkFont(size=13),
            command=self.ao_mudar_modelo
        )
        self.combo_modelo.set("u2net (geral - recomendado)")
        self.combo_modelo.pack(side="left", padx=(0, 16))

        # === BOTÕES PRINCIPAIS ===
        self.frame_botoes = ctk.CTkFrame(self, fg_color="transparent")
        self.frame_botoes.pack(pady=4)

        self.btn_selecionar = ctk.CTkButton(
            self.frame_botoes,
            text="📂 Selecionar",
            command=self.selecionar_imagem,
            width=140,
            height=38,
            font=ctk.CTkFont(size=13)
        )
        self.btn_selecionar.pack(side="left", padx=6)

        self.btn_batch = ctk.CTkButton(
            self.frame_botoes,
            text="📁 Lote (várias)",
            command=self.selecionar_lote,
            width=140,
            height=38,
            font=ctk.CTkFont(size=13)
        )
        self.btn_batch.pack(side="left", padx=6)

        self.btn_processar = ctk.CTkButton(
            self.frame_botoes,
            text="✨ Remover Fundo",
            command=self.iniciar_remocao,
            state="disabled",
            width=150,
            height=38,
            font=ctk.CTkFont(size=13)
        )
        self.btn_processar.pack(side="left", padx=6)

        self.btn_salvar = ctk.CTkButton(
            self.frame_botoes,
            text="💾 Salvar",
            command=self.salvar_imagem,
            state="disabled",
            width=120,
            height=38,
            font=ctk.CTkFont(size=13)
        )
        self.btn_salvar.pack(side="left", padx=6)

        self.btn_copiar = ctk.CTkButton(
            self.frame_botoes,
            text="📋 Copiar",
            command=self.copiar_para_clipboard,
            state="disabled",
            width=120,
            height=38,
            font=ctk.CTkFont(size=13)
        )
        self.btn_copiar.pack(side="left", padx=6)

        # === BARRA DE PROGRESSO (visível só no lote) ===
        self.frame_progresso = ctk.CTkFrame(self, fg_color="transparent")
        self.frame_progresso.pack(pady=(6, 2), fill="x", padx=30)

        self.label_progresso = ctk.CTkLabel(
            self.frame_progresso,
            text="",
            font=ctk.CTkFont(size=12)
        )
        self.label_progresso.pack(pady=(0, 2))

        self.barra_progresso = ctk.CTkProgressBar(
            self.frame_progresso,
            width=700,
            height=16,
            corner_radius=8
        )
        self.barra_progresso.set(0)
        self.barra_progresso.pack()
        # Esconde no início
        self.frame_progresso.pack_forget()

        # === PRÉ-VISUALIZAÇÃO ===
        self.frame_preview = ctk.CTkFrame(self)
        self.frame_preview.pack(pady=6, padx=18, fill="both", expand=True)

        # Original
        self.frame_original = ctk.CTkFrame(self.frame_preview)
        self.frame_original.pack(side="left", padx=10, pady=10, fill="both", expand=True)

        self.label_titulo_original = ctk.CTkLabel(
            self.frame_original,
            text="📷 Antes  (arraste a imagem aqui)",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        self.label_titulo_original.pack(pady=(6, 2))

        self.label_preview_original = ctk.CTkLabel(
            self.frame_original,
            text="Nenhuma imagem\n\nArraste e solte aqui\nou use os botões acima",
            font=ctk.CTkFont(size=13),
            width=400,
            height=380,
            justify="center"
        )
        self.label_preview_original.pack(pady=4, padx=8)

        # Resultado
        self.frame_resultado = ctk.CTkFrame(self.frame_preview)
        self.frame_resultado.pack(side="right", padx=10, pady=10, fill="both", expand=True)

        self.label_titulo_resultado = ctk.CTkLabel(
            self.frame_resultado,
            text="✅ Depois",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        self.label_titulo_resultado.pack(pady=(6, 2))

        self.label_preview_resultado = ctk.CTkLabel(
            self.frame_resultado,
            text="Resultado aparecerá aqui",
            font=ctk.CTkFont(size=13),
            width=400,
            height=380
        )
        self.label_preview_resultado.pack(pady=4, padx=8)

        # === STATUS ===
        self.label_status = ctk.CTkLabel(
            self,
            text="Aguardando imagem... Arraste, selecione ou use o modo Lote.",
            font=ctk.CTkFont(size=13)
        )
        self.label_status.pack(pady=(2, 10))

        # Drag & Drop
        if HAS_DND:
            self._configurar_drag_drop()
        else:
            self.label_status.configure(
                text="Aguardando imagem... (instale tkinterdnd2 para arrastar e soltar)"
            )

    # ------------------------------------------------------------------
    # Drag & Drop
    # ------------------------------------------------------------------
    def _configurar_drag_drop(self):
        try:
            TkinterDnD.require(self)
            for widget in (self.label_preview_original, self.frame_original):
                widget.drop_target_register(DND_FILES)
                widget.dnd_bind("<<Drop>>", self._on_drop)
        except Exception as e:
            print(f"Aviso DnD: {e}")

    def _on_drop(self, event):
        if self.processando:
            return
        try:
            caminhos = self.tk.splitlist(event.data)
            if not caminhos:
                return

            arquivos_validos = []
            for c in caminhos:
                caminho = c.strip("{}")
                if Path(caminho).suffix.lower() in EXTENSOES and Path(caminho).is_file():
                    arquivos_validos.append(caminho)

            if not arquivos_validos:
                self.label_status.configure(
                    text="Nenhum arquivo de imagem válido encontrado.",
                    text_color=("red", "#e74c3c")
                )
                return

            if len(arquivos_validos) == 1:
                self.carregar_imagem(arquivos_validos[0])
            else:
                self.iniciar_lote_com_lista(arquivos_validos)

        except Exception as e:
            self.label_status.configure(
                text=f"Erro no drop: {e}",
                text_color=("red", "#e74c3c")
            )

    # ------------------------------------------------------------------
    # Modelo
    # ------------------------------------------------------------------
    def ao_mudar_modelo(self, escolha):
        self.modelo_atual = MODELOS.get(escolha, "u2net")
        self.session = None
        self.label_status.configure(
            text=f"Modelo alterado para: {escolha}",
            text_color=("gray", "gray70")
        )

    # ------------------------------------------------------------------
    # Helpers de imagem
    # ------------------------------------------------------------------
    def criar_fundo_xadrez(self, tamanho=(400, 400), celula=14):
        img = Image.new("RGBA", tamanho, (255, 255, 255, 255))
        draw = ImageDraw.Draw(img)
        cor1 = (190, 190, 190, 255)
        cor2 = (255, 255, 255, 255)
        for y in range(0, tamanho[1], celula):
            for x in range(0, tamanho[0], celula):
                cor = cor1 if (x // celula + y // celula) % 2 == 0 else cor2
                draw.rectangle([x, y, x + celula, y + celula], fill=cor)
        return img

    def redimensionar_para_preview(self, imagem, tamanho_max=370):
        largura, altura = imagem.size
        if largura == 0 or altura == 0:
            return imagem
        proporcao = min(tamanho_max / largura, tamanho_max / altura)
        return imagem.resize(
            (max(1, int(largura * proporcao)), max(1, int(altura * proporcao))),
            Image.LANCZOS
        )

    def carregar_imagem(self, caminho):
        try:
            self.caminho_entrada = caminho
            self.fila_batch = []
            nome = os.path.basename(caminho)

            self.imagem_original = Image.open(caminho).convert("RGBA")
            preview = self.redimensionar_para_preview(self.imagem_original.copy())
            self.photo_original = ImageTk.PhotoImage(preview)
            self.label_preview_original.configure(image=self.photo_original, text="")

            self.imagem_sem_fundo = None
            self.photo_resultado = None
            self.label_preview_resultado.configure(image=None, text="Resultado aparecerá aqui")

            self._esconder_progresso()

            self.label_status.configure(
                text=f"Selecionado: {nome}",
                text_color=("green", "#2ecc71")
            )
            self.btn_processar.configure(state="normal")
            self.btn_salvar.configure(state="disabled")
            self.btn_copiar.configure(state="disabled")

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

    # ------------------------------------------------------------------
    # Progresso
    # ------------------------------------------------------------------
    def _mostrar_progresso(self):
        self.frame_progresso.pack(pady=(6, 2), fill="x", padx=30, before=self.frame_preview)
        self.barra_progresso.set(0)
        self.label_progresso.configure(text="Preparando...")

    def _esconder_progresso(self):
        self.frame_progresso.pack_forget()
        self.barra_progresso.set(0)
        self.label_progresso.configure(text="")

    def _atualizar_progresso(self, atual, total, nome=""):
        if total <= 0:
            return
        valor = atual / total
        self.barra_progresso.set(valor)
        pct = int(valor * 100)
        texto = f"{atual}/{total}  ({pct}%)"
        if nome:
            texto += f"  —  {nome}"
        self.label_progresso.configure(text=texto)

    # ------------------------------------------------------------------
    # Processamento em LOTE
    # ------------------------------------------------------------------
    def selecionar_lote(self):
        if self.processando:
            return

        caminhos = filedialog.askopenfilenames(
            title="Selecione várias imagens para processar em lote",
            filetypes=[
                ("Imagens", "*.png *.jpg *.jpeg *.webp *.bmp *.gif"),
                ("Todos os arquivos", "*.*")
            ]
        )
        if not caminhos:
            return

        self.iniciar_lote_com_lista(list(caminhos))

    def iniciar_lote_com_lista(self, lista):
        self.fila_batch = [c for c in lista if Path(c).suffix.lower() in EXTENSOES]
        if not self.fila_batch:
            self.label_status.configure(
                text="Nenhuma imagem válida selecionada.",
                text_color=("red", "#e74c3c")
            )
            return

        pasta = filedialog.askdirectory(title="Escolha a pasta onde salvar os resultados")
        if not pasta:
            self.fila_batch = []
            return

        self.pasta_saida_batch = pasta
        self.indice_batch = 0
        self.processando = True
        self._desabilitar_controles()
        self._mostrar_progresso()

        self.label_status.configure(
            text=f"Iniciando lote com {len(self.fila_batch)} imagens...",
            text_color=("orange", "#f39c12")
        )
        self.update_idletasks()

        thread = threading.Thread(target=self._processar_lote, daemon=True)
        thread.start()

    def _processar_lote(self):
        total = len(self.fila_batch)
        sucesso = 0
        erros = 0

        try:
            if self.session is None:
                self.session = new_session(self.modelo_atual)

            for i, caminho in enumerate(self.fila_batch):
                self.indice_batch = i + 1
                nome = os.path.basename(caminho)

                # Atualiza barra + status na thread principal
                self.after(0, lambda a=i+1, t=total, n=nome: self._atualizar_progresso(a, t, n))
                self.after(0, lambda n=nome, i=i, t=total: self.label_status.configure(
                    text=f"Lote: processando {n} ({i+1}/{t})",
                    text_color=("orange", "#f39c12")
                ))

                try:
                    img = Image.open(caminho).convert("RGBA")
                    resultado = remove(img, session=self.session)

                    stem = Path(caminho).stem
                    saida = os.path.join(self.pasta_saida_batch, f"{stem}_sem_fundo.png")
                    resultado.save(saida, "PNG")
                    sucesso += 1

                    # Atualiza preview com a última processada
                    self.imagem_original = img
                    self.imagem_sem_fundo = resultado
                    preview_orig = self.redimensionar_para_preview(img.copy())
                    preview_res = self.redimensionar_para_preview(resultado.copy())
                    fundo = self.criar_fundo_xadrez(preview_res.size)
                    composto = Image.alpha_composite(fundo, preview_res.convert("RGBA"))

                    self.photo_original = ImageTk.PhotoImage(preview_orig)
                    self.photo_resultado = ImageTk.PhotoImage(composto)

                    self.after(0, self._atualizar_preview_lote)

                except Exception as e:
                    erros += 1
                    print(f"Erro em {caminho}: {e}")

            msg = f"Lote finalizado: {sucesso} ok"
            if erros:
                msg += f", {erros} com erro"
            msg += f" — salvos em: {os.path.basename(self.pasta_saida_batch)}"

            self.after(0, lambda: self._finalizar_lote(msg, sucesso > 0, total))

        except Exception as e:
            self.after(0, lambda: self._finalizar_lote(f"Erro no lote: {e}", False, total))

    def _atualizar_preview_lote(self):
        self.label_preview_original.configure(image=self.photo_original, text="")
        self.label_preview_resultado.configure(image=self.photo_resultado, text="")

    def _finalizar_lote(self, mensagem, sucesso, total):
        # Completa a barra
        self.barra_progresso.set(1.0)
        self.label_progresso.configure(text=f"{total}/{total}  (100%) — Concluído")

        self.label_status.configure(
            text=mensagem,
            text_color=("green", "#2ecc71") if sucesso else ("red", "#e74c3c")
        )
        self._habilitar_controles()
        self.processando = False
        if sucesso:
            self.btn_salvar.configure(state="normal")
            self.btn_copiar.configure(state="normal")

        # Esconde a barra depois de alguns segundos
        self.after(4000, self._esconder_progresso)

    # ------------------------------------------------------------------
    # Processamento único
    # ------------------------------------------------------------------
    def iniciar_remocao(self):
        if self.processando or not self.caminho_entrada or self.imagem_original is None:
            return
        if self.fila_batch:
            return

        self.processando = True
        self._desabilitar_controles()
        self._esconder_progresso()

        self.label_status.configure(
            text=f"Processando com modelo '{self.modelo_atual}'... Aguarde",
            text_color=("orange", "#f39c12")
        )
        self.update_idletasks()

        thread = threading.Thread(target=self.remover_fundo, daemon=True)
        thread.start()

    def remover_fundo(self):
        try:
            if self.session is None:
                self.session = new_session(self.modelo_atual)

            resultado = remove(self.imagem_original, session=self.session)
            self.imagem_sem_fundo = resultado

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
        self.btn_copiar.configure(state="normal")
        self._habilitar_controles()
        self.processando = False

    def atualizar_resultado_erro(self, mensagem):
        self.label_status.configure(
            text=f"Erro ao processar: {mensagem}",
            text_color=("red", "#e74c3c")
        )
        self._habilitar_controles()
        self.processando = False

    # ------------------------------------------------------------------
    # Controles
    # ------------------------------------------------------------------
    def _desabilitar_controles(self):
        self.btn_selecionar.configure(state="disabled")
        self.btn_batch.configure(state="disabled")
        self.btn_processar.configure(state="disabled")
        self.btn_salvar.configure(state="disabled")
        self.btn_copiar.configure(state="disabled")
        self.combo_modelo.configure(state="disabled")

    def _habilitar_controles(self):
        self.btn_selecionar.configure(state="normal")
        self.btn_batch.configure(state="normal")
        self.btn_processar.configure(state="normal")
        self.combo_modelo.configure(state="normal")

    # ------------------------------------------------------------------
    # Salvar e Copiar
    # ------------------------------------------------------------------
    def salvar_imagem(self):
        if self.imagem_sem_fundo is None or self.processando:
            return

        caminho = filedialog.asksaveasfilename(
            defaultextension=".png",
            filetypes=[("Imagem PNG", "*.png")],
            title="Salvar imagem sem fundo",
            initialfile="sem_fundo.png"
        )
        if not caminho:
            return

        try:
            self.imagem_sem_fundo.save(caminho, "PNG")
            self.label_status.configure(
                text=f"Salvo em: {os.path.basename(caminho)}",
                text_color=("green", "#2ecc71")
            )
        except Exception as e:
            self.label_status.configure(
                text=f"Erro ao salvar: {e}",
                text_color=("red", "#e74c3c")
            )

    def copiar_para_clipboard(self):
        if self.imagem_sem_fundo is None or self.processando:
            return

        try:
            img = self.imagem_sem_fundo.convert("RGBA")
            fundo = Image.new("RGBA", img.size, (255, 255, 255, 255))
            composto = Image.alpha_composite(fundo, img).convert("RGB")

            output = io.BytesIO()
            composto.save(output, "BMP")
            data = output.getvalue()[14:]
            output.close()

            try:
                import win32clipboard
                win32clipboard.OpenClipboard()
                win32clipboard.EmptyClipboard()
                win32clipboard.SetClipboardData(win32clipboard.CF_DIB, data)
                win32clipboard.CloseClipboard()
                self.label_status.configure(
                    text="Imagem copiada para a área de transferência!",
                    text_color=("green", "#2ecc71")
                )
                return
            except ImportError:
                pass

            temp = Path.home() / ".bg_remover_temp.png"
            self.imagem_sem_fundo.save(temp, "PNG")

            import platform
            sistema = platform.system()

            if sistema == "Linux":
                os.system(f'xclip -selection clipboard -t image/png -i "{temp}" 2>/dev/null')
                self.label_status.configure(
                    text="Imagem enviada para a área de transferência (xclip).",
                    text_color=("green", "#2ecc71")
                )
            elif sistema == "Darwin":
                os.system(f'osascript -e \'set the clipboard to (read (POSIX file "{temp}") as «class PNGf»)\'')
                self.label_status.configure(
                    text="Imagem enviada para a área de transferência.",
                    text_color=("green", "#2ecc71")
                )
            else:
                self.label_status.configure(
                    text="Para copiar no Windows, instale: pip install pywin32",
                    text_color=("orange", "#f39c12")
                )

            self.after(3000, lambda: temp.unlink(missing_ok=True))

        except Exception as e:
            self.label_status.configure(
                text=f"Erro ao copiar: {e}",
                text_color=("red", "#e74c3c")
            )


if __name__ == "__main__":
    app = AppRemoverBG()
    app.mainloop()
