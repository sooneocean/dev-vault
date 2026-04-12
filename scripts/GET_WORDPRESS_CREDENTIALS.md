# 🔐 獲取 WordPress.com 應用密碼（一次性設置）

為了自動部署，你需要生成一個 WordPress.com 應用密碼。

## 5 分鐘快速設置指南

### 步驟 1️⃣ : 進入安全設置

打開: https://wordpress.com/me/security

### 步驟 2️⃣ : 找到應用密碼部分

在頁面中找到 "**App Passwords**" 或 "**應用密碼**" 部分
（通常在頁面下方）

### 步驟 3️⃣ : 生成應用密碼

1. 在應用名稱輸入框輸入: `YOLO Deployer`
2. 點擊 "生成應用密碼" 或 "Generate App Password"
3. 複製生成的密碼（會有一串 16 個字符的密碼）

### 步驟 4️⃣ : 設置環境變數

打開終端/命令行，運行以下命令：

**Windows (PowerShell)：**
```powershell
$env:WP_USERNAME="你的WordPress.com用戶名"
$env:WP_APP_PASSWORD="複製的應用密碼"
```

**macOS/Linux (Bash)：**
```bash
export WP_USERNAME="你的WordPress.com用戶名"
export WP_APP_PASSWORD="複製的應用密碼"
```

**Windows (Command Prompt)：**
```cmd
set WP_USERNAME=你的WordPress.com用戶名
set WP_APP_PASSWORD=複製的應用密碼
```

### 步驟 5️⃣ : 運行自動部署

```bash
cd "C:/DEX_data/Claude Code DEV"
node scripts/auto-deploy-complete.js
```

---

## 獲取你的 WordPress.com 用戶名

你的 WordPress.com 用戶名是你登入時使用的用戶名或郵箱地址。

如果不確定，可以：
1. 進入 https://wordpress.com/me/account
2. 看頁面頂部顯示的用戶名

---

## 常見問題

**Q: 應用密碼在哪裡生成？**
A: https://wordpress.com/me/security → 向下捲動找到 "App Passwords"

**Q: 應用密碼是什麼？**
A: 它是一個特殊的 16 字符密碼，用於讓應用（如我們的部署腳本）存取你的 WordPress.com 帳戶，但無法更改帳戶設置或密碼。

**Q: 這個應用密碼安全嗎？**
A: 是的！應用密碼只能用於特定目的，而且你隨時可以在安全設置中刪除它。

**Q: 設置後就不需要再設置了嗎？**
A: 正確！設置一次環境變數後，你可以無限次運行自動部署腳本。

---

## 完成後

設置好環境變數後，運行：

```bash
node scripts/auto-deploy-complete.js
```

腳本將：
1. ✓ 連接到你的 WordPress.com 站點
2. ✓ 查詢首頁信息
3. ✓ 自動上傳新首頁內容
4. ✓ 顯示完成狀態和驗證步驟

---

## 安全說明

- 應用密碼只用於存取 WordPress.com API
- 不會儲存到任何地方（環境變數在會話結束後過期）
- 你可以隨時在 WordPress.com 安全設置中刪除應用密碼
- 這不是你的主 WordPress.com 密碼

---

**準備好了？**

1. 進入 https://wordpress.com/me/security
2. 生成應用密碼
3. 設置環境變數
4. 運行 `node scripts/auto-deploy-complete.js`

祝你部署順利！🚀
