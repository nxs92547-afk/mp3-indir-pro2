import os
import sys
import subprocess
import threading

# ==========================================
# 1. AŞAMA: OTO-KURULUM (BOOTSTRAP) SİSTEMİ
# ==========================================
def gereksinimleri_kontrol_et_ve_kur():
    gerekli_kutuphaneler = {
        "kivy": "kivy",
        "yt_dlp": "yt-dlp"
    }
    
    eksikler = []
    for modul_adi, pip_adi in gerekli_kutuphaneler.items():
        try:
            __import__(modul_adi)
        except ImportError:
            eksikler.append(pip_adi)
            
    if eksikler:
        print("--------------------------------------------------")
        print("İLK KURULUM: Eksik kütüphaneler tespit edildi.")
        print(f"İndiriliyor: {', '.join(eksikler)}")
        print("Bu işlem internet hızınıza bağlı olarak birkaç dakika sürebilir...")
        print("--------------------------------------------------")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", *eksikler])
            print("Kurulum başarıyla tamamlandı! Uygulama başlatılıyor...\n")
        except Exception as e:
            print(f"Kurulum sırasında hata oluştu: {e}")
            sys.exit(1)

gereksinimleri_kontrol_et_ve_kur()


# ==========================================
# 2. AŞAMA: KIVY ARAYÜZÜ VE UYGULAMA MANTIĞI
# ==========================================
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.uix.image import AsyncImage 
from kivy.graphics import Color, RoundedRectangle
from kivy.core.window import Window
from kivy.clock import Clock
from kivy.utils import get_color_from_hex

# --- GÖRSEL TEMALAR (Renk Paleti ve Stiller) ---
DARK_BG = get_color_from_hex('#121212')
ACCENT_RED = get_color_from_hex('#E53935')
SECONDARY_GRAY = get_color_from_hex('#333333')
TEXT_WHITE = get_color_from_hex('#FFFFFF')
TEXT_GRAY = get_color_from_hex('#B0B0B0')

Window.clearcolor = DARK_BG

# --- ÖZEL WIDGET'LAR ---

class RoundedButton(Button):
    def __init__(self, bg_color=ACCENT_RED, text_color=TEXT_WHITE, radius=15, **kwargs):
        super().__init__(**kwargs)
        self.background_color = [0, 0, 0, 0]
        self.background_normal = ''
        self.color = text_color
        self.bold = True
        self.font_size = '16sp'
        self.radius = radius
        self.bg_color = bg_color
        self.bind(pos=self.update_canvas, size=self.update_canvas)

    def update_canvas(self, *args):
        self.canvas.before.clear()
        with self.canvas.before:
            Color(*self.bg_color)
            self.rect = RoundedRectangle(pos=self.pos, size=self.size, radius=[self.radius])

# YENİ VE KESİN ÇÖZÜM: Yazı ve Arka Planı Birbirinden Ayırdık (BoxLayout Wrapper)
class RoundedTextInput(BoxLayout):
    def __init__(self, hint_text='', radius=10, **kwargs):
        super().__init__(**kwargs)
        self.radius = radius
        
        # İçine şeffaf ve bağımsız bir yazı kutusu ekliyoruz. Bu sayede Kivy arka planla yazıyı karıştırmaz.
        self.text_input = TextInput(
            hint_text=hint_text,
            multiline=False,
            background_normal='', 
            background_active='',
            background_color=[0, 0, 0, 0], 
            foreground_color=[1, 1, 1, 1], # BEMBEYAZ YAZI RENGİ
            cursor_color=[1, 1, 1, 1],     # BEMBEYAZ İMLEÇ
            hint_text_color=[0.6, 0.6, 0.6, 1], 
            font_size='16sp',
            padding=[15, 18, 15, 0] 
        )
        self.add_widget(self.text_input)
        
        self.bind(pos=self.update_canvas, size=self.update_canvas)

    def update_canvas(self, *args):
        self.canvas.before.clear()
        with self.canvas.before:
            Color(0.2, 0.2, 0.2, 1) # Yuvarlak kutunun gri arka planı
            RoundedRectangle(pos=self.pos, size=self.size, radius=[self.radius])

    # Ana kodun yazdığın metni okuyabilmesi için gerekli bağlantı
    @property
    def text(self):
        return self.text_input.text


