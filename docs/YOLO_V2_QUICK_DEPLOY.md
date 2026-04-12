# ⚡ YOLO LAB v2 快速部署指南（5 分鐘）

**站點:** yololab.net
**Site ID:** 133512998
**發布日期:** 2026-04-08

---

## 🚀 3 個步驟快速部署

### ✅ 步驟 1：取得 HTML 代碼

**文件:** `seo-optimization-output/homepage-v2-ultramodern.html`

**代碼位置：** C:\DEX_data\Claude Code DEV\seo-optimization-output\homepage-v2-ultramodern.html

---

### ✅ 步驟 2：進入 WordPress 後台

```
1️⃣ 打開瀏覽器，進入：
   https://yololab.net/wp-admin

2️⃣ 登入你的 WordPress 帳號

3️⃣ 左側菜單 → Pages（頁面）

4️⃣ 找到首頁（Homepage 或 首頁 - 通常是第一個）

5️⃣ 點擊編輯
```

---

### ✅ 步驟 3：貼入新首頁代碼

```
1️⃣ 在頁面編輯器中，看到兩個模式：
   • Visual Editor（視覺編輯）
   • Code Editor（代碼編輯）

2️⃣ 點擊右上角的三個點（⋯）→ 選擇 Code Editor
   或直接點擊 Code Editor 標籤

3️⃣ 看到代碼編輯框後：
   • 全選所有代碼（Ctrl+A 或 Cmd+A）
   • 刪除（Delete）

4️⃣ 複製以下 ENTIRE HTML：
```

---

## 📋 完整 HTML 代碼（複製全部）

