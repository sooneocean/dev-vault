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

#PROJECT_TREE

```text
project/
├─src/
│ ├─schemas/
│ │ ├─job.py
│ │ ├─annotation.py
│ │ └─config.py
│ ├─orchestrator/
│ │ ├─job_runner.py
│ │ ├─planner.py
│ │ └─routing.py
│ ├─video/
│ │ ├─extract_frames.py
│ │ ├─encode_video.py
│ │ └─metadata.py
│ ├─tracking/
│ │ ├─dummy_tracker.py
│ │ ├─sam2_bridge.py
│ │ ├─cotracker_bridge.py
│ │ └─mask_smoother.py
│ ├─patch/
│ │ ├─cropper.py
│ │ ├─context_pad.py
│ │ ├─stitcher.py
│ │ ├─blend.py
│ │ └─color_match.py
│ ├─reconstruct/
│ │ ├─mock_processor.py
│ │ ├─comfy_client.py
│ │ ├─workflow_loader.py
│ │ └─patch_processor.py
│ ├─qa/
│ │ ├─contact_sheet.py
│ │ ├─flicker_score.py
│ │ └─side_by_side.py
│ └─cli/
│   └─main.py
├─workflows/
│ └─local_patch_inpaint.json
├─config/
│ ├─default.yaml
│ └─profiles/
│   ├─static_bg.yaml
│   ├─soft_motion.yaml
│   └─complex_motion.yaml
├─examples/
│ ├─jobs/
│ │ └─demo_job.yaml
│ └─annotations/
│   └─demo_frame_annotation.json
├─tests/
│ ├─test_cropper.py
│ ├─test_stitcher.py
│ ├─test_routing.py
│ └─test_job_schema.py
├─assets/
│ ├─input/
│ └─replacements/
└─runs/
```

##模組責任
###schemas
定義所有輸入輸出資料結構。

###orchestrator
負責整條任務流程與策略路由。

###video
負責影片抽幀、資訊讀取、輸出重編碼。

###tracking
負責mask與追蹤抽象，初期先dummy，後面接SAM2與CoTracker。

###patch
負責crop、padding、stitch、blend、顏色修正。

###reconstruct
負責patch processor抽象，先mock，後接ComfyUI。

###qa
負責人工覆核資產與品質分數。

###cli
負責命令列入口。
