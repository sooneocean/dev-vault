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

#CONFIG_SCHEMA

##1.Job YAML範例
```yaml
job_id: job_demo_001
video_path: assets/input/demo.mp4
output_dir: runs/job_demo_001
processing_mode: replace
profile: soft_motion
target_tracks:
  - overlay_01

mask_init:
  type: manual_first_frame_bbox
  bbox_xyxy: [1402, 74, 1718, 236]

replacement_asset: assets/replacements/logo_clean.png
```

##2.全域設定範例
```yaml
video:
  extract_format: png
  ffmpeg_path: ffmpeg

crop:
  context_padding_ratio: 0.18
  min_crop_size: 128
  target_patch_resolution: 1024
  keep_aspect_ratio: true
  crop_window_smoothing_strength: 0.0

stitch:
  feather_radius: 12
  color_match: true
  luma_match: true

processing:
  default_strategy: replace
  fallback_strategy: redact

comfyui:
  enabled: false
  base_url: http://127.0.0.1:8188
  workflow_path: workflows/local_patch_inpaint.json
  poll_interval_sec: 1.0
  timeout_sec: 180

qa:
  export_contact_sheet: true
  export_side_by_side: true
  flicker_score_enabled: false
```

##3.FrameAnnotation
```json
{
  "frame_index": 12,
  "objects": [
    {
      "track_id": "overlay_01",
      "class": "dynamic_overlay",
      "mask_path": "masks/000012_overlay_01.png",
      "bbox_xyxy": [1402, 74, 1718, 236],
      "polygon": [[1402,80],[1500,74],[1718,100],[1708,236],[1408,228]],
      "confidence": 0.95,
      "alpha_hint": 0.61,
      "motion_hint": {
        "cx": 1562.4,
        "cy": 154.1,
        "scale": 1.02,
        "rotation_deg": -1.3
      }
    }
  ]
}
```

##4.資料結構原則
-bbox只負責裁切
-mask或polygon負責不規則形狀
-motion_hint負責後續平滑
-alpha_hint負責軟邊界與半透明提示
-confidence可用於策略回退與QA標記

##5.必要schema
###JobSpec
-job_id
-video_path
-output_dir
-processing_mode
-profile
-target_tracks
-mask_init
-replacement_asset(optional)

###TrackedObject
-track_id
-class
-mask_path(optional)
-bbox_xyxy
-polygon(optional)
-confidence
-alpha_hint(optional)
-motion_hint(optional)

###CropMetadata
-frame_index
-source_width
-source_height
-crop_xyxy
-padding_ratio
-resize_from
-resize_to
-track_id
