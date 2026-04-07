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

#PROJECT_BLUEPRINT

##1.專案目的
建立一套由外部agent調度、由ComfyUI承接局部patch推理的影片後期系統，用來處理**不規則形狀、時間上變形、可能移動、可能半透明**的動態疊加物。

這套系統的核心任務不是「恢復未授權原圖」，而是：

-追蹤overlay region
-輸出穩定的每幀mask
-依場景選擇合法策略
-完成替換、遮蔽、局部重建
-降低時序閃爍
-輸出可交付影片與QA結果

##2.系統總體架構
系統分成五層。

###A.Orchestrator Layer
責任：
-讀取job
-解析config
-切分工作階段
-選擇處理策略
-調用ComfyUI API
-追蹤任務進度
-處理失敗重試
-輸出日誌與QA成品

輸入：
-job yaml/json
-影片路徑
-初始化mask、點位或bbox
-profile設定

輸出：
-frames
-annotations
-processed frames
-final video
-QA artifacts

###B.Video IO Layer
責任：
-抽幀
-讀取fps、解析度、duration
-重編碼輸出影片
-生成預覽圖
-輸出差異預覽

###C.Tracking & Mask Layer
責任：
-初始化目標區域
-影片級mask propagation
-點追蹤
-mask修正
-mask temporal smoothing
-bbox與crop window擬合

建議演進：
-第一版：人工提供首幀mask或bbox
-第二版：SAM2做影片分割傳播
-第三版：CoTracker幫助穩定關鍵點與局部變形

###D.Region Processing Layer
責任：
-依bbox/mask計算crop
-加入context padding
-局部patch處理
-縫回原畫面
-做邊界羽化與顏色修正

支援策略：
-redact
-replace
-local reconstruct
-temporal patch fill

###E.Temporal Stabilization & QA Layer
責任：
-mask smoothing
-crop smoothing
-patch flicker suppression
-luma/color一致化
-QA評分
-contact sheet
-人工覆核輸出

##3.策略路由
不要把全部場景都丟進同一條路線。應先做策略判斷。

```text
if authorized_replacement_asset_exists:
    use replace
elif region_is_sensitive_or_should_be_hidden:
    use redact
elif region_small and background_motion_low:
    use local_reconstruct
elif neighboring_frames_are_usable:
    use temporal_patch_fill
else:
    fallback to replace_or_redact
```

##4.推薦MVP方案
最適合MVP的是**混合式架構**。

###外部Python負責
-讀取job
-抽幀
-資料格式驗證
-mask讀寫
-crop計算
-stitch
-ffmpeg重編碼
-QA輸出
-任務重試

###ComfyUI負責
-局部patch的高品質image-to-image或inpaint workflow
-批次patch推理
-回傳輸出patch

###為什麼這樣最適合MVP
-影片工程控制用Python更穩
-ComfyUI擅長模型推理，不擅長整體任務編排
-工作流JSON可以獨立維護
-之後替換模型更容易
-便於Codex逐檔生成與測試

##5.資料流
```text
Video Input
 -> Frame Extraction
 -> First-frame Init (mask / bbox / points)
 -> Frame-wise Annotation Generation
 -> Crop Window Calculation + Context Padding
 -> Strategy Routing
 -> Patch Processing (ComfyUI or fallback processor)
 -> Stitch Back
 -> Temporal Stabilization Hooks
 -> Video Encode
 -> QA Export
```

##6.關鍵設計原則
###6.1合法使用範圍
系統僅服務於：
-自有素材
-已授權素材
-品牌overlay替換
-隱私資訊遮蔽
-內部後期修補

###6.2不要過早做複雜時序模型
第一版先跑通：
-單一track
-單一策略
-CLI
-local output
-mock processor
-基本測試

###6.3把schema放在最前面
每一輪擴充前，先做：
-schema
-config
-module
-test
-cli接線

###6.4工作流與業務邏輯分離
-`workflows/*.json`只放ComfyUI workflow template
-`src/reconstruct/comfy_client.py`只負責API互動
-`src/orchestrator/*`負責任務流程
-`src/patch/*`負責crop與stitch

##7.成功標準
專案成功代表它可以：
-追蹤動態不規則overlay
-生成穩定的每幀mask
-正確執行合法處理策略
-維持可接受的時序穩定性
-輸出可審核影片
-生成QA artifacts供人工覆核