class ResultItem(BoxLayout):
    def __init__(self, index, title, url, thumbnail_url, download_callback, **kwargs):
        super().__init__(orientation='horizontal', size_hint_y=None, height=80, padding=[10, 5], spacing=10, **kwargs)
        self.url = url
        self.download_callback = download_callback

        if thumbnail_url:
            self.add_widget(AsyncImage(source=thumbnail_url, size_hint=(None, 1), width=120, pos_hint={'center_y': 0.5}))
        else:
            self.add_widget(AsyncImage(source='atlas://data/images/defaulttheme/minus', size_hint=(None, None), size=(40, 40), pos_hint={'center_y': 0.5}))

        text_layout = BoxLayout(orientation='vertical', size_hint_x=0.5)
        text_layout.add_widget(Label(text=f"{index}. {title[:35]}...", color=TEXT_WHITE, bold=True, font_size='14sp', halign='left', text_size=(Window.width * 0.4, None)))
        text_layout.add_widget(Label(text="Sanatçı Adı", color=TEXT_GRAY, font_size='12sp', halign='left', text_size=(Window.width * 0.4, None)))
        self.add_widget(text_layout)

        download_btn = RoundedButton(text='SES İNDİR', bg_color=SECONDARY_GRAY, size_hint=(None, 0.7), width=100, pos_hint={'center_y': 0.5}, font_size='12sp')
        download_btn.bind(on_press=self.on_download_press)
        self.add_widget(download_btn)

    def on_download_press(self, instance):
        self.download_callback(self.url)

