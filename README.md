# Nakarat — Müzik Tahmin Oyunu

Kategori seç (Pop, Arabesk, Rock, Rap, Türk Halk Müziği, Caz, Elektronik,
Klasik) → Yerel (ülke seç) ya da Evrensel → 30 saniyelik bir önizleme
çalar → şarkının adını ve sanatçısını tahmin etmeye çalışırsın.

## Nasıl çalışır?

Şarkılar sabit bir dosya değil; Apple'ın herkese açık, anahtar
gerektirmeyen **iTunes Arama API**'sinden (`itunes.apple.com/search`)
canlı olarak çekilir. Bu yüzden:

- Çalıştırmak için internet bağlantısı gerekir.
- Aynı kategori + ülke kombinasyonunu tekrar seçtiğinde farklı bir şarkı
  gelebilir (rastgele seçiliyor).
- Bazı tür + ülke eşleşmelerinde (ör. Arabesk + Japonya) sonuç az/garip
  çıkabilir — API'nin o mağazadaki kataloğuna bağlı, bu normal.
- Doğru cevap tarayıcıya hemen gönderilmiyor; sunucu tarafında (oturumda)
  tutulup tahminle orada karşılaştırılıyor.

## Kurulum

1. Python 3.9+ gerekir.
2. Bu klasörde bir terminal aç.
3. (Önerilir) Sanal ortam oluştur:
   ```
   python -m venv venv
   venv\Scripts\activate        # Windows
   source venv/bin/activate     # macOS / Linux
   ```
4. Bağımlılıkları kur:
   ```
   pip install -r requirements.txt
   ```

## Çalıştırma

```
python app.py
```

Tarayıcıda **http://127.0.0.1:5000** adresini aç.

## Genişletme fikirleri

- Yeni kategori eklemek için `app.py` içindeki `CATEGORIES` sözlüğüne
  bir satır eklemen yeterli (`"k-pop": {"label": "K-Pop", "term": "kpop hits", "theme": "pop"}` gibi — `theme` için `static/style.css` içine yeni bir `.theme-...` gradyanı eklemen gerekir).
- Yeni ülke eklemek için `COUNTRIES` sözlüğüne iTunes mağaza kodunu
  (ör. `"NL": "Hollanda"`) eklemen yeterli.
- Tahmin eşiğini (`MATCH_THRESHOLD`, şu an 0.72) `app.py` içinden
  değiştirerek oyunu daha kolay/zor yapabilirsin.
- Round sayısı sınırlı bir "oyun modu" (ör. 10 turda bitiş ekranı) veya
  bir skor tablosu eklenebilir.
