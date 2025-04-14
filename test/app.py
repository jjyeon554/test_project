import os
import requests
import qrcode
import base64
from io import BytesIO
from flask import Flask, render_template, request, redirect, url_for
from bs4 import BeautifulSoup
from googletrans import Translator

app = Flask(__name__)

# API 키
GOOGLE_API_KEY = "AIzaSyA-Ke9_zTdLuCUQz6-GfALDCnJUmwyICpQ"
GOOGLE_CX = "15f1bb801c2b0460d"
NAVER_CLIENT_ID = "7hnrArrstKNOHAqjnt3Y"
NAVER_CLIENT_SECRET = "d0Ee7D74EB"

translator = Translator()

# 썸네일 추출
def get_thumbnail(url):
    try:
        html = requests.get(url, timeout=3).text
        soup = BeautifulSoup(html, 'html.parser')
        og_image = soup.find("meta", property="og:image")
        return og_image["content"] if og_image else url_for('static', filename='default_thumb.png')
    except:
        return url_for('static', filename='default_thumb.png')

# 사이트 내용 추출
def extract_text_from_url(url):
    try:
        html = requests.get(url, timeout=3).text
        soup = BeautifulSoup(html, "html.parser")
        paragraphs = soup.find_all("p")
        return " ".join(p.get_text() for p in paragraphs if p.get_text().strip())
    except:
        return "사이트 내용을 가져올 수 없습니다."

# 번역
def translate_text(text, dest_lang):
    return translator.translate(text, dest=dest_lang).text

# QR 생성
def generate_qrcode(url):
    qr = qrcode.make(url)
    img_io = BytesIO()
    qr.save(img_io, 'PNG')
    img_io.seek(0)
    return base64.b64encode(img_io.read()).decode('utf-8')

# 구글 검색
def google_search(query):
    url = f"https://www.googleapis.com/customsearch/v1?q={query}&key={GOOGLE_API_KEY}&cx={GOOGLE_CX}"
    data = requests.get(url).json()
    results = []
    for item in data.get("items", []):
        results.append({
            "title": item["title"],
            "link": item["link"],
            "thumbnail": get_thumbnail(item["link"]),
            "source": "Google"
        })
    return results

# 네이버 검색
def naver_search(query):
    url = "https://openapi.naver.com/v1/search/news.json"
    headers = {
        "X-Naver-Client-Id": NAVER_CLIENT_ID,
        "X-Naver-Client-Secret": NAVER_CLIENT_SECRET
    }
    params = {"query": query, "display": 10, "sort": "sim"}
    data = requests.get(url, headers=headers, params=params).json()
    results = []
    for item in data.get("items", []):
        results.append({
            "title": item["title"],
            "link": item["link"],
            "thumbnail": get_thumbnail(item["link"]),
            "source": "Naver"
        })
    return results

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        query = request.form.get("query")
        action = request.form.get("action")
        selected_urls = request.form.getlist("selected_urls")
        lang = request.form.get("lang")

        if action == "search":
            google_results = google_search(query)
            naver_results = naver_search(query)
            return render_template("index.html", results=google_results + naver_results, query=query)

        if not selected_urls:
            return render_template("index.html", error="⚠️ 하나 이상의 검색 결과를 선택해주세요.", results=[], query=query)

        if action == "translate":
            texts = [extract_text_from_url(url) for url in selected_urls]
            translated = [translate_text(text, lang) for text in texts]
            return render_template("translation.html", urls=selected_urls, translated=translated, lang=lang)


        if action == "qrcode":
            qrcodes = [(url, generate_qrcode(url)) for url in selected_urls]
            return render_template("qrcode_result.html", qrcodes=qrcodes)

    return render_template("index.html", results=[], query="")

if __name__ == "__main__":
    app.run(debug=True)
