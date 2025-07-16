import os
import random
import requests
from bs4 import BeautifulSoup
import google.generativeai as genai
import tweepy

# --- FUNGSI UNTUK SCRAPING ---
def scrape_trends_from_trends24():
    """Mengambil 4 tren teratas dari trends24.in untuk United States."""
    url = "https://trends24.in/united-states/"
    try:
        response = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'})
        response.raise_for_status()  # Cek jika ada error HTTP
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Cari elemen 'li' di dalam 'ol' dengan class 'trend-card__list'
        trend_list = soup.select('ol.trend-card__list li a')
        
        # Ambil 4 teks tren teratas, hilangkan '#' jika ada
        trends = [trend.text.strip().replace('#', '') for trend in trend_list[:4]]
        
        if not trends:
            print("Peringatan: Tidak ada tren yang ditemukan. Mungkin struktur website berubah.")
            return None
            
        print(f"Tren yang ditemukan: {trends}")
        return trends
    except requests.exceptions.RequestException as e:
        print(f"Error saat mengakses trends24.in: {e}")
        return None

# --- FUNGSI UNTUK GENERASI KONTEN ---
def generate_post_with_gemini(trends, link):
    """Membuat konten post dengan Gemini API berdasarkan tren dan link."""
    # Ambil API Key dari environment variable (lebih aman)
    gemini_api_key = os.getenv('GEMINI_API_KEY')
    if not gemini_api_key:
        raise ValueError("GEMINI_API_KEY tidak ditemukan di environment variables!")
        
    genai.configure(api_key=gemini_api_key)
    model = genai.GenerativeModel('gemini-pro')
    
    # Buat prompt yang jelas untuk Gemini
    prompt = (
        f"Buat sebuah postingan singkat untuk X.com (Twitter) dalam bahasa Inggris yang relevan dengan topik atau tagar berikut: '{', '.join(trends)}'. "
        f"Postingan harus menarik, informatif, dan diakhiri dengan tagar yang relevan. "
        f"Sertakan link ini di akhir postingan: {link}. "
        "Jangan menambahkan URL lain selain yang saya berikan."
    )
    
    try:
        response = model.generate_content(prompt)
        print("Konten berhasil dibuat oleh Gemini.")
        return response.text
    except Exception as e:
        print(f"Error saat menghubungi Gemini API: {e}")
        return None

# --- FUNGSI UNTUK MENDAPATKAN LINK ---
def get_random_link(filename="links.txt"):
    """Membaca file dan memilih satu link secara acak."""
    try:
        with open(filename, 'r') as f:
            links = [line.strip() for line in f if line.strip()]
        return random.choice(links) if links else None
    except FileNotFoundError:
        print(f"Error: File '{filename}' tidak ditemukan.")
        return None

# --- FUNGSI UNTUK POSTING KE X.COM ---
def post_to_x(text_to_post):
    """Memposting teks ke X.com menggunakan API v2."""
    try:
        client = tweepy.Client(
            bearer_token=os.getenv('X_BEARER_TOKEN'),
            consumer_key=os.getenv('X_API_KEY'),
            consumer_secret=os.getenv('X_API_SECRET'),
            access_token=os.getenv('X_ACCESS_TOKEN'),
            access_token_secret=os.getenv('X_ACCESS_TOKEN_SECRET')
        )
        response = client.create_tweet(text=text_to_post)
        print(f"Berhasil memposting tweet ID: {response.data['id']}")
    except Exception as e:
        print(f"Error saat memposting ke X.com: {e}")

# --- FUNGSI UTAMA ---
if __name__ == "__main__":
    print("Memulai proses auto-posting...")
    
    # 1. Scrape tren
    top_trends = scrape_trends_from_trends24()
    
    if top_trends:
        # 2. Ambil link acak
        random_link = get_random_link()
        
        if random_link:
            # 3. Buat konten post dengan Gemini
            post_content = generate_post_with_gemini(top_trends, random_link)
            
            if post_content:
                # 4. Posting ke X.com
                post_to_x(post_content)
    
    print("Proses selesai.")