```html
<!-- YOLO LAB 首頁 v2（超現代化）- FSE Blocks HTML -->

<!-- 自訂 CSS 注入（內頁） -->
<!-- wp:html -->
<style>
:root {
  --color-primary: #418a2c;
  --color-secondary: #7a7a7a;
  --color-accent-2: #6a6ab1;
  --color-accent-3: #ffffa0;
  --color-hero-bg: #050811;
  --color-card-dark: rgba(255,255,255,0.08);
  --color-film: #e74c3c;
  --color-music: #6a6ab1;
  --color-tech: #3498db;
  --color-sports: #418a2c;
  --spacing-sm: 8px;
  --spacing-md: 16px;
  --spacing-lg: 24px;
  --spacing-xl: 32px;
  --radius-sm: 8px;
  --radius-md: 12px;
  --transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

/* ===== HERO SECTION ===== */
.yolo-hero {
  position: relative;
  min-height: 600px;
  background: linear-gradient(135deg, #050811 0%, #1a0f2e 50%, #0f1419 100%);
  overflow: hidden;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 60px 20px;
  animation: gradientShift 8s ease infinite;
  background-size: 200% 200%;
}

@keyframes gradientShift {
  0% { background-position: 0% 50%; }
  50% { background-position: 100% 50%; }
  100% { background-position: 0% 50%; }
}

@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(30px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.yolo-hero::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background:
    radial-gradient(circle at 20% 50%, rgba(65,138,44,0.1) 0%, transparent 50%),
    radial-gradient(circle at 80% 80%, rgba(106,106,177,0.1) 0%, transparent 50%);
  pointer-events: none;
}

.yolo-hero-content {
  position: relative;
  z-index: 1;
  text-align: center;
  max-width: 900px;
  animation: fadeInUp 0.8s ease;
}

.yolo-hero h1 {
  font-size: 56px;
  font-weight: 900;
  color: #ffffff;
  margin: 0 0 20px 0;
  line-height: 1.2;
  text-shadow: 0 0 30px rgba(65,138,44,0.6),
               0 0 60px rgba(65,138,44,0.3);
  letter-spacing: -1px;
}

.yolo-hero-tags {
  display: flex;
  gap: 8px;
  justify-content: center;
  margin-bottom: 24px;
  flex-wrap: wrap;
}

.yolo-tag {
  background: rgba(255,255,160,0.15);
  border: 1px solid rgba(255,255,160,0.4);
  color: #ffffa0;
  padding: 6px 16px;
  border-radius: 20px;
  font-size: 12px;
  font-weight: 600;
  backdrop-filter: blur(8px);
  -webkit-backdrop-filter: blur(8px);
  animation: fadeInUp 0.8s ease 0.1s backwards;
}

.yolo-hero p {
  color: rgba(255,255,255,0.8);
  font-size: 18px;
  line-height: 1.6;
  margin: 0 0 32px 0;
  animation: fadeInUp 0.8s ease 0.2s backwards;
}

.yolo-hero-buttons {
  display: flex;
  gap: 16px;
  justify-content: center;
  flex-wrap: wrap;
  animation: fadeInUp 0.8s ease 0.3s backwards;
}

.yolo-btn {
  padding: 12px 32px;
  border: none;
  border-radius: 6px;
  font-weight: 600;
  font-size: 16px;
  cursor: pointer;
  transition: var(--transition);
  text-decoration: none;
  display: inline-block;
  font-family: inherit;
}

.yolo-btn-primary {
  background: linear-gradient(135deg, #418a2c 0%, #2d5f1f 100%);
  color: white;
  box-shadow: 0 8px 24px rgba(65,138,44,0.3);
}

.yolo-btn-primary:hover {
  transform: translateY(-2px);
  box-shadow: 0 16px 40px rgba(65,138,44,0.5);
}

.yolo-btn-secondary {
  background: rgba(255,255,255,0.1);
  border: 2px solid rgba(255,255,255,0.3);
  color: white;
  backdrop-filter: blur(8px);
  -webkit-backdrop-filter: blur(8px);
}

.yolo-btn-secondary:hover {
  background: rgba(255,255,255,0.2);
  border-color: rgba(255,255,255,0.6);
  transform: translateY(-2px);
}

/* ===== STATS BAR ===== */
.yolo-stats {
  background: linear-gradient(90deg, #1a1a1a 0%, #2a2a2a 100%);
  padding: 32px 20px;
  border-top: 1px solid rgba(255,255,255,0.1);
  border-bottom: 1px solid rgba(255,255,255,0.1);
}

.yolo-stats-container {
  display: flex;
  justify-content: center;
  gap: 48px;
  flex-wrap: wrap;
  max-width: 1200px;
  margin: 0 auto;
}

.yolo-stat-item {
  text-align: center;
  animation: fadeInUp 0.8s ease;
}

.yolo-stat-number {
  font-size: 32px;
  font-weight: 900;
  color: var(--color-primary);
  margin: 0;
  letter-spacing: -1px;
}

.yolo-stat-label {
  font-size: 13px;
  color: rgba(255,255,255,0.6);
  margin-top: 4px;
  text-transform: uppercase;
  letter-spacing: 1px;
}

/* ===== GLASSMORPHISM CARDS ===== */
.yolo-glass-card {
  background: rgba(255,255,255,0.08);
  border: 1px solid rgba(255,255,255,0.15);
  border-radius: var(--radius-md);
  backdrop-filter: blur(16px);
  -webkit-backdrop-filter: blur(16px);
  overflow: hidden;
  transition: var(--transition);
}

.yolo-glass-card:hover {
  transform: translateY(-8px);
  border-color: rgba(65,138,44,0.3);
  box-shadow: 0 20px 40px rgba(65,138,44,0.3);
  background: rgba(255,255,255,0.12);
}

.yolo-glass-card img {
  width: 100%;
  height: 250px;
  object-fit: cover;
  display: block;
  transition: var(--transition);
}

.yolo-glass-card:hover img {
  transform: scale(1.05);
}

.yolo-glass-card-content {
  padding: 20px;
  color: rgba(255,255,255,0.9);
}

.yolo-glass-card-title {
  font-size: 18px;
  font-weight: 700;
  margin: 0 0 8px 0;
  color: white;
  line-height: 1.3;
}

.yolo-glass-card-meta {
  font-size: 12px;
  color: rgba(255,255,255,0.5);
  display: flex;
  gap: 8px;
}

/* ===== FEATURED GRID ===== */
.yolo-featured-grid {
  display: grid;
  grid-template-columns: 1.5fr 1fr 1fr;
  grid-template-rows: auto auto;
  gap: 16px;
  background: linear-gradient(180deg, #0a0a0a 0%, #1a1a1a 100%);
  padding: 40px 20px;
  max-width: 1400px;
  margin: 0 auto;
}

.yolo-featured-main {
  grid-row: 1 / 3;
  grid-column: 1;
}

.yolo-featured-main .yolo-glass-card img {
  height: 400px;
}

@media (max-width: 1024px) {
  .yolo-featured-grid {
    grid-template-columns: 1fr 1fr;
    padding: 30px 20px;
  }

  .yolo-featured-main {
    grid-row: 1;
    grid-column: 1 / 3;
  }
}

@media (max-width: 768px) {
  .yolo-featured-grid {
    grid-template-columns: 1fr;
    gap: 12px;
    padding: 20px 15px;
  }

  .yolo-featured-main {
    grid-column: 1;
  }

  .yolo-featured-main .yolo-glass-card img {
    height: 300px;
  }
}

/* ===== CATEGORY GRID ===== */
.yolo-categories {
  padding: 40px 20px;
  background: #ffffff;
}

.yolo-cat-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 20px;
  max-width: 1200px;
  margin: 0 auto;
}

.yolo-cat-card {
  background: white;
  border: 2px solid;
  border-radius: var(--radius-md);
  padding: 24px;
  transition: var(--transition);
  cursor: pointer;
  position: relative;
  overflow: hidden;
  box-shadow: 0 2px 8px rgba(0,0,0,0.05);
}

.yolo-cat-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 4px;
  transition: var(--transition);
}

.yolo-cat-card.film {
  border-color: var(--color-film);
}
.yolo-cat-card.film::before {
  background: var(--color-film);
}

.yolo-cat-card.music {
  border-color: var(--color-music);
}
.yolo-cat-card.music::before {
  background: var(--color-music);
}

.yolo-cat-card.tech {
  border-color: var(--color-tech);
}
.yolo-cat-card.tech::before {
  background: var(--color-tech);
}

.yolo-cat-card.sports {
  border-color: var(--color-sports);
}
.yolo-cat-card.sports::before {
  background: var(--color-sports);
}

.yolo-cat-card:hover {
  transform: translateY(-6px);
  box-shadow: 0 12px 24px rgba(0,0,0,0.15);
}

.yolo-cat-card:hover::before {
  height: 6px;
}

.yolo-cat-card h3 {
  margin: 0 0 16px 0;
  font-size: 24px;
  font-weight: 700;
  color: #2a2a2a;
}

.yolo-cat-card p {
  margin: 0 0 20px 0;
  font-size: 13px;
  color: var(--color-secondary);
  line-height: 1.6;
}

.yolo-cat-card a {
  font-size: 14px;
  font-weight: 600;
  transition: var(--transition);
}

.yolo-cat-card a:hover {
  text-decoration: none;
  margin-left: 4px;
}

@media (max-width: 1024px) {
  .yolo-cat-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 640px) {
  .yolo-cat-grid {
    grid-template-columns: 1fr;
  }

  .yolo-categories {
    padding: 30px 15px;
  }
}

/* ===== MAGAZINE LAYOUT ===== */
.yolo-magazine {
  padding: 40px 20px;
  background: white;
  max-width: 1200px;
  margin: 0 auto;
}

.yolo-mag-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 32px;
}

.yolo-mag-hero img {
  width: 100%;
  height: 400px;
  object-fit: cover;
  border-radius: var(--radius-md);
  margin-bottom: 16px;
  transition: var(--transition);
}

.yolo-mag-hero img:hover {
  transform: scale(1.02);
}

.yolo-mag-hero h3 {
  font-size: 28px;
  margin: 0 0 12px 0;
  color: #2a2a2a;
  line-height: 1.3;
}

.yolo-mag-hero a {
  margin-top: 12px;
  display: inline-block;
  font-weight: 600;
  transition: var(--transition);
}

.yolo-mag-hero a:hover {
  text-decoration: none;
  margin-left: 4px;
}

.yolo-mag-sidebar {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.yolo-mag-item {
  padding: 16px 0;
  border-bottom: 1px solid #e0e0e0;
  transition: var(--transition);
}

.yolo-mag-item:last-child {
  border-bottom: none;
}

.yolo-mag-item:hover {
  padding-left: 8px;
}

.yolo-mag-item-meta {
  font-size: 12px;
  color: #7a7a7a;
  margin-bottom: 6px;
}

.yolo-mag-item h4 {
  font-size: 16px;
  margin: 0;
  color: #2a2a2a;
  line-height: 1.4;
  transition: var(--transition);
}

.yolo-mag-item:hover h4 {
  color: var(--color-primary);
}

@media (max-width: 768px) {
  .yolo-mag-grid {
    grid-template-columns: 1fr;
    gap: 20px;
  }

  .yolo-mag-hero img {
    height: 300px;
  }

  .yolo-magazine {
    padding: 30px 15px;
  }
}

/* ===== DARK MODE ===== */
@media (prefers-color-scheme: dark) {
  .yolo-categories,
  .yolo-magazine {
    background: #1a1a1a;
  }

  .yolo-cat-card {
    background: #2a2a2a;
    box-shadow: 0 2px 8px rgba(255,255,255,0.1);
  }

  .yolo-cat-card h3 {
    color: #ffffff;
  }

  .yolo-cat-card p {
    color: rgba(255,255,255,0.6);
  }

  .yolo-mag-hero h3 {
    color: #ffffff;
  }

  .yolo-mag-item h4 {
    color: #ffffff;
  }

  .yolo-mag-item {
    border-bottom-color: rgba(255,255,255,0.1);
  }

  .yolo-mag-item-meta {
    color: rgba(255,255,255,0.5);
  }

  .yolo-cat-card:hover {
    box-shadow: 0 12px 24px rgba(65,138,44,0.2);
  }
}

/* ===== RESPONSIVE ===== */
@media (max-width: 768px) {
  .yolo-hero {
    min-height: 400px;
    padding: 40px 20px;
  }

  .yolo-hero h1 {
    font-size: 36px;
  }

  .yolo-hero p {
    font-size: 16px;
  }

  .yolo-stats-container {
    gap: 24px;
  }

  .yolo-stat-number {
    font-size: 24px;
  }

  .yolo-btn {
    padding: 10px 24px;
    font-size: 14px;
  }
}

@media (max-width: 480px) {
  .yolo-hero {
    min-height: 350px;
    padding: 30px 15px;
  }

  .yolo-hero h1 {
    font-size: 28px;
  }

  .yolo-hero-tags {
    gap: 6px;
  }

  .yolo-tag {
    padding: 4px 12px;
    font-size: 11px;
  }

  .yolo-hero-buttons {
    gap: 8px;
  }

  .yolo-btn {
    padding: 8px 16px;
    font-size: 13px;
  }

  .yolo-stats {
    padding: 24px 15px;
  }

  .yolo-stats-container {
    gap: 16px;
  }

  .yolo-stat-number {
    font-size: 20px;
  }
}

@media (prefers-reduced-motion: reduce) {
  * {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
  }
}

@media print {
  .yolo-hero-buttons,
  .yolo-stats,
  .yolo-mag-sidebar {
    display: none;
  }
}
</style>
<!-- /wp:html -->

<!-- Header Template Part -->
<!-- wp:template-part {"slug":"header","theme":"yolo-lab"} /-->

<!-- Hero Section -->
<!-- wp:html -->
<div class="yolo-hero">
  <div class="yolo-hero-content">
    <h1 class="yolo-hero-h1">YOLO LAB<br/>解構科技邊際<br/>與媒體娛樂</h1>
    <div class="yolo-hero-tags">
      <span class="yolo-tag">📊 數據驅動</span>
      <span class="yolo-tag">🚀 前衛觀點</span>
      <span class="yolo-tag">⚡ 實驗精神</span>
    </div>
    <p>科技疆界與娛樂底層邏輯的深度分析 | 電影 · 音樂 · 科技 · 運動 · 文化</p>
    <div class="yolo-hero-buttons">
      <a href="/category/film/" class="yolo-btn yolo-btn-primary">瀏覽分類</a>
      <a href="/search/" class="yolo-btn yolo-btn-secondary">搜尋文章</a>
    </div>
  </div>
</div>
<!-- /wp:html -->

<!-- Stats Bar -->
<!-- wp:html -->
<div class="yolo-stats">
  <div class="yolo-stats-container">
    <div class="yolo-stat-item">
      <p class="yolo-stat-number">898+</p>
      <p class="yolo-stat-label">精選文章</p>
    </div>
    <div class="yolo-stat-item">
      <p class="yolo-stat-number">4</p>
      <p class="yolo-stat-label">主要分類</p>
    </div>
    <div class="yolo-stat-item">
      <p class="yolo-stat-number">2025</p>
      <p class="yolo-stat-label">內容資料庫</p>
    </div>
  </div>
</div>
<!-- /wp:html -->

<!-- Featured Posts Section -->
<!-- wp:group {"tagName":"section","align":"full"} -->
<section class="wp-block-group alignfull" style="padding: 0;">
<!-- wp:html -->
<div class="yolo-featured-grid">
  <!-- Main Featured Post (Left) -->
  <div class="yolo-glass-card yolo-featured-main">
    <img src="https://yololab.net/wp-content/uploads/featured-hero.jpg" alt="Featured Article" />
    <div class="yolo-glass-card-content">
      <div class="yolo-glass-card-meta">
        <span>熱門精選</span>
        <span>3 天前</span>
      </div>
      <p class="yolo-glass-card-title">AI 浪潮下的媒體未來：數據如何重塑內容產業</p>
    </div>
  </div>

  <!-- Secondary Cards (Right Top) -->
  <div class="yolo-glass-card">
    <img src="https://yololab.net/wp-content/uploads/post-2.jpg" alt="Post 2" />
    <div class="yolo-glass-card-content">
      <div class="yolo-glass-card-meta">
        <span>科技</span>
      </div>
      <p class="yolo-glass-card-title">ChatGPT 一週年反思</p>
    </div>
  </div>

  <!-- Secondary Card (Right Middle) -->
  <div class="yolo-glass-card">
    <img src="https://yololab.net/wp-content/uploads/post-3.jpg" alt="Post 3" />
    <div class="yolo-glass-card-content">
      <div class="yolo-glass-card-meta">
        <span>音樂</span>
      </div>
      <p class="yolo-glass-card-title">2026 音樂市場預測</p>
    </div>
  </div>

  <!-- Secondary Card (Right Bottom) -->
  <div class="yolo-glass-card">
    <img src="https://yololab.net/wp-content/uploads/post-4.jpg" alt="Post 4" />
    <div class="yolo-glass-card-content">
      <div class="yolo-glass-card-meta">
        <span>電影</span>
      </div>
      <p class="yolo-glass-card-title">奧斯卡 2026 劇透分析</p>
    </div>
  </div>
</div>
<!-- /wp:html -->
</section>
<!-- /wp:group -->

<!-- Category Section -->
<!-- wp:group {"tagName":"section","align":"full","style":{"spacing":{"padding":{"top":"40px","bottom":"40px"}}}} -->
<section class="wp-block-group alignfull">
<!-- wp:html -->
<h2 style="text-align: center; margin-bottom: 40px; font-size: 32px; font-weight: 700; color: #2a2a2a;">分類專欄</h2>
<div class="yolo-cat-grid">
  <!-- Film -->
  <div class="yolo-cat-card film">
    <h3>🎬 電影</h3>
    <p>導演視野、敘事結構、視覺美學。院線大製作、獨立製片、國際電影節、串流原創 — 深入理解電影如何塑造世界認知。</p>
    <a href="/category/film/" style="color: var(--color-film); text-decoration: none; font-weight: 600;">探索電影 →</a>
  </div>

  <!-- Music -->
  <div class="yolo-cat-card music">
    <h3>🎵 音樂</h3>
    <p>製作理念、藝人品牌、粉絲經濟。華語創新、韓樂全球、歐美輸出、獨立精神 — 發掘每一首歌背後的故事。</p>
    <a href="/category/music/" style="color: var(--color-music); text-decoration: none; font-weight: 600;">探索音樂 →</a>
  </div>

  <!-- Tech -->
  <div class="yolo-cat-card tech">
    <h3>⚡ 科技</h3>
    <p>AI、晶片、雲端革命。前沿動態、產品評測、數位政策、倫理困境 — 透視科技如何塑造未來世界。</p>
    <a href="/category/tech/" style="color: var(--color-tech); text-decoration: none; font-weight: 600;">探索科技 →</a>
  </div>

  <!-- Sports -->
  <div class="yolo-cat-card sports">
    <h3>🏆 運動</h3>
    <p>競技數據、運動員心理、體育產業。足籃排主流、電競極限新興 — 融合統計與敘事，呈現體育完整面貌。</p>
    <a href="/category/sports/" style="color: var(--color-sports); text-decoration: none; font-weight: 600;">探索運動 →</a>
  </div>
</div>
<!-- /wp:html -->
</section>
<!-- /wp:group -->

<!-- Latest Posts Magazine Layout -->
<!-- wp:group {"tagName":"section","align":"full","style":{"spacing":{"padding":{"top":"40px","bottom":"40px"}}}} -->
<section class="wp-block-group alignfull">
<!-- wp:html -->
<h2 style="text-align: center; margin-bottom: 40px; font-size: 32px; font-weight: 700; color: #2a2a2a;">最新發布</h2>
<div class="yolo-magazine">
  <div class="yolo-mag-grid">
    <!-- Hero Post (Left) -->
    <div>
      <div class="yolo-mag-hero">
        <img src="https://yololab.net/wp-content/uploads/latest-hero.jpg" alt="Latest Article" />
        <div class="yolo-mag-item-meta">3 小時前 | 科技</div>
        <h3>最新發布的深度分析文章</h3>
        <p style="margin-top: 12px; color: #7a7a7a; line-height: 1.6;">這是最新發布的文章摘要。點擊進去閱讀完整分析。</p>
        <a href="#" style="color: var(--color-primary); text-decoration: none; font-weight: 600; margin-top: 12px; display: inline-block;">閱讀全文 →</a>
      </div>
    </div>

    <!-- Sidebar (Right) -->
    <div class="yolo-mag-sidebar">
      <div class="yolo-mag-item">
        <div class="yolo-mag-item-meta">昨天 | 電影</div>
        <h4>文章標題 1</h4>
      </div>
      <div class="yolo-mag-item">
        <div class="yolo-mag-item-meta">2 天前 | 音樂</div>
        <h4>文章標題 2</h4>
      </div>
      <div class="yolo-mag-item">
        <div class="yolo-mag-item-meta">3 天前 | 運動</div>
        <h4>文章標題 3</h4>
      </div>
      <div class="yolo-mag-item">
        <div class="yolo-mag-item-meta">4 天前 | 科技</div>
        <h4>文章標題 4</h4>
      </div>
      <div class="yolo-mag-item">
        <div class="yolo-mag-item-meta">5 天前 | 電影</div>
        <h4>文章標題 5</h4>
      </div>
    </div>
  </div>
</div>
<!-- /wp:html -->
</section>
<!-- /wp:group -->

<!-- Footer Template Part -->
<!-- wp:template-part {"slug":"footer","theme":"yolo-lab"} /-->
```

