---
title: 手動停用外掛指南
type: project
tags: [project, active]
created: 2026-04-03
updated: "2026-04-03"
status: "archived"
maturity: growing
domain: knowledge-management
summary: ""
---

# 手動停用外掛指南

## 第一步：訪問外掛頁面

1. 打開瀏覽器，進入：
   **https://yololab.net/wp-admin/plugins.php**

2. 用你的帳號登入：
   - 郵件：yololab.life@gmail.com
   - 密碼：(已設置)

---

## 第二步：停用 SpeedyCache

1. 在外掛列表中找到 **SpeedyCache**
2. 點擊 **停用** 連結
3. 看到確認訊息後，確認已停用

截圖位置示例：
```
外掛名稱: SpeedyCache 1.3.8
狀態列: [停用] ← 點擊這個
```

---

## 第三步：停用 Page Optimize

1. 在外掛列表中找到 **Page Optimize**
2. 點擊 **停用** 連結  
3. 看到確認訊息後，確認已停用

截圖位置示例：
```
外掛名稱: Page Optimize 0.6.2
狀態列: [停用] ← 點擊這個
```

---

## 第四步：驗證關鍵外掛仍為啟用

檢查以下外掛為 **綠色/已啟用** 狀態：

1. ✅ **Jetpack Boost** - 主要性能外掛
   - 位置：務必顯示 "停用" 連結

2. ✅ **Jetpack** - 基礎套件
   - 位置：務必顯示 "停用" 連結

3. ✅ **Imagify** - 圖片優化
   - 位置：務必顯示 "停用" 連結

4. ✅ **Yoast SEO** - SEO 優化
   - 位置：務必顯示 "停用" 連結

---

## 驗證完成

完成後，你會看到：

**已停用的外掛（2 個）：**
- [ ] SpeedyCache
- [ ] Page Optimize

**仍已啟用的關鍵外掛：**
- [x] Jetpack
- [x] Jetpack Boost
- [x] Imagify
- [x] Yoast SEO

---

## 完成時間

預計時間：**2-3 分鐘**

完成後，系統將自動清除快取。頁面速度應在 15 分鐘內改善。

