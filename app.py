import tkinter as tk
from tkinter import ttk, messagebox
from pytube import YouTube
import threading
import os
from moviepy.editor import VideoFileClip, AudioFileClip
import itertools
from pathvalidate import sanitize_filename
from PIL import Image, ImageTk

class Downloader(tk.Tk):
    def __init__(self):
        super().__init__()
        self.download_folder = os.path.join(os.path.expanduser("~"), "Downloads")
        if not os.path.exists(self.download_folder):
            os.makedirs(self.download_folder)

        # Configuração da Janela Principal
        self.title('Youtube Downloader')
        self.geometry('500x250')
        self.minsize(500,250)
        self.maxsize(500,250)
        self.configure(bg='#2e2e2e')

        # Adicionando a logo
        self.logo_canvas = tk.Canvas(self, width=400, height=100, bg='#2e2e2e', highlightthickness=0)
        self.logo_canvas.pack(anchor=tk.NW, padx=10, pady=10)  # Ancorando no canto superior direito

        # Carregando a imagem da logo
        logo_image = Image.open("description.png")  
        logo_image = logo_image.resize((400, 160))
        self.logo_image = ImageTk.PhotoImage(logo_image)
        self.logo_canvas.create_image(0, 0, anchor=tk.NW, image=self.logo_image)

        # Estilos personalizados para interface
        self.style = ttk.Style()
        self.style.configure('TFrame', background='#2e2e2e') # Cor de fundo dos frames
        self.style.configure('TButton', background='black', foreground='black') # Cores do botão
        self.style.configure('TLabel', background='#2e2e2e', foreground='white') # Cores dos rótulos
        self.style.configure('TRadiobutton', background='#2e2e2e', foreground='white') # Cores dos radio buttons
        self.style.configure('Horizontal.TProgressbar', background='navy') # Cor da barra de progresso

        # Elementos de interface do usuário
        self.url_frame = ttk.Frame(self)
        self.url_label = ttk.Label(self.url_frame, text='YouTube URL:')
        self.url_entry = ttk.Entry(self.url_frame, width=50)

        self.option_frame = ttk.Frame(self)
        self.option = tk.StringVar()
        self.radio_mp3 = ttk.Radiobutton(self.option_frame, text='MP3', variable=self.option, value='mp3')
        self.radio_mp4 = ttk.Radiobutton(self.option_frame, text='MP4', variable=self.option, value='mp4')

        self.download_button = ttk.Button(self.option_frame, text='Download', command=self.download)

        self.loading_label = ttk.Label(self.option_frame, text='')

        # Barra de progresso: inicialmente oculta
        self.progress = ttk.Progressbar(self, length=400, mode='determinate', style='Horizontal.TProgressbar')

        # Layout dos Elementos
        self.url_frame.pack(padx=10, pady=20, fill='both')
        self.url_label.pack(side=tk.LEFT)
        self.url_entry.pack(side=tk.LEFT)

        self.option_frame.pack(padx=10, pady=5, fill='both')
        self.radio_mp3.pack(side=tk.LEFT)
        self.radio_mp4.pack(side=tk.LEFT)
        self.download_button.pack(side=tk.LEFT)
        self.loading_label.pack(side=tk.LEFT)

    def progress_func(self, stream, chunk, bytes_remaining):
        # Função para atualizar a barra de progresso durante o download
        total_size = stream.filesize
        bytes_downloaded = total_size - bytes_remaining
        percentage = (bytes_downloaded / total_size) * 100
        self.progress['value'] = percentage
        self.update_idletasks()

    def download(self):
        # Função chamada quando o botão de download é clicado
        url = self.url_entry.get()
        option = self.option.get()

        if not url or not option:
            messagebox.showerror('Error', 'All fields must be filled')
            return
        
        self.progress['value'] = 0

        # Repack da barra de progresso quando o download começa
        self.progress.pack(pady=10)

        if option == 'mp4':
            self.thread = threading.Thread(target=self.download_video, args=(url,))
        else:
            self.thread = threading.Thread(target=self.download_audio, args=(url,))

        self.thread.start()

    def download_video(self, url):
        # Função para baixar videos
        try:
            current_dir = os.getcwd()  # Obter o diretório de trabalho atual
            os.chdir(self.download_folder)  # Mudar para a área de trabalho

            yt = YouTube(url)
            yt.register_on_progress_callback(self.progress_func)
            video = yt.streams.filter(only_video=True, file_extension='mp4').order_by('resolution').desc().first()
            audio = yt.streams.get_audio_only()

            video_file = video.download(output_path=self.download_folder, filename='video')
            audio_file = audio.download(output_path=self.download_folder, filename='audio')

            video_clip = VideoFileClip(video_file)
            audio_clip = AudioFileClip(audio_file)

            final_clip = video_clip.set_audio(audio_clip)

            loading_text = 'Merging Video and Audio...'
            loading_animation = itertools.cycle(['|','/','-','\\'])

            def animate_loading():
                self.loading_label.config(text=loading_text + next(loading_animation))
                if not self.thread.is_alive():
                    self.download_button.config(state='normal')
                    self.loading_label.config(text='')
                else:
                    self.after(200, animate_loading)

            self.url_entry.config(state='disabled')
            self.download_button.config(state='disabled')
            self.loading_label.pack(side=tk.LEFT)
            self.loading_label.config(text=loading_text + next(loading_animation))
            self.after(200, animate_loading)

            final_clip.write_videofile(sanitize_filename(yt.title + '.mp4'))

            os.remove(video_file)
            os.remove(audio_file)
            os.chdir(current_dir)  # Retornar ao diretório original após o download

            messagebox.showinfo('Success', 'Video Completed')
        except Exception as e:
            messagebox.showerror('Error', str(e))
        finally:
            self.url_entry.config(state='normal')
            self.download_button.config(state='normal')
            self.loading_label.config(text='')
            self.progress.pack_forget() # Resetar a barra de progresso quando o download for concluido
            self.url_entry.delete(0, 'end')  # Limpar o campo de entrada de URL
    
    def download_audio(self, url):
        # Função para baixar apenas o áudio
        try:
            current_dir = os.getcwd()  # Obter o diretório de trabalho atual
            os.chdir(self.download_folder)  # Mudar para a área de trabalho

            yt = YouTube(url)
            yt.register_on_progress_callback(self.progress_func)
            yt = yt.streams.filter(only_audio=True).first()
            out_file = yt.download(output_path=self.download_folder, filename='audio')

            new_file = sanitize_filename(yt.title + '.mp3')
            os.rename(out_file, new_file)

            loading_text = 'Downloading...'
            loading_animation = itertools.cycle(['|','/','-','\\'])

            def animate_loading():
                self.loading_label.config(text=loading_text + next(loading_animation))
                if not self.thread.is_alive():
                    self.download_button.config(state='normal')
                    self.loading_label.config(text='')
                else:
                    self.after(200, animate_loading)

            self.url_entry.config(state='disabled')
            self.download_button.config(state='disabled')
            self.loading_label.pack(side=tk.LEFT)
            self.loading_label.config(text=loading_text + next(loading_animation))
            self.after(200, animate_loading)

            os.chdir(current_dir)  # Retornar ao diretório original após o download

            messagebox.showinfo("Success", "Download completed")
        except Exception as e:
            messagebox.showerror("Error", str(e))
        finally:
            self.url_entry.config(state='normal')
            self.download_button.config(state='normal')
            self.loading_label.config(text='')
            self.progress.pack_forget()
            self.url_entry.delete(0, 'end')  # Limpar o campo de entrada de URL

if __name__== '__main__':
    app = Downloader()
    app.mainloop()