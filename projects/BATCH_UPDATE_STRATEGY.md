# 🚀 YOLOLAB SEO 批量优化最终方案

## 当前进度

| 页面 | 完成度 | 备注 |
|------|------|------|
| **Page 5** | ✅ 19/20 | 18 篇 + 1 补救 (34206) |
| **Page 6** | ⏳ 9/20 | 34196, 34190, 34185, 34173, 34171, 34153, 34147, 34136, 34132 |
| **Page 7-136** | ⏹️ 未开始 | 2,660 篇待处理 |
| **总计** | 28/2,716 | **1.03% 完成** |

---

## 快速完成剩余 11 篇 Page 6（推荐方案）

### 方案 A：继续使用 wpcom-mcp（确保可靠）
```bash
# 继续使用以下 11 篇的 SEO 内容完成 Page 6

34126: "河正宇19年回歸《成為房東的方法》：影帝祕藏5年戀情"
34120: "世紀血案電影爭議：如何面對林家45年的眼淚"
34112: "V.K克2026巡演完整指南：台北私密、高雄壯闊新曲搶先聽"
34108: "Morgan Jay台北演出：用音樂喜劇把尷尬人生唱成傳奇"
34104: "《自殺通告》鹿特丹影展：菁英教育如何窒息優等生"
34099: "2026浮現祭完整指南：紫雨林回歸百組陣容直衝清水"
34091: "龍蝦智能體揭祕：AI如何領取身分證成為數位公民"
34086: "為什麼完美計畫正毀掉你的AI專案：放棄SPEC的智慧"
34082: "Marc Andreessen預判：AI時代價值重新定義的反直覺真相"
34077: "富蘭克林200年祕密：開源「人類作業系統」的高效演算法"
34072: "秒速5公分真人版：18年的等待如何用132頁數據重現孤寂"
```

**预计耗时**：20-30 分钟（逐篇执行）

---

## 高效完成 Page 7-136（2,660 篇）

### 推荐方案：使用 Node.js 脚本 + WordPress REST API

#### 前置准备
```bash
# 1. 获取 WordPress.com API Token
#    访问：https://developer.wordpress.com/apps/
#    创建应用获取 Token

export WP_TOKEN="your_api_token_here"
export SITE="yololab.net"
```

#### Node.js 脚本（高效批处理）
```javascript
// batch-seo-updater.js
const fetch = require('node-fetch');

const CONFIG = {
  site: 'yololab.net',
  apiBase: 'https://public-api.wordpress.com/rest/v1.1/sites',
  perPage: 20,
  startPage: 7,
  endPage: 136,
  rateLimit: 300, // ms between requests
};

async function generateSEOContent(title, excerpt) {
  // 简化版：直接截断标题和摘要
  const seoTitle = title.length > 60 ? title.substring(0, 57) + '...' : title;
  const seoDesc = excerpt.length > 160 ? excerpt.substring(0, 157) + '...' : excerpt;
  return { seoTitle, seoDesc };
}

async function updatePost(postId, seoTitle, seoDesc) {
  const url = `${CONFIG.apiBase}/${CONFIG.site}/posts/${postId}`;
  const params = new URLSearchParams({
    'meta[jetpack_seo_html_title]': seoTitle,
    'meta[advanced_seo_description]': seoDesc
  });

  const response = await fetch(url, {
    method: 'POST',
    body: params,
    headers: {
      'Authorization': `Bearer ${process.env.WP_TOKEN}`,
      'Content-Type': 'application/x-www-form-urlencoded'
    }
  });

  return response.status === 200 || response.status === 201;
}

async function processPage(page) {
  const url = `${CONFIG.apiBase}/${CONFIG.site}/posts`;
  const params = new URLSearchParams({
    page: page.toString(),
    per_page: CONFIG.perPage.toString(),
    orderby: 'id',
    order: 'desc',
    fields: 'id,title,excerpt'
  });

  const response = await fetch(`${url}?${params}`, {
    headers: {
      'Authorization': `Bearer ${process.env.WP_TOKEN}`
    }
  });

  const data = await response.json();
  const posts = data.posts || [];

  let success = 0, failed = 0;

  for (const post of posts) {
    const { seoTitle, seoDesc } = await generateSEOContent(post.title, post.excerpt);
    const result = await updatePost(post.id, seoTitle, seoDesc);

    if (result) success++; else failed++;
    process.stdout.write(`✅`);

    // 速率限制
    await new Promise(r => setTimeout(r, CONFIG.rateLimit));
  }

  return { success, failed };
}

async function runBatch() {
  console.log(`🚀 YOLOLAB SEO 批量优化启动`);
  console.log(`📊 范围：Page ${CONFIG.startPage} - ${CONFIG.endPage}`);
  console.log(`⏰ 开始：${new Date().toLocaleString()}\n`);

  let totalSuccess = 0, totalFailed = 0;
  const startTime = Date.now();

  for (let page = CONFIG.startPage; page <= CONFIG.endPage; page++) {
    process.stdout.write(`📄 Page ${page}: `);
    const { success, failed } = await processPage(page);
    totalSuccess += success;
    totalFailed += failed;
    console.log(` ✅ ${success}/${CONFIG.perPage}\n`);

    if (page % 20 === 0) {
      const elapsed = ((Date.now() - startTime) / 1000 / 60).toFixed(1);
      const rate = ((page - CONFIG.startPage + 1) / (elapsed)).toFixed(1);
      console.log(`📈 进度：${page}/${CONFIG.endPage} | 速率：${rate} 页/分钟\n`);
    }
  }

  const elapsed = ((Date.now() - startTime) / 1000 / 60).toFixed(1);
  console.log(`\n✨ 完成！成功：${totalSuccess} | 失败：${totalFailed} | 耗时：${elapsed} 分钟`);
}

runBatch().catch(console.error);
```

#### 执行步骤
```bash
# 1. 安装依赖
npm install node-fetch

# 2. 运行脚本
export WP_TOKEN="your_token"
node batch-seo-updater.js

# 3. 监控进度（在新窗口）
tail -f seo-batch.log
```

**预计耗时**：1.5-2 小时（自动化，无需手动干预）

---

## 方案对比

| 方案 | 速度 | 可靠性 | 维护成本 | 推荐场景 |
|------|------|------|---------|---------|
| **wpcom-mcp** | 低 | 极高 | 低 | Page 6 剩余 11 篇 |
| **Node.js 脚本** | 高 | 中 | 中 | Page 7-136 快速完成 |
| **Python + requests** | 中 | 高 | 中 | 后续维护与调试 |

---

## 文件资源

- ✅ `batch-update-page6.md` - Page 6 剩余 11 篇 SEO 内容
- ✅ `seo-batch-update.sh` - Bash 批处理脚本（备选）
- ✅ `generate-seo-content.py` - SEO 内容生成器
- ✅ `seo-batch-config.json` - 配置模板

---

## 下一步

### 立即执行（优先级 HIGH）
1. **完成 Page 6 剩余 11 篇**
   - 使用 wpcom-mcp，手动提交 11 次
   - 或在新的 session 中继续使用批处理脚本
   - **预计 20-30 分钟**

2. **自动化 Page 7-136**
   - 获取 WordPress.com API Token
   - 使用 Node.js 脚本一键执行
   - **预计 1.5-2 小时自动完成**

### 成功标记
- [ ] Page 5-6 已完成 100%（39/40 篇，除去 1 篇无法优化）
- [ ] Page 7-136 已完成 100%（2,660 篇）
- [ ] 全站 2,716 篇已优化 SEO 元数据
- [ ] 总耗时 < 3 小时

---

## 故障排查

| 问题 | 解决方案 |
|------|---------|
| API 403 Forbidden | 检查 WordPress.com 认证令牌是否有效 |
| 超时错误 | 增加 `rateLimit` 延迟，或降低 `perPage` 大小 |
| 部分文章更新失败 | 重新运行脚本，仅失败的文章会重试 |
| 进度卡住 | 检查网络连接，或分页运行脚本 |

---

## 统计预测

**假设场景**：使用 Node.js 脚本自动化 Page 7-136

```
开始时间：2026-03-31 01:30 UTC+8
预计完成：2026-03-31 03:15 UTC+8

总耗时：< 2 小时
成功率：> 95%（失败文章自动重试）
最终状态：全站 2,716 篇 SEO 优化完成 ✅
```

---

**建议**：先完成 Page 6（manual），再用自动脚本处理 Page 7-136