---

### ✅ 步驟 4：發布

```
1️⃣ 在代碼編輯框底部，點擊：
   • Update（更新）或 Publish（發布）

2️⃣ 等待發布完成（通常 2-5 秒）

3️⃣ 看到 "Page published" 或 "Page updated" 確認消息
```

---

## 🎨 驗證清單

部署後，訪問 **https://yololab.net** 檢查：

- [ ] **Hero 區域** — 深黑背景 + 綠色霓虹光暈 H1
- [ ] **Tag Pills** — 黃色半透明標籤（數據驅動、前衛、實驗）
- [ ] **2 個按鈕** — 綠色 + 玻璃風格
- [ ] **Stats Bar** — 898+、4、2025 三個數據
- [ ] **Glassmorphism 卡片** — 毛玻璃效果 + Hover 浮動
- [ ] **4 個分類卡片** — 紅(電影)、紫(音樂)、藍(科技)、綠(運動)
- [ ] **最新文章區** — 左大右小雜誌版
- [ ] **響應式**
  - 桌面 (1200px+) ✅
  - 平板 (768px) ✅ (2 欄)
  - 手機 (320px) ✅ (1 欄)

---

## 📱 測試響應式

```
1️⃣ 打開首頁
2️⃣ 按 F12（Chrome DevTools）
3️⃣ 點擊 Device Toolbar（手機圖標）
4️⃣ 選擇：
   • iPhone 12 (390px)
   • iPad (820px)
   • Desktop (1200px)
5️⃣ 確認布局正確轉換
```

