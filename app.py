"""
Nakarat — Müzik Tahmin Oyunu
============================
Flask backend. Kullanıcının seçtiği kategoriye (pop, arabesk, ...) ve
bölgeye (yerel/ülke ya da evrensel) göre Apple'ın herkese açık, anahtar
gerektirmeyen iTunes Arama API'sinden 30 saniyelik bir şarkı önizlemesi
çeker. Şarkının adı/sanatçısı tarayıcıya gönderilmez; oturumda saklanır
ve kullanıcı tahmin gönderdiğinde sunucu tarafında karşılaştırılır.
"""

import random
import re
import secrets
from difflib import SequenceMatcher

import requests
from flask import Flask, jsonify, render_template, request, session

app = Flask(__name__)
app.secret_key = secrets.token_hex(16)

ITUNES_SEARCH_URL = "https://itunes.apple.com/search"
REQUEST_TIMEOUT = 8  # saniye
RESULTS_PER_QUERY = 25
MATCH_THRESHOLD = 0.72  # tahmin doğruluğu için benzerlik eşiği (0-1)

# Kategori anahtarı -> görünen ad, iTunes arama terimi, kart rengi teması.
# Yeni bir kategori eklemek için buraya bir satır eklemen yeterli.
CATEGORIES = {
    "pop":        {"label": "Pop",              "term": "pop hits",         "theme": "pop"},
    "arabesk":    {"label": "Arabesk",           "term": "arabesk",          "theme": "arabesk"},
    "rock":       {"label": "Rock",              "term": "rock hits",        "theme": "rock"},
    "rap":        {"label": "Rap / Hip-Hop",     "term": "rap hits",         "theme": "rap"},
    "halk":       {"label": "Türk Halk Müziği",  "term": "türk halk müziği", "theme": "halk"},
    "caz":        {"label": "Caz",               "term": "jazz",             "theme": "caz"},
    "elektronik": {"label": "Elektronik",        "term": "electronic dance", "theme": "elektronik"},
    "klasik":     {"label": "Klasik",            "term": "classical music",  "theme": "klasik"},
}

# Ülke kodu -> görünen ad ("Yerel" seçildiğinde gösterilen liste).
COUNTRIES = {
    "TR": "Türkiye", "US": "Amerika", "GB": "İngiltere", "DE": "Almanya",
    "FR": "Fransa", "ES": "İspanya", "IT": "İtalya", "KR": "Güney Kore",
    "IN": "Hindistan", "JP": "Japonya",
}

DEFAULT_COUNTRY = "US"  # "Evrensel" seçildiğinde kullanılan mağaza


def normalize(text: str) -> str:
    """Tahmin karşılaştırması için metni sadeleştirir: parantez içi ekleri
    ((feat. ...), (Remastered) gibi) atar, Türkçe karakterleri ASCII'ye
    indirger, küçük harfe çevirir ve noktalamayı temizler."""
    if not text:
        return ""
    text = re.sub(r"[\(\[].*?[\)\]]", " ", text)
    tr_map = str.maketrans("çğıöşüÇĞİÖŞÜ", "cgiosuCGIOSU")
    text = text.translate(tr_map).lower()
    text = re.sub(r"[^a-z0-9 ]", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def similarity(a: str, b: str) -> float:
    return SequenceMatcher(None, normalize(a), normalize(b)).ratio()


def fetch_song(term: str, country: str):
    """iTunes Arama API'sinden önizleme linki olan rastgele bir şarkı döner.
    Sonuç yoksa (ya da istek başarısızsa) None döner."""
    params = {
        "term": term,
        "country": country,
        "media": "music",
        "entity": "song",
        "limit": RESULTS_PER_QUERY,
    }
    try:
        resp = requests.get(ITUNES_SEARCH_URL, params=params, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
        data = resp.json()
    except (requests.RequestException, ValueError):
        return None

    results = [r for r in data.get("results", []) if r.get("previewUrl")]
    return random.choice(results) if results else None


@app.route("/")
def home():
    return render_template("index.html", categories=CATEGORIES, countries=COUNTRIES)


@app.route("/api/round")
def api_round():
    category = request.args.get("category", "")
    scope = request.args.get("scope", "evrensel")
    country = request.args.get("country", DEFAULT_COUNTRY).upper()

    cat = CATEGORIES.get(category)
    if not cat:
        return jsonify({"error": "Geçersiz kategori."}), 400

    if scope != "yerel" or country not in COUNTRIES:
        country = DEFAULT_COUNTRY

    song = fetch_song(cat["term"], country)
    if song is None and country != DEFAULT_COUNTRY:
        # Bazı kategori + ülke kombinasyonlarında sonuç az olabilir; genel
        # mağazayla bir kez daha dene.
        song = fetch_song(cat["term"], DEFAULT_COUNTRY)
    if song is None:
        return jsonify({"error": "Bu kategori için şarkı bulunamadı. Tekrar dener misin?"}), 404

    round_token = secrets.token_hex(8)
    session["round"] = {
        "token": round_token,
        "title": song.get("trackName", ""),
        "artist": song.get("artistName", ""),
    }

    artwork = song.get("artworkUrl100", "")
    if artwork:
        artwork = artwork.replace("100x100", "600x600")

    return jsonify({
        "round_token": round_token,
        "preview_url": song.get("previewUrl"),
        "artwork": artwork,
        "album": song.get("collectionName", ""),
    })


@app.route("/api/guess", methods=["POST"])
def api_guess():
    data = request.get_json(silent=True) or {}
    round_data = session.get("round")

    if not round_data or not round_data.get("token") or data.get("round_token") != round_data["token"]:
        return jsonify({"error": "Bu tur artık geçerli değil. Yeni bir şarkı getir."}), 400

    title_correct = similarity(data.get("title_guess", ""), round_data["title"]) >= MATCH_THRESHOLD
    artist_correct = similarity(data.get("artist_guess", ""), round_data["artist"]) >= MATCH_THRESHOLD
    points = int(title_correct) + int(artist_correct)

    session["score"] = session.get("score", 0) + points
    session["rounds_played"] = session.get("rounds_played", 0) + 1

    # Aynı tur için ikinci kez puan verilmesin.
    round_data["token"] = ""
    session["round"] = round_data

    return jsonify({
        "title_correct": title_correct,
        "artist_correct": artist_correct,
        "correct_title": round_data["title"],
        "correct_artist": round_data["artist"],
        "points": points,
        "score": session["score"],
        "rounds_played": session["rounds_played"],
    })


@app.route("/api/reset", methods=["POST"])
def api_reset():
    session["score"] = 0
    session["rounds_played"] = 0
    return jsonify({"score": 0, "rounds_played": 0})


if __name__ == "__main__":
    app.run(debug=True, port=5000)
