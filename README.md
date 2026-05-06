 Finansal Analiz Platformu (Financial Analysis Platform)

Finansal veri yönetimi, yapay zeka (AI) destekli OCR ve finansal analiz platformu. Bu platform, finansal belgeleri (PDF, Excel vb.) işleyerek şirketlerin finansal durumlarını analiz etmeyi, abonelik süreçlerini yönetmeyi ve bir yönetici (admin) paneli üzerinden platformu kontrol etmeyi sağlar.

## 🚀 Özellikler

- **Gelişmiş AI Destekli OCR**: Gemini API kullanılarak finansal belgelerden (PDF, Excel, vb.) veri çıkarımı.
- **Şirket ve Finansal Rapor Yönetimi**: Şirketlere ait finansal raporların yüklenmesi, analiz edilmesi ve arşivlenmesi.
- **Kullanıcı ve Rol Yönetimi**: JWT tabanlı güvenli kimlik doğrulama ve yetkilendirme (Admin, Standart Kullanıcı vb.).
- **Abonelik Sistemi**: Kullanıcılar için abonelik planları ve limit yönetimleri.
- **Bildirim Sistemi**: Kullanıcı eylemleri ve analiz sonuçları için anlık bildirim altyapısı.
- **Admin Paneli**: Tüm sistem istatistiklerinin, kullanıcıların ve raporların yönetilebildiği kapsamlı kontrol paneli.
- **Güvenlik**: CORS politikaları, Rate Limiting (opsiyonel eklenebilir) ve Security Header (XSS vb. korumalar) entegrasyonu.

## 🛠️ Teknolojiler

