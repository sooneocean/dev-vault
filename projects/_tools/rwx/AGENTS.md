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

#AGENTS

##Project
Dynamic Overlay Tracking, Redaction, Replacement, and Local Reconstruction Pipeline

##Mission
Build a production-oriented video post-processing pipeline for legally authorized assets only.

The system processes dynamic overlay regions that may be:
-irregular in shape
-moving over time
-changing scale or rotation
-partially transparent
-deforming frame by frame

The project must support:
-overlay detection
-overlay tracking
-mask propagation
-local reconstruction
-redaction
-replacement
-temporal stabilization
-video export
-quality review

This project must not be framed or implemented as a tool for bypassing ownership protections on third-party media.

##Product Framing
Treat the problem as:
“track and process a dynamic overlay region in authorized video assets”

Do not treat it as:
“recover unauthorized source imagery”

##Architecture
The system is divided into:
1.Orchestrator Layer
2.Video IO Layer
3.Tracking and Mask Layer
4.Region Processing Layer
5.Temporal Stabilization and QA Layer

##Core Routing Logic
Prefer:
-authorized replacement asset exists -> replace
-sensitive content should be hidden -> redact
-small region + low motion -> local reconstruct
-neighboring frames usable -> temporal patch fill
-otherwise -> replace or redact fallback

##ComfyUI Integration Rules
Use ComfyUI only as a patch-level inference worker.

External Python handles:
-video IO
-job parsing
-schema validation
-mask management
-crop and stitch
-temporal hooks
-encoding
-QA output

ComfyUI handles:
-local patch workflows
-inpaint or img2img style patch processing
-batch inference

##Implementation Order
1.Define schemas
2.Define config
3.Build frame extraction / encoding
4.Build crop / stitch
5.Build mock patch processor
6.Build ComfyUI client
7.Build job runner
8.Build CLI
9.Add tests
10.Then improve tracking

##Data Rules
Each frame annotation must describe:
-frame index
-mask path
-bbox
-polygon
-confidence
-motion hint

Each crop must preserve:
-source frame size
-crop coordinates
-padding
-resize ratio
-stitch metadata

##Coding Rules
-Use Python 3.11+
-Use type hints
-Prefer pydantic or dataclasses
-Keep modules narrow
-Avoid premature abstraction
-Write tests for geometry-sensitive logic
-Use yaml for editable config
-Do not bury business logic inside helpers
-Keep deterministic filenames and logs

##When You Implement
Always output in this order:
1.narrow goal
2.files to create or edit
3.schema changes
4.config changes
5.implementation plan
6.code
7.tests
8.next best step
