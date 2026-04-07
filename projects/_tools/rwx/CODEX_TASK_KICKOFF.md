---
title: Untitled
type: project
tags: [project, active]
created: 2026-04-03
updated: 2026-04-03
status: active
maturity: growing
domain: knowledge-management
summary: ""
---

#CODEX_TASK_KICKOFF

請根據repo內的`AGENTS.md`、`PROJECT_BLUEPRINT.md`、`CONFIG_SCHEMA.md`與`PROJECT_TREE.md`，先完成第一輪CLI MVP骨架。

##目標
建立一個可執行的CLI原型，用於合法授權素材中的動態疊加物處理流程。

##第一輪範圍
只做最小可跑版本，不要做GUI，不要做完整tracking模型，不要做過度抽象。

需要支援：
1.讀取job yaml
2.解析影片資訊
3.抽出frames
4.載入第一幀mask或bbox資料
5.根據bbox計算帶context的crop window
6.保存crop metadata
7.實作一個mock patch processor，暫時不接ComfyUI
8.把patch原樣stitch回原圖
9.輸出重組影片
10.寫基本pytest測試

##輸出順序
請依序輸出：
1.專案檔案樹
2.第一輪要建立的檔案
3.每個檔案的責任
4.實作順序
5.然後直接開始寫程式碼

##工程要求
-使用Python 3.11+
-完整型別註解
-用yaml作設定
-先定義schema
-先做CLI版本
-保留ComfyUI接入點
-保留future temporal stabilization hook
-不要一次改很多無關檔案
-先讓專案可以跑，再往下擴充
