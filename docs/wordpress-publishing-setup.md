# WordPress 發佈系統安裝與設定指南 (Pandoc & WP-CLI)

本文件旨在協助您安裝與設定發佈文章至 WordPress 所需的工具：Pandoc (Markdown 轉 HTML) 與 WP-CLI (WordPress 命令行介面)。

## 1. 安裝 Pandoc

Pandoc 是一個強大的文件格式轉換工具，用於將 Markdown 轉換為 HTML。

### Windows
*   請訪問 [Pandoc 官方網站](https://pandoc.org/installing.html)。
*   下載適用於 Windows 的安裝程式 (`.msi` 文件)，並按照提示完成安裝。

### macOS
*   若已安裝 Homebrew，請在終端機中執行：
    `brew install pandoc`
*   若未安裝 Homebrew，可從 [Pandoc 官方網站](https://pandoc.org/installing.html) 下載 macOS 安裝包。

### Linux (Debian/Ubuntu)
*   在終端機中執行：
    ```bash
    sudo apt update
    sudo apt install pandoc
    ```

### Linux (Fedora/CentOS)
*   在終端機中執行：
    ```bash
    sudo yum install pandoc
    ```

**驗證安裝**：
安裝完成後，請在終端機中執行 `pandoc --version` 來確認安裝成功。

---

## 2. 安裝 WP-CLI

WP-CLI 是 WordPress 的命令行介面，用於管理 WordPress 站點。

### Linux / macOS 通用步驟

1.  **下載 WP-CLI PHAR 文件**：
    ```bash
    curl -O https://raw.githubusercontent.com/wp-cli/builds/gh-pages/phar/wp-cli.phar
    ```
2.  **使其可執行**：
    ```bash
    chmod +x wp-cli.phar
    ```
3.  **移動到系統 PATH**：
    為了方便全局使用 `wp` 指令，將其移動到 PATH 中的目錄（例如 `/usr/local/bin`）。
    ```bash
    sudo mv wp-cli.phar /usr/local/bin/wp
    ```
    *(請根據您的系統配置調整路徑)*

### Windows

*   請參考 WP-CLI 官方網站的 Windows 安裝說明：[WP-CLI Installation on Windows](https://wp-cli.org/#installing)。通常涉及下載 PHAR 文件並將其路徑添加到系統的 PATH 環境變量中。

### 配置 WP-CLI 連接 WordPress 站點

WP-CLI 需要與您的 WordPress 站點進行通信。最常見的方法是：

1.  **在 WordPress 網站根目錄執行**：在包含 `wp-config.php` 文件的目錄下執行 `wp` 命令。
2.  **配置 `wp-cli.yml`**：您可以在 WordPress 根目錄或您的家目錄下創建 `wp-cli.yml` 文件，指定 `path` 和 `url`。

    **範例 `wp-cli.yml` 內容：**
    ```yaml
    path: /path/to/your/wordpress/installation # <-- 請替換為您的 WordPress 實際路徑
    url: https://your-wordpress-site.com     # <-- 請替換為您的 WordPress 實際 URL
    ```

**驗證安裝**：
在終端機中分別執行 `pandoc --version` 和 `wp --info` 來確認安裝成功。

---

完成這些步驟後，我們就可以繼續配置文章的 Frontmatter 和 Agent 的發佈邏輯了。