# --- ANA UYGULAMA SINIFI ---
class YtIndiriciProApp(App):
    def build(self):
        self.title = 'Müzik Bulucu Pro'
        
        self.main_layout = BoxLayout(orientation='vertical', padding=15, spacing=15)

        header_layout = BoxLayout(orientation='horizontal', size_hint=(1, 0.08))
        header_layout.add_widget(Label(text='[b]Müzik Bulucu [color=E53935]Pro[/color][/b]', markup=True, font_size='22sp', halign='left', text_size=(Window.width * 0.8, None)))
        self.main_layout.add_widget(header_layout)

        self.url_input = RoundedTextInput(hint_text='Şarkı Adı veya YouTube Linki...', size_hint=(1, 0.1))
        self.main_layout.add_widget(self.url_input)

        self.aksiyon_btn = RoundedButton(text='HIZLI ARA (Listele)', size_hint=(1, 0.1))
        self.aksiyon_btn.bind(on_press=self.baslat_yonlendirici)
        self.main_layout.add_widget(self.aksiyon_btn)

        self.kurulum_btn = RoundedButton(text='Youtube İndiriciyi Güncelle (yt-dlp)', size_hint=(1, 0.08), font_size='13sp', bg_color=(0.15, 0.15, 0.15, 1))
        self.kurulum_btn.bind(on_press=self.manuel_guncelle)
        self.main_layout.add_widget(self.kurulum_btn)

        self.status_panel = BoxLayout(orientation='vertical', size_hint=(1, 0.12), spacing=3)
        self.durum_yazisi = Label(text='[b]DURUM:[/b] Hazır', markup=True, font_size='14sp', color=TEXT_GRAY, halign='left', text_size=(Window.width * 0.9, None))
        self.status_panel.add_widget(self.durum_yazisi)
        
        self.download_details = Label(text='', font_size='12sp', color=TEXT_GRAY, halign='left', text_size=(Window.width * 0.9, None))
        self.status_panel.add_widget(self.download_details)
        self.main_layout.add_widget(self.status_panel)

        results_header = Label(text='Arama Sonuçları', font_size='16sp', bold=True, color=TEXT_WHITE, halign='left', text_size=(Window.width * 0.9, None), size_hint=(1, None), height=30)
        self.main_layout.add_widget(results_header)
        
        self.scroll = ScrollView(size_hint=(1, 0.4))
        self.sonuclar_kutusu = BoxLayout(orientation='vertical', spacing=10, size_hint_y=None)
        self.sonuclar_kutusu.bind(minimum_height=self.sonuclar_kutusu.setter('height'))
        self.scroll.add_widget(self.sonuclar_kutusu)
        self.main_layout.add_widget(self.scroll)

        return self.main_layout

    def mesaj_guncelle(self, mesaj, details=''):
        self.durum_yazisi.text = mesaj
        self.download_details.text = details

    def manuel_guncelle(self, instance):
        self.mesaj_guncelle("[color=B0B0B0]DURUM:[/color] yt-dlp güncelleniyor, lütfen bekleyin...")
        self.kurulum_btn.disabled = True
        threading.Thread(target=self._arka_planda_guncelle).start()

    def _arka_planda_guncelle(self):
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "yt-dlp", "--upgrade"])
            Clock.schedule_once(lambda dt: self.mesaj_guncelle("[color=B0B0B0]DURUM:[/color] Güncelleme Tamamlandı!"))
        except:
            Clock.schedule_once(lambda dt: self.mesaj_guncelle("[color=E53935]DURUM: Güncelleme hatası![/color]"))
        finally:
            Clock.schedule_once(lambda dt: setattr(self.kurulum_btn, 'disabled', False))

    def baslat_yonlendirici(self, instance):
        girdi = self.url_input.text.strip()
        if not girdi:
            self.mesaj_guncelle("[color=E53935]DURUM: Lütfen giriş yapın.[/color]")
            return

        self.sonuclar_kutusu.clear_widgets()
        self.aksiyon_btn.disabled = True

        if "http" in girdi or "youtube.com" in girdi or "youtu.be" in girdi:
            if "&" in girdi: girdi = girdi.split("&")[0]
            self.mesaj_guncelle("[color=B0B0B0]DURUM:[/color] Link algılandı, analiz ediliyor...")
            threading.Thread(target=self.ses_indir, args=(girdi,)).start()
        else:
            self.mesaj_guncelle("[color=B0B0B0]DURUM:[/color] YouTube aranıyor, bekleyin...")
            threading.Thread(target=self.arama_yap, args=(girdi,)).start()

    def arama_yap(self, kelime):
        try:
            import yt_dlp
            ydl_opts = {'extract_flat': False, 'quiet': True, 'no_warnings': True} 
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                bilgi = ydl.extract_info(f"ytsearch5:{kelime}", download=False)
                sonuclar = bilgi.get('entries', [])
            Clock.schedule_once(lambda dt: self.sonuclari_goster(sonuclar))
        except Exception as e:
            Clock.schedule_once(lambda dt: self.mesaj_guncelle(f"[color=E53935]DURUM: Arama hatası![/color]"))
            print(f"HATA: {e}")
        finally:
            Clock.schedule_once(lambda dt: setattr(self.aksiyon_btn, 'disabled', False))

    def sonuclari_goster(self, sonuclar):
        if not sonuclar:
            self.mesaj_guncelle("[color=B0B0B0]DURUM:[/color] Sonuç bulunamadı.")
            return
        
        self.mesaj_guncelle("[color=B0B0B0]DURUM:[/color] Lütfen indirmek istediğiniz sesi seçin:")
        for index, video in enumerate(sonuclar):
            thumbnail_url = video.get('thumbnail') or video.get('thumbnails', [{}])[0].get('url')
            
            # YENİ: videoplayback mp4 hatasını önlemek için ham URL yerine orijinal YouTube ID'sini alıyoruz
            video_id = video.get('id')
            dogru_youtube_linki = f"https://www.youtube.com/watch?v={video_id}"
            
            self.sonuclar_kutusu.add_widget(ResultItem(
                index + 1,
                video.get('title', 'İsimsiz'),
                dogru_youtube_linki, 
                thumbnail_url,
                self.secilen_videoyu_indir
            ))

    def secilen_videoyu_indir(self, url):
        self.sonuclar_kutusu.clear_widgets()
        self.mesaj_guncelle("[color=B0B0B0]DURUM:[/color] İndirme başlatılıyor...")
        self.aksiyon_btn.disabled = True
        threading.Thread(target=self.ses_indir, args=(url,)).start()

    def ses_indir(self, url):
        try:
            import yt_dlp
            indirme_klasoru = "Music" if not os.path.exists("/storage/emulated/0/Music") else "/storage/emulated/0/Music"
            if not os.path.exists(indirme_klasoru) and indirme_klasoru == "Music":
                os.makedirs(indirme_klasoru)
                
            def progress_hook(d):
                if d['status'] == 'downloading':
                    try:
                        percent = d.get('_percent_str', '0%').strip()
                        speed = d.get('_speed_str', 'N/A')
                        eta = d.get('_eta_str', 'N/A')
                        Clock.schedule_once(lambda dt: self.mesaj_guncelle(
                            f"[color=B0B0B0]DURUM: İndiriliyor... {percent}[/color]",
                            f"Hız: {speed} | Kalan Süre: {eta}"
                        ))
                    except: pass

            ydl_opts = {
                # YENİ: Video (mp4) inmesini engeller. Sadece m4a formatında saf ve yüksek kaliteli Ses indirir.
                'format': 'm4a/bestaudio/best',
                'outtmpl': f'{indirme_klasoru}/%(title)s.%(ext)s',
                'noplaylist': True,
                'quiet': True,
                'no_warnings': True,
                'progress_hooks': [progress_hook],
            }

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])

            Clock.schedule_once(lambda dt: self.mesaj_guncelle("✅ [color=FFFFFF]Başarılı![/color]", f"Şarkı '{indirme_klasoru}' klasörüne kaydedildi."))
        except Exception as e:
            Clock.schedule_once(lambda dt: self.mesaj_guncelle("[color=E53935]DURUM: İndirme hatası![/color]"))
            print(f"HATA: {e}")
        finally:
            Clock.schedule_once(lambda dt: setattr(self.aksiyon_btn, 'disabled', False))

if __name__ == '__main__':
    YtIndiriciProApp().run()