---

## 🌙 測試 Dark Mode

```
1️⃣ F12 打開開發者工具
2️⃣ Ctrl+Shift+P (Windows) 或 Cmd+Shift+P (Mac)
3️⃣ 輸入：Dark mode
4️⃣ 選擇：Emulate CSS media feature prefers-color-scheme
5️⃣ 選擇：dark
6️⃣ 網站自動切換深色配色 ✅
```

---

## ⚠️ 故障排除

| 問題 | 解決方案 |
|------|--------|
| 代碼編輯器顯示錯誤 | 檢查 HTML 有無遺漏標籤 — 複製時確保完整 |
| 光暈不明顯 | 檢查瀏覽器支持 `text-shadow` — 用 Chrome 測試 |
| 卡片沒毛玻璃效果 | 需要 Chrome 76+ / Safari 9+ — 用 `backdrop-filter` |
| 圖片顯示不了 | 圖片 URL 尚未設置 — 替換為你的媒體庫 URL |
| 小屏幕顯示錯亂 | 清除緩存：Ctrl+Shift+Del → 全部清除 → Ctrl+F5 |

---

## 📸 預期效果

```
🌙 深黑 Hero + 綠色光暈
📊 Stats Bar (三個數據)
🔮 Glassmorphism 卡片 (毛玻璃 + Hover)
🎨 4 色分類 (紅紫藍綠)
📰 Magazine 雜誌版 (左大右小)
✨ 所有動畫 + Dark Mode
```

---

## 🎯 下一步

完成部署後，你可以：

1. **替換圖片** — 上傳真實內容圖片
2. **調整文案** — 編輯標題、描述文字
3. **優化 SEO** — 添加 Meta 標籤
4. **追蹤分析** — 用 Google Analytics 監控效果

---

**需要幫助？**
✉️ 在 WordPress 後台有問題？ → 查看 https://wordpress.com/support/
📁 文件位置：`seo-optimization-output/homepage-v2-ultramodern.html`
📋 完整指南：`docs/YOLO_HOMEPAGE_V2_DEPLOYMENT.md`
