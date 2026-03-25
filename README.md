# 🤖 UtaiSOFT Case Study - Dynamic Tool Selection & Agent Architecture

Bu proje, **Hasan Kırtaş** tarafından UtaiSOFT AI Engineer vaka çalışması için geliştirilmiş; ölçeklenebilir ve dinamik tool seçimi yapan bir **Agentic AI** prototipidir.

## I. Overview & Problem Statement
Geleneksel ajan mimarilerinde tüm araç tanımlarının sistem prompt'una sığdırılması, sistem ölçeklendikçe yüksek token maliyeti ve modelin araçları birbirine karıştırması gibi sorunlara yol açar. Bu projede, ajanın araçları önceden bilmediği ve sadece ihtiyaç anında en doğru aracı keşfedip kullandığı bir yapı tasarladım.

## II. Architecture & Workflow
Sistemi, merkezi bir depo katmanından beslenen ve sadece ilgili yeteneği o anlık çağıran bir **Orkestratör** olarak kurguladım.

```mermaid
graph TD
    A[User Query] --> B{Intent Detection & <br/>Query Transformation}
    B -- Small Talk --> C[Straight Response]
    B -- Tool Required --> D[Capability Search & <br/>Vector Retrieval]
    D --> E[ChromaDB + BGE-Large]
    E --> F[Candidate Tools]
    F --> G[Cross-Encoder Reranking <br/>(False-Positive Protection)]
    G --> H{Final Tool Selection <br/>& Validation}
    H -- No Match --> I[Hallucination Guard / <br/>Graceful Rejection]
    H -- Selection --> J[Tool Execution]
    J --> K[Observation / <br/>Result Synthesis]
    K --> L[Final Humanized Answer]
```

## III. Agent Design

### Intelligence Layer (Model & API Choice)
*   **Model:** **DeepSeek-V3.2-fast** modelini güçlü reasoning yeteneği ve hızı nedeniyle seçtim. 
*   **API:** **Nebius (Token Factory)** altyapısını tercih ettim. Avrupa merkezli sunucuları sayesinde sunduğu low-latency başarısı ve maliyet avantajı, son projelerimde de sıklıkla tercih ettiğim optimize bir detaydır.

### Orchestration Logic (Prompt Chaining & CoT)
Süreci modüllere bölerek hata payını minimize ettiğim bir **Prompt Chaining** yapısı kurguladım. Bu yöntem, ajanın adım adım düşünmesini sağlayarak her aşamada doğrulanabilir çıktılar üretmesine olanak tanır.

## IV. Tool Selection Strategy
Sistemin en kritik bileşeni, alakasız araçların tetiklenmesini engelleyen ve yüksek isabet oranını önceliklendiren 3 aşamalı seçim hattıdır:

*   **Step 1: Semantic Retrieval** – Kullanıcı niyetine göre üretilen sorguyla, en yakın 5 aday araç vektör veritabanından hızla çekilir.
*   **Step 2: Reranking** – Sadece kelime benzerliğine güvenmek yerine, `BGE-Reranker` ile adayların dökümantasyonunu kullanıcı sorgusuyla mantıksal olarak kıyaslayıp tekrar sıraladım.
*   **Step 3: Validation** – Final aşamasında LLM, seçilen araçların gerçekten göreve uygun olup olmadığını dökümantasyon üzerinden son kez denetler. Bu adım, ajanın yanlış araç kullanmasını engelleyen bir güvenlik katmanıdır.

**Mühendislik Tercihi:** Bu yaklaşımda, hız yerine isabet oranını önceliklendirdim. Bir ajanın yanlış aracı kullanmasındansa, güvenli bir şekilde durması tasarımda benimsediğim temel prensiptir.

## V. Tool Discovery & Registry
Vektör veritabanı olarak, düşük seviyeli alternatiflerine kıyasla basitliği ve hızlı prototiplemeye uygunluğu nedeniyle **ChromaDB**'yi seçtim. Embedding tarafında, lokalde çalışan SOTA performanslı **BGE-Large** modelini tercih ettim.

## VI. Software Quality & Engineering Principles
Sistemi net modüler sınırlarla inşa ettim:
*   Araçlar, arşiv ve ajan mantığı sorumlulukların izole edilmesi için birbirinden ayrılmıştır.
*   `Pydantic` modelleri ile giriş doğrulaması yapılarak çalışma zamanı hataları önlenmiştir.
*   Yeni yetenekler, ana sistemde herhangi bir kod değişikliği yapmadan eklenebilir.

## VII. Automated Testing & Verification
Sistemin kararlılığını sağlamak için `pytest` tabanlı test süreçleri hazırladım:
- **Registry Tests:** Araç keşfi ve vektör arama başarısı.
- **Agent Tests:** Niyet tespiti ve doğru araç seçimi mantığı.
- **Örnek Senaryolar:** Hava durumu veya kod icrası gibi başarılı kullanım durumları ve imkansız taleplerin güvenli bir şekilde reddedilme süreçleri.

## VIII. Setup Guide
1. Bağımlılıkları yükleyin: `poetry install`
2. `.env` dosyasına `NEBIUS_API_KEY` ekleyin.
3. Uygulamayı çalıştırın: `poetry run streamlit run main.py`

---
*Developed by **Hasan Kırtaş** for UtaiSOFT AI Case Study.*