**Backend:**
- [FastAPI](https://fastapi.tiangolo.com/): Yüksek performanslı modern Python web framework'ü.
- [PostgreSQL](https://www.postgresql.org/): İlişkisel veritabanı.
- [SQLAlchemy](https://www.sqlalchemy.org/) & [Alembic](https://alembic.sqlalchemy.org/): Veritabanı ORM ve migrasyon yönetimi.
- [Redis](https://redis.io/): Önbellekleme ve oturum/durum yönetimi.
- [Google Generative AI](https://ai.google.dev/): Gemini modelleri ile belge analizi ve veri çıkarımı.
- [Pydantic](https://docs.pydantic.dev/): Veri doğrulama ve ayar yönetimi.

**Frontend:**
- HTML5, CSS3, Vanilla JavaScript.

**Altyapı:**
- [Docker](https://www.docker.com/) & [Docker Compose](https://docs.docker.com/compose/): Konteynerizasyon ve kolay kurulum.

## 🏗️ Mimari ve İş Akışı

Projenin mimarisi ayrık bir Frontend ve Backend (Client-Server) yapısına dayanır.
- **Frontend (Kullanıcı Arayüzü):** Kullanıcı işlemlerinin, belge yükleme ekranlarının ve admin paneli fonksiyonlarının yürütüldüğü Vanilla JavaScript (HTML/CSS) tabanlı arayüzdür. REST API üzerinden backend ile asenkron iletişim kurar.
- **Backend (API ve İş Mantığı):** FastAPI üzerine kurulu olan backend, HTTP isteklerini karşılar, yetkilendirme (JWT) işlemlerini yapar ve veritabanı (PostgreSQL) işlemlerini SQLAlchemy ORM üzerinden gerçekleştirir.
- **AI/OCR Entegrasyonu:** Yüklenen finansal belgeler `AIService` modülü aracılığıyla doğrudan Gemini API'ye gönderilir. AI tarafından işlenip yapılandırılan veriler, ilişkisel veritabanında arşivlenir.
- **Cache ve State Yönetimi:** Redis kullanılarak önbellekleme ve ileride gerekebilecek asenkron görev kuyrukları için altyapı sağlanır.

## 🧠 AI Prompt Stratejisi

Proje içerisinde yapılandırılmamış finansal belgelerden veri çıkarımı ve ardından bu verilerin yorumlanması için **Google Gemini (2.5 Flash Lite)** modeli kullanılmaktadır. Süreç iki aşamalı, optimize edilmiş bir prompt stratejisi ile ilerler:

1. **Veri Çıkarımı (OCR / Extraction) Promptu**:
   - Sistem **"deneyimli bir finansal analiz uzmanı"** rolünü üstlenir.
   - Modele PDF, Excel veya Görsel verisi Base64 formatında multimodal olarak iletilir.
   - Prompt, modelin sadece net bir JSON şemasına (Bilanço, Gelir Tablosu, Nakit Akış Tablosu formatında) uymasını kesin bir dille emreder.
   - Sayıların tam veya ondalık (nokta ile) olması zorunlu tutulur ve halüsinasyonu (yanlış/sahte veri uydurmayı) engellemek adına belge üzerinde bulunamayan alanlar için kesinlikle `null` döndürmesi istenir.
   - **Generation Config:** Düşük yaratıcılık (`temperature=0.1`) kullanılarak kurumsal finansal veri çıkarımında yüksek tutarlılık (deterministik sonuçlar) elde edilir.

2. **Finansal Analiz ve Rasyo Hesaplama Promptu**:
   - Birinci adımdan elde edilen veya kullanıcının manuel sağladığı *yapılandırılmış JSON finansal verileri* string olarak modele beslenir.
   - Prompt, modele **"Likidite, Kaldıraç, Kârlılık, Etkinlik"** gibi alt başlıklarda rasyoları (örneğin: `current_ratio`, `debt_to_equity`, `roa` vb.) formülleriyle birlikte hesaplamasını söyler.
   - Aynı zamanda her kategori için bir metinsel değerlendirme (assessment), toplam sağlık skoru (1-100 arası), genel değerlendirme metni, şirketin güçlü yönleri (positive_indicators) ve risk faktörleri (risk_indicators) gibi özet bilgileri yine sistem entegrasyonu için tamamen JSON formatında döndürmeye zorlar.

## 📂 Proje Yapısı

```
financial_platform/
├── app/                  # Backend kaynak kodları (FastAPI)
│   ├── api/v1/           # API Endpoint'leri (auth, admin, financial vb.)
│   ├── models/           # Veritabanı modelleri (SQLAlchemy)
│   ├── schemas/          # Veri doğrulama şemaları (Pydantic)
│   ├── services/         # İş mantığı ve dış servis entegrasyonları (AI vb.)
│   ├── utils/            # Yardımcı fonksiyonlar (Logging, güvenlik vb.)
│   ├── config.py         # Proje ayarları
│   ├── database.py       # Veritabanı bağlantısı
│   └── main.py           # FastAPI uygulaması giriş noktası
├── frontend/             # Kullanıcı arayüzü dosyaları (HTML, JS, CSS)
├── migrations/           # Alembic veritabanı migrasyon dosyaları
├── scripts/              # Çeşitli yardımcı betikler
├── tests/                # Birim ve entegrasyon testleri
├── .env                  # Çevresel değişkenler
├── alembic.ini           # Alembic konfigürasyon dosyası
├── docker-compose.yml    # Docker servis tanımları
├── Dockerfile            # Backend uygulaması için Docker imajı
├── pytest.ini            # Test konfigürasyonu
└── requirements.txt      # Python bağımlılıkları
```

## 🔐 Ortam Değişkenleri (.env)

Projeyi başlatmadan önce kök dizinde bir `.env` dosyası oluşturmalı (veya var olanı düzenlemeli) ve aşağıdaki değişkenleri kendi sisteminize/ortamınıza göre yapılandırmalısınız:

```env
# Veritabanı Ayarları (Docker için aşağıdaki gibi, lokal için localhost olarak güncelleyin)
DATABASE_URL=postgresql://postgres:postgres@db:5432/financial_platform

# Güvenlik ve Kimlik Doğrulama
SECRET_KEY=rastgele_uretılmis_gizli_anahtar # Örn: openssl rand -hex 32
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
REFRESH_TOKEN_EXPIRE_DAYS=7

# Google Gemini API Anahtarı
GEMINI_API_KEY=AIzaSyB... # Kendi Google AI Studio anahtarınızı girin

# Şifreleme Anahtarı (Veritabanındaki hassas veriler için 32-byte Base64)
ENCRYPTION_KEY=O5De8Zoc...=

# Redis Konfigürasyonu
REDIS_URL=redis://redis:6379/0

# Uygulama Çalışma Ortamı
APP_ENV=development # development veya production
DEBUG=true

# CORS Ayarları (Virgülle ayrılmış liste veya JSON array formatında)
ALLOWED_ORIGINS=["http://localhost:3000","http://localhost:5173","http://127.0.0.1:5500","http://localhost:5500","null"]
```

## ⚙️ Kurulum ve Çalıştırma (Docker ile)

Projeyi en kolay şekilde Docker kullanarak ayağa kaldırabilirsiniz. Sisteminizde Docker ve Docker Compose kurulu olmalıdır.

1. **Projeyi Klonlayın veya Dizine Gidin:**
   ```bash
   cd financial_platform
   ```

2. **Çevresel Değişkenleri Ayarlayın:**
   Projeyi çalıştırmadan önce, `.env` dosyasını yapılandırdığınızdan emin olun. Özellikle `GEMINI_API_KEY` ve diğer gerekli anahtarların tanımlı olması gerekir.

3. **Docker Servislerini Başlatın:**
   ```bash
   docker-compose up --build
   ```
   *Not: Arka planda çalıştırmak için `-d` parametresini ekleyebilirsiniz.*

4. **Erişim:**
   - **Backend API Docs (Swagger UI):** [http://localhost:8000/docs](http://localhost:8000/docs) (Sadece DEBUG modunda aktifse)
   - **Frontend:** Frontend dosyalarını canlı bir sunucuda ya da VS Code Live Server gibi bir eklenti ile ayağa kaldırarak `app.js` üzerinden localhost:8000 (Backend API)'e istek atacak şekilde kullanabilirsiniz.

## 💻 Geliştirme Ortamı (Lokal Kurulum)

Eğer Docker kullanmadan direkt lokalinizde çalıştırmak isterseniz:

1. **Sanal Ortam Oluşturun:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # Windows için: venv\Scripts\activate
   ```

2. **Bağımlılıkları Yükleyin:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Veritabanını Başlatın (PostgreSQL ve Redis):**
   Lokalinizde çalışan bir PostgreSQL ve Redis olduğundan emin olun. `.env` dosyasındaki `DATABASE_URL` ve `REDIS_URL` değişkenlerini buna göre güncelleyin.

4. **Veritabanı Migrasyonlarını Uygulayın:**
   ```bash
   alembic upgrade head
   ```

5. **Uygulamayı Çalıştırın:**
   ```bash
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

## 🧪 Testler

Testleri çalıştırmak için `pytest` kullanabilirsiniz:

```bash
pytest tests/
```

## 📄 Lisans: kullanım ve ticaret hakları tarafıma aittir
