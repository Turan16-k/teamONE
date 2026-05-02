# Financial Analysis Platform - BSMT Hackathon Submission

Bu proje, **Pro Sicht** iş birliği ile düzenlenen BSMT Hackathon kapsamında geliştirilen; finansal danışmanlık süreçlerini AI ve OCR teknolojileri ile modernize eden çok katmanlı bir platformdur.

---

## 🚀 Proje Özeti
Platform, karmaşık finansal belgeleri (Bilanço, Gelir Tablosu vb.) **Gemini 1.5 Pro** multimodal AI kullanarak dijitalleştirir, analiz eder ve jüri/müşteri sunumuna hazır **.pptx** formatında raporlar üretir.

### 🎯 Yönetici Özeti (Executive Summary)
1. **Temel Mimari ve Erişim Kontrolü:** Rol Bazlı Erişim Kontrolü (RBAC) ile yönetilen iki farklı arayüzden oluşur. Admin Paneli tüm verilere ve AI analizlerine tam erişim sağlarken, Kullanıcı Paneli sadece ilgili firmanın verilerine kısıtlı erişim sunar.
2. **Yapay Zeka ve Veri İşleme (Projenin Kalbi):** Yüklenen belgeler (PDF/Görsel) OCR + LLM ile ayrıştırılır. Ardından finansal tablolara bakarak yorumlu, yazılı finansal analiz raporları ve uzman görüşleri oluşturulur ve otomatik .pptx dosyası hazırlanır.
3. **Fonksiyonel Gereksinimler:** Tam teşekküllü CRUD operasyonları ile firma yönetimi sağlanırken, Premium Akış (Monetizasyon) sayesinde "Uzman Görüşü" ve "AI Analiz" özelliklerine admin onaylı bir talep/satın alma sistemi kurulmuştur.
4. **Sistem Kalitesi ve Optimizasyon:** Kullanıcı işlemleri, CRUD operasyonları, AI/LLM çağrıları detaylıca loglanır. PostgreSQL üzerinde indeksleme, N+1 sorgu optimizasyonu ve hassas veriler için at-rest encryption mevcuttur.
5. **Kullanıcı Deneyimi (UX):** Koyu mod, cam efekti (glassmorphism), chart tabanlı veri görselleştirme, yükleme anlarında skeleton yapıları ve anlaşılır hata mesajları (Clean Messages) ile premium bir Fintech hissi yaratılmıştır.

## 🛠️ Kurulum ve Çalıştırma

### Gereksinimler
- Python 3.10+
- PostgreSQL
- Redis
- Google Gemini API Key

### Kurulum Adımları
1.  **Bağımlılıkları Yükleyin**:
    ```bash
    pip install -r requirements.txt
    ```
2.  **Veritabanı ve Ortam Değişkenleri**:
    `.env` dosyasını `.env.example` üzerinden oluşturun ve API anahtarlarınızı girin.
3.  **Migration ve Seed Verilerini Yükleyin (T10)**:
    ```bash
    python -m scripts.seed
    ```
4.  **Sunucuyu Başlatın**:
    ```bash
    uvicorn app.main:app --reload
    ```

## 🏗️ Teknik Mimari
- **Backend**: FastAPI (Asenkron yapı, yüksek performans).
- **Veritabanı**: PostgreSQL (Kalıcılık katmanı) + SQLAlchemy 2.0 ORM.
- **AI/OCR**: Google Gemini 1.5 Pro (Multimodal belge işleme).
- **Raporlama**: Python-pptx (Dinamik sunum üretimi).
- **Güvenlik**: JWT tabanlı RBAC (Admin/Kullanıcı ayrımı).
- **Loglama**: Structlog ile teknik ve kullanıcı dostu ikili hata yönetimi.

## 🧠 AI Prompt Stratejisi (Jüri Özel Bölümü)
Projemizde kullanılan prompt stratejisi, **Multimodal Chain-of-Thought** ve **Structured Output** tekniklerine dayanmaktadır:

1.  **Extraction (Veri Çıkarma)**: Doküman doğrudan Gemini'ye gönderilir. Prompt içerisinde dokümanın finansal yapısı (Bilanço/Gelir Tablosu) tarif edilir ve **kesin JSON formatı** zorunlu kılınır.
2.  **Analysis (Analitik)**: Çıkarılan yapılandırılmış veri üzerinden likidite, borçluluk ve kârlılık rasyoları için finansal uzman rolü tanımlanmış ikincil bir prompt kullanılır.
3.  **Güven Skoru (O4)**: AI'dan her işlem için bir `financial_score` (1-100 arası sağlık skoru) üretmesi istenir, böylece firmaların durumu tek bir metrikle değerlendirilebilir.

## 📊 Önemli Özellikler (T Serisi)
*   **T1 & T2**: Tam kapsamlı Admin ve Kullanıcı paneli ayrımı ve CRUD işlemleri.
*   **T3 & T4**: Belgeden otomatik veri çıkarma ve kapsamlı finansal analiz raporu.
*   **T5**: İndirilebilir .pptx sunum çıktısı.
*   **T9 & T10**: Detaylı loglama (hata/işlem) ve veritabanı optimizasyonu (İndeksleme, N+1 önleme).

## ⚠️ Demo Veri Bildirimi
Sistemde kullanılan tüm firma profilleri ve finansal tablolar **sahte/demo veridir**. AI araçları ile test amaçlı oluşturulmuştur ve gerçek mali verileri yansıtmamaktadır.

---
**Geliştiren**: Smart Inspection AI Ekibi
**Versiyon**: 1.0.0 (Hackathon Edition)
