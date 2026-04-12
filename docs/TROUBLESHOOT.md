# Troubleshooting Guide

## Connection Issues

**ComfyUI not reachable**
- Verify ComfyUI is running: `http://localhost:8188` in browser
- Check port in config (default: 8188)
- If on different machine: set `comfyui_host` to server IP

## Quality Issues

**Visible seams at crop edges**
- Increase feather blending: `blend_feather_width: 64`
- Add more context: `context_padding: 100`
- Strengthen inpaint guidance: `cfg_scale: 10.0` + more `steps: 30`

**Watermark still visible or poor quality**
- Improve prompt: `"seamlessly inpaint watermark region, blend naturally"`
- Try different model: `model_name: flux-pro`
- Increase quality: `steps: 30`, `cfg_scale: 10.0`, `context_padding: 100`

## Performance Issues

**GPU out of memory**
- Reduce batch: `batch_size: 1`
- Smaller inpaint region: `target_inpaint_size: 512`
- Fewer steps: `steps: 10-15`

**FFmpeg encoding fails/hangs**
- Verify FFmpeg: `ffmpeg -version`
- Try different codec: `output_codec: h265`
- Check disk space
- Smaller batch: `batch_size: 2`

## Debugging

Enable verbose logging: `verbose: true`

Keep intermediate files: `keep_intermediate: true`
- `output/frames/` — extracted frames
- `output/crops/` — cropped watermark regions
- `output/inpainted/` — ComfyUI results
- `output/stitched/` — reconstructed frames

See quality metrics: `save_checkpoints: true` → `output/metrics.csv`
