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

#IMPLEMENTATION_PHASES

##Phase 1：CLI MVP
###目標
先跑通最小流程。

###內容
-Job schema
-Frame extraction
-Basic annotation loading
-Crop with context
-Mock patch processor
-Stitch back
-Encode video
-CLI entrypoint
-pytest基礎測試

###可交付結果
-可以輸入一支影片
-可以輸入首幀bbox或mask
-可以輸出重新組裝的影片
-有基本日誌
-有最小測試

###風險
-邊界處理錯誤
-crop metadata不完整
-stitch位置偏移
-編碼流程不穩

##Phase 2：ComfyUI接入
###目標
把mock patch processor替換為可切換的ComfyUI patch processor。

###內容
-HTTP client
-workflow template loader
-input field injection
-task polling
-output patch retrieval
-fallback機制

###可交付結果
-可讀取`workflows/*.json`
-可透過API提交patch任務
-可回收patch並接回stitch流程

##Phase 3：Tracking & Mask層
###目標
讓資料流從單幀初始化進化到frame-wise annotations。

###內容
-TrackedObject schema
-FrameAnnotation schema
-Dummy tracker
-mask smoothing抽象
-SAM2 bridge預留介面
-CoTracker bridge預留介面

###可交付結果
-job_runner可優先讀frame-wise annotation
-沒有annotation時回退first-frame模式

##Phase 4：Temporal Stabilization與QA
###目標
降低播動時的閃爍與邊界違和感。

###內容
-mask smoothing
-crop window smoothing
-color/luma correction
-flicker score
-contact sheet
-side-by-side preview

###可交付結果
-最小QA報表
-人工覆核資產
-不穩定鏡頭提示
