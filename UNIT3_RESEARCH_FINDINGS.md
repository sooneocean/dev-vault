# Unit 3 LaMa Inpainter Research Findings

**Research Context:** Pre-implementation research for Unit 3 (LaMa Inpainter with Gaussian Tiling) of RTX 4090 dual-engine watermark removal system.

**Scope:** Model loading patterns, tiling/unfold implementations, edge blending, InpaintExecutor interface, test fixtures, and shape conventions.

---

## 1. Model Loading Patterns

### Reference Implementations

#### Pattern A: Non-ComfyUI Model Loading (Florence-2, from `/0414/app.py`)
Location: `/c/DEX_data/Claude Code DEV/0414/app.py` (lines 23-35)

```python
from transformers import AutoProcessor, AutoModelForCausalLM

# Loading Florence-2 (3.2B params, FP16)
model_id = "microsoft/Florence-2-large"
processor = AutoProcessor.from_pretrained(model_id, trust_remote_code=True)
model = AutoModelForCausalLM.from_pretrained(
    model_id,
    trust_remote_code=True,
    torch_dtype=torch.float16 if device == "cuda" else torch.float32
).to(device)
model.eval()
```

**Key Pattern:**
- Uses `transformers.AutoXXX` (AutoProcessor, AutoModelForCausalLM)
- Explicit `torch_dtype=torch.float16` for CUDA, `torch.float32` for CPU
- `.to(device)` after model instantiation
- `.eval()` mode for inference
- GPU→CPU offload via `.to("cpu")` for memory management

#### Pattern B: SimpleLama Model Loading (from `/0414/app.py` lines 44-50)
```python
from simple_lama_inpainting import SimpleLama

# Loading SimpleLama (wrapper around pretrained model)
self.inpainter_model = SimpleLama()
# SimpleLama handles cuda detection internally, no explicit .to() needed
```

**Key Pattern:**
- High-level wrapper library abstracts model loading
- Automatic device selection (prefers CUDA if available)
- No explicit FP16 dtype specification in wrapper

**Recommendation for Unit 3:**
- **Use transformers.AutoModelForImageInpainting** (preferred, explicit control)
- Alternative: wrapped library (less control but simpler)
- Model source: Hugging Face hub (e.g., `facebook/lama-mpe` or pretrained LaMa variant)

---

## 2. Memory Manager Integration (Unit 1 Complete)

### MemoryManager Interface
Location: `/c/DEX_data/Claude Code DEV/src/watermark_removal/memory_manager.py`

**VRAM Footprint Estimates (from line 60-65):**
```python
MODEL_VRAM_ESTIMATES = {
    "florence2": 8.0,  # FP16 (~3.2B params)
    "lama": 2.0,       # FP16 with tiling ← UNIT 3 TARGET
    "flux": 12.0,      # FP16 + optimizations
    "poisson_blender": 0.5,
}
```

**State Machine (lines 17-28):**
```
IDLE → INPAINT_LOADING → INFERRING → INPAINT_CLEANUP → POSTPROCESS → IDLE
```

**Integration Pattern:**
```python
# Load model with memory validation
memory_manager.transition_to(MemoryState.INPAINT_LOADING)
memory_manager.validate_vram_headroom(threshold_gb=2.5)  # LaMa estimate + buffer
model = load_lama_model(...)
memory_manager.load_model("lama", model_instance)
memory_manager.transition_to(MemoryState.INFERRING)

# Infer tiles...

memory_manager.transition_to(MemoryState.INPAINT_CLEANUP)
memory_manager.unload_model("lama")
memory_manager.transition_to(MemoryState.IDLE)
```

**Key Methods:**
- `transition_to(target_state)`: State validation (raises ValueError on invalid transition)
- `validate_vram_headroom(threshold_gb)`: Raises `InsufficientVRAMError` if insufficient
- `load_model(model_name, model_instance)`: Register model for cleanup
- `unload_model(model_name)`: GPU cleanup + `torch.cuda.empty_cache()`
- `estimate_peak_vram(engine_name, image_resolution)`: Returns estimated VRAM in GB

---

## 3. Edge Blending / Gaussian Weighting (Production Reference)

### Location
`/c/DEX_data/Claude Code DEV/src/watermark_removal/postprocessing/edge_blending.py`

### Gaussian Feather Mask Creation (NOT 2D Gaussian window, but distance-based gradient)

**Method: `create_distance_feather_mask()` (lines 54-103)**
```python
def create_distance_feather_mask(self, shape: tuple, region_bbox: tuple, blur: bool = True) -> np.ndarray:
    """Create feather mask using distance transform for gradient fade."""
    height, width = shape
    x, y, w, h = region_bbox

    # 1. Create binary mask of region
    binary_mask = np.zeros((height, width), dtype=np.uint8)
    x_end = min(x + w, width)
    y_end = min(y + h, height)
    binary_mask[y:y_end, x:x_end] = 255

    # 2. Create inverse mask (outside region)
    inverse_mask = 255 - binary_mask

    # 3. Compute Euclidean distance from boundaries
    distance = cv2.distanceTransform(inverse_mask, cv2.DIST_L2, cv2.DIST_MASK_PRECISE)

    # 4. Normalize distance to feather width (gradient)
    feather_mask = np.clip(distance / self.feather_width, 0, 1)

    # 5. Invert so inner region is 1.0, boundary fades to 0.0
    feather_mask = 1.0 - feather_mask

    # 6. Ensure inner region always 1.0
    feather_mask = np.maximum(feather_mask, binary_mask.astype(np.float32) / 255.0)

    # 7. Optional Gaussian blur for smoothing
    if blur:
        feather_mask_uint8 = (feather_mask * 255).astype(np.uint8)
        blurred = cv2.GaussianBlur(feather_mask_uint8, (self.blur_kernel_size, self.blur_kernel_size), 0)
        feather_mask = blurred.astype(np.float32) / 255.0

    return feather_mask  # float32, shape (height, width), values [0, 1]
```

**Output Properties:**
- dtype: `np.float32`
- values: `[0.0, 1.0]` (0 at boundaries, 1.0 at center)
- shape: Same as input `shape` (full image, not per-tile)

### Blending Application (lines 105-159)
```python
def blend_edges(self, original, inpainted, region_bbox, blend_mask=None):
    """Blend using: output = original * (1 - mask) + inpainted * mask"""
    if blend_mask is None:
        blend_mask = self.create_distance_feather_mask(original.shape[:2], region_bbox, blur=True)

    # Extract region from blend_mask and resize to match inpainted crop
    region_mask = blend_mask[y:y_end, x:x_end]
    region_mask = cv2.resize(region_mask, (actual_w, actual_h)) if needed

    # Per-channel blending
    for c in range(3):  # BGR
        blended[y:y_end, x:x_end, c] = (
            original[y:y_end, x:x_end, c].astype(np.float32) * (1 - region_mask)
            + inpainted_resized[:, :, c].astype(np.float32) * region_mask
        )

    return blended.astype(np.uint8)
```

### Critical Insight for Tile Blending
- Production uses **distance-transform-based gradient** (not pure 2D Gaussian)
- Applied **per-region** in full-frame coordinates
- For **tiling**, a **pure 2D Gaussian window** centered on each tile is more efficient than computing distance transform per-tile
- **Recommendation:** Use `scipy.signal.windows.gaussian2d()` or manual 2D Gaussian for tile-local weighting

---

## 4. InpaintExecutor Interface

### Location
`/c/DEX_data/Claude Code DEV/src/watermark_removal/inpaint/inpaint_executor.py`

**Critical Finding:** Current executor is **ComfyUI-specific** (async, remote server). Unit 3 LaMa inpainter should be **synchronous local inference**.

### Current InpaintExecutor (for reference, NOT for Unit 3)
```python
async def inpaint_single(
    self,
    image_path: str,
    mask_path: str,
    config: InpaintConfig,
    output_dir: str,
) -> Path:
    """Submit crop for inpaint to ComfyUI server."""
    # Submits workflow to ComfyUI via REST API
    # Returns Path to output file
```

**Key Pattern NOT needed for Unit 3:**
- File-based I/O (paths, not numpy arrays)
- Async execution (`async`/`await`)
- ComfyUI workflow JSON

### InpaintConfig (REUSE THIS)
Location: `/c/DEX_data/Claude Code DEV/src/watermark_removal/core/types.py` (lines 99-123)

```python
@dataclass
class InpaintConfig:
    model_name: str = "flux-dev.safetensors"
    prompt: str = "remove watermark, clean background"
    negative_prompt: str = "watermark, text, artifacts, blurry"
    steps: int = 20
    cfg_scale: float = 7.5
    seed: int = 42
    sampler: str = "euler"
```

**For Unit 3 LaMa:**
- Model params (steps, cfg_scale) **not applicable** to LaMa (no diffusion)
- Use config for consistency, but ignore diffusion-specific fields
- OR create `LamaInpaintConfig` subclass with LaMa-specific params

---

## 5. Test Fixtures for Image/Mask Inpainting

### Image Fixture Pattern
Location: `/c/DEX_data/Claude Code DEV/tests/test_inpaint_executor.py` (lines 17-22)

```python
def create_dummy_image(path: str, width: int = 1024, height: int = 1024) -> None:
    """Create a dummy PNG image for testing."""
    image = np.zeros((height, width, 3), dtype=np.uint8)
    image[:, :] = [100, 150, 200]  # BGR color
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(path, image)
```

**Key Convention:**
- **Shape:** `(height, width, 3)` NOT `(width, height, 3)`
- **dtype:** `np.uint8` (0-255 range)
- **Color:** BGR (OpenCV convention)

### Mask Fixture Patterns
Location: `/c/DEX_data/Claude Code DEV/tests/test_crop_handler.py` (lines 32-70)

**Pattern A: BBOX Mask (dict-based)**
```python
def create_bbox_mask(x: int, y: int, w: int, h: int) -> Mask:
    return Mask(
        type=MaskType.BBOX,
        data={"x": x, "y": y, "w": w, "h": h},
        valid_frame_range=(0, 0),
    )
```

**Pattern B: IMAGE Mask (numpy-based, binary)**
```python
def create_image_mask_with_circle(mask_width, mask_height, circle_x, circle_y, radius):
    mask = np.zeros((mask_height, mask_width), dtype=np.uint8)
    cv2.circle(mask, (circle_x, circle_y), radius, 255, -1)  # 255 = inpaint region
    return Mask(
        type=MaskType.IMAGE,
        data=mask,
        valid_frame_range=(0, 0),
    )
```

**Key Convention:**
- **Inpaint mask:**
  - dtype: `np.uint8`
  - values: `0` = keep (don't inpaint), `255` = inpaint region
  - shape: `(height, width)` grayscale, NOT RGB

---

## 6. Shape Conventions Summary

| Component | Shape | dtype | Range | Notes |
|-----------|-------|-------|-------|-------|
| **Image (frame)** | (H, W, 3) | uint8 | 0-255 | BGR order (OpenCV) |
| **Inpaint Mask** | (H, W) | uint8 | 0-255 | 0=keep, 255=inpaint |
| **Blend Mask** | (H, W) | float32 | 0.0-1.0 | Feather gradient |
| **Image (internal)** | (H, W, 3) | float32 | 0.0-255.0 | Intermediate computation |

---

## 7. LaMa Model-Specific Patterns (from `/0414/app.py`)

### Tiling Implementation Reference (lines 146-198)

```python
class SeamlessInpainter:
    def _get_gaussian_mask(self, size):
        """Produce 2D Gaussian weight matrix."""
        mask = np.zeros((size, size))
        sigma = size / 4
        center = size // 2
        for i in range(size):
            for j in range(size):
                dist_sq = (i - center)**2 + (j - center)**2
                mask[i, j] = np.exp(-dist_sq / (2 * sigma**2))
        return mask  # float, values [0, 1], peak at center

    def process(self, image_np, mask_np, patch_size=512, stride=256):
        """Tile-based inpainting with Gaussian blending."""
        # 1. Pad image/mask to multiple of stride
        pad_h = (stride - h % stride) % stride
        pad_w = (stride - w % stride) % stride
        img_padded = np.pad(image_np, ((0, pad_h), (0, pad_w), (0, 0)), mode='reflect')
        mask_padded = np.pad(mask_np, ((0, pad_h), (0, pad_w)), mode='reflect')

        # 2. Create accumulators
        accumulator = np.zeros((new_h, new_w, 3), dtype=np.float32)
        weight_map = np.zeros((new_h, new_w), dtype=np.float32)

        # 3. Generate Gaussian tile mask
        g_mask = self._get_gaussian_mask(patch_size)

        # 4. Iterate tiles with stride
        for y in range(0, new_h - patch_size + 1, stride):
            for x in range(0, new_w - patch_size + 1, stride):
                img_patch = img_padded[y:y+patch_size, x:x+patch_size]
                mask_patch = mask_padded[y:y+patch_size, x:x+patch_size]

                # Skip if no inpaint region (optimization)
                if np.max(mask_patch) < 10:
                    patch_result = img_patch.astype(np.float32)
                else:
                    # LaMa inference (SimpleLama returns PIL Image)
                    pil_patch = Image.fromarray(img_patch)
                    pil_mask = Image.fromarray(mask_patch)
                    patch_result = np.array(self.inpainter_model(pil_patch, pil_mask)).astype(np.float32)

                # 5. Weighted accumulation (Gaussian center-weighted)
                for c in range(3):
                    accumulator[y:y+patch_size, x:x+patch_size, c] += patch_result[:, :, c] * g_mask
                weight_map[y:y+patch_size, x:x+patch_size] += g_mask

        # 6. Normalize by weight map (handles overlaps)
        weight_map = np.expand_dims(weight_map, axis=-1)
        final_img = accumulator / (weight_map + 1e-8)
        final_img = np.clip(final_img, 0, 255).astype(np.uint8)

        # 7. Crop back to original size
        result = final_img[:h, :w]
        return result
```

**Key Insights:**
1. **Tile Size:** 512×512 (default), stride 256 → 50% overlap
2. **Padding:** Reflect mode to handle boundaries
3. **Gaussian Window:** Simple 2D Gaussian (not distance-transform)
4. **Accumulator:** Float32, weighted sum of tile outputs
5. **Weight Normalization:** Divides by weight_map to handle overlaps
6. **PIL Bridge:** LaMa expects PIL Image, not numpy

---

## 8. Existing Code Using torch.unfold (Search Results)

**Finding:** No existing use of `torch.nn.functional.unfold()` in codebase.

**Implication:** Unit 3 will introduce unfold/fold pattern as **new implementation pattern** for efficient tiling.

---

## 9. Directory and Module Structure

### Inpaint Module
Location: `/c/DEX_data/Claude Code DEV/src/watermark_removal/inpaint/`

**Current Files:**
- `inpaint_executor.py`: ComfyUI async client
- `workflow_builder.py`: Flux workflow template builder
- `__init__.py`: Exports WorkflowBuilder

**Unit 3 Addition:**
- `lama_inpainter.py`: ← Create here

### Module Import Pattern (for `__init__.py` update)
```python
# Current __init__.py
from .workflow_builder import WorkflowBuilder
__all__ = ["WorkflowBuilder"]

# Updated __init__.py (Unit 3)
from .workflow_builder import WorkflowBuilder
from .lama_inpainter import LamaInpainter  # ← Add
__all__ = ["WorkflowBuilder", "LamaInpainter"]  # ← Update
```

---

## 10. Test Pattern for Inpainting Operations

### Test Structure (from `test_inpaint_executor.py`)

```python
class TestInpaintExecutorHappyPath:
    """Happy path tests."""

    @pytest.mark.asyncio
    async def test_inpaint_single(self, executor, config):
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create dummy image and mask
            image_path = f"{tmpdir}/crop.png"
            mask_path = f"{tmpdir}/mask.png"
            output_dir = f"{tmpdir}/output"

            create_dummy_image(image_path)
            create_dummy_image(mask_path)

            # Mock or run actual inference
            result = await executor.inpaint_single(
                image_path=image_path,
                mask_path=mask_path,
                config=config,
                output_dir=output_dir,
            )

            assert result.exists()
            assert result.is_file()

class TestInpaintExecutorEdgeCases:
    """Edge cases."""

    @pytest.mark.asyncio
    async def test_empty_batch(self, executor, config):
        results = await executor.inpaint_batch(
            image_mask_pairs=[],
            config=config,
            output_dir="/tmp",
        )
        assert results == []

    @pytest.mark.asyncio
    async def test_boundary_condition(self, executor, config):
        """Test image at resolution boundary (2048×2048)."""
        # Create 2048×2048 image
        create_dummy_image(path, width=2048, height=2048)
        # Should use full-image path (not tiling)
        result = await executor.inpaint_single(...)
        assert result.exists()

class TestInpaintExecutorErrors:
    """Error handling."""

    @pytest.mark.asyncio
    async def test_nan_detection(self, executor, config):
        """Test that NaN output raises exception."""
        # Mock inference to return NaN
        with pytest.raises(ValueError, match="NaN"):
            await executor.inpaint_single(...)
```

---

## 11. Recommendations for Unit 3 Implementation

### 1. Model Loading
- **Use:** `transformers.AutoModelForImageInpainting` (explicit control over FP16/device)
- **Alternative:** wrapped library (e.g., `simple_lama_inpainting`) for faster prototyping
- **Memory:** Integrate with `MemoryManager` (already complete in Unit 1)

### 2. Tiling Strategy
- **Boundary condition:** Resolution ≤2048×2048 → full-image path (no tiling)
- **High-res (>2048×2048):** Sliding-window tiling with 512×512 tiles, 256px stride (50% overlap)
- **Edge handling:** Pad with reflect mode, crop output back to original size
- **Unfold/Fold:** Can use `torch.nn.functional.unfold/fold()` OR loop (loop is clearer for learning)

### 3. Gaussian Blending
- **2D Gaussian window:** Use simple 2D Gaussian (lines 135-144 of `/0414/app.py` pattern)
- **NOT distance-transform:** Distance-based blending is for full-frame regions; tiles use local Gaussian windows
- **Accumulation:** Float32 accumulator with weight normalization (handles overlaps naturally)

### 4. Testing
- **Happy path (full-image):** 512×512 input → no tiling → output 512×512
- **Happy path (tiling):** 4096×4096 input → tiling → 4096×4096 output
- **Boundary:** 2048×2048 → full-image path (verify no tiling occurs)
- **Seam detection:** Visual inspection or MSE between seam regions and adjacent areas
- **NaN check:** Verify no NaN in output, log warning/error if present

### 5. Integration Points
- **MemoryManager:** Call `transition_to()`, `validate_vram_headroom()`, `load_model()`, `unload_model()`
- **InpaintConfig:** Use existing config (or create `LamaInpaintConfig` variant)
- **Edge Blending:** Can integrate `EdgeBlender` for post-tile seam smoothing (deferred to Unit 8 quality validation)

---

## 12. File Paths Summary

| Component | File Path |
|-----------|-----------|
| **Memory Manager (Unit 1)** | `/c/DEX_data/Claude Code DEV/src/watermark_removal/memory_manager.py` |
| **InpaintConfig** | `/c/DEX_data/Claude Code DEV/src/watermark_removal/core/types.py` (lines 99-123) |
| **InpaintExecutor (reference)** | `/c/DEX_data/Claude Code DEV/src/watermark_removal/inpaint/inpaint_executor.py` |
| **EdgeBlender (reference)** | `/c/DEX_data/Claude Code DEV/src/watermark_removal/postprocessing/edge_blending.py` |
| **CropHandler (reference)** | `/c/DEX_data/Claude Code DEV/src/watermark_removal/preprocessing/crop_handler.py` |
| **LaMa Tiling Reference** | `/c/DEX_data/Claude Code DEV/0414/app.py` (lines 131-198) |
| **Test Fixtures (inpaint)** | `/c/DEX_data/Claude Code DEV/tests/test_inpaint_executor.py` |
| **Test Fixtures (crop)** | `/c/DEX_data/Claude Code DEV/tests/test_crop_handler.py` |
| **Test Fixtures (edge blend)** | `/c/DEX_data/Claude Code DEV/tests/test_edge_blending.py` |
| **Target: Create** | `/c/DEX_data/Claude Code DEV/src/watermark_removal/lama_inpainter.py` |
| **Target: Create** | `/c/DEX_data/Claude Code DEV/tests/test_lama_tiling.py` |
| **Target: Modify** | `/c/DEX_data/Claude Code DEV/src/watermark_removal/inpaint/__init__.py` |

---

## 13. Critical Code Snippets for Copy-Paste Reference

### Gaussian 2D Window Generator
```python
def _create_gaussian_window(self, size: int, sigma: float | None = None) -> np.ndarray:
    """Create 2D Gaussian window for tile weighting.

    Args:
        size: Window size (e.g., 512).
        sigma: Standard deviation (default: size/4 for good falloff).

    Returns:
        float32 array (size, size), values [0, 1], peak 1.0 at center.
    """
    if sigma is None:
        sigma = size / 4.0

    window = np.zeros((size, size), dtype=np.float32)
    center = size // 2

    for i in range(size):
        for j in range(size):
            dist_sq = (i - center) ** 2 + (j - center) ** 2
            window[i, j] = np.exp(-dist_sq / (2 * sigma ** 2))

    return window
```

### Tile Accumulation Pattern
```python
# Accumulate weighted tiles
for c in range(3):
    accumulator[y:y+h, x:x+w, c] += tile_output[:, :, c] * gaussian_window
weight_map[y:y+h, x:x+w] += gaussian_window

# Normalize
weight_map_3ch = np.expand_dims(weight_map, axis=-1)
final = accumulator / (weight_map_3ch + 1e-8)
final = np.clip(final, 0, 255).astype(np.uint8)
```

### Memory Manager Integration Template
```python
from src.watermark_removal.memory_manager import MemoryManager, MemoryState

manager = MemoryManager(device="cuda", vram_safety_threshold_gb=1.0)

# Before inpainting
manager.transition_to(MemoryState.INPAINT_LOADING)
manager.validate_vram_headroom(threshold_gb=2.5)  # LaMa estimate
lama_model = load_lama_model(...)  # Your load function
manager.load_model("lama", lama_model)

manager.transition_to(MemoryState.INFERRING)
# ... inpaint tiles ...
manager.transition_to(MemoryState.INPAINT_CLEANUP)

manager.unload_model("lama")
manager.transition_to(MemoryState.IDLE)
```

---

## Summary Table: Research Completeness

| Research Question | Answer | Source |
|-------------------|--------|--------|
| **1. How are existing models loaded (non-ComfyUI)?** | Use transformers.Auto* with explicit FP16/device control | `/0414/app.py`, lines 23-35 |
| **2. Are there existing unfold/fold implementations?** | NO — new pattern for Unit 3 | Grep search (no results) |
| **3. How is edge_blending.py implemented?** | Distance-transform-based feather + cv2.GaussianBlur | `/edge_blending.py`, lines 54-103 |
| **4. What is InpaintExecutor interface?** | Async ComfyUI client (not for Unit 3); reuse InpaintConfig | `/inpaint_executor.py` |
| **5. How are tests structured for inpainting?** | Pytest with fixtures (create_dummy_image, mocks) | `/test_inpaint_executor.py` |
| **6. What are shape conventions?** | Images (H,W,3) uint8 BGR; Masks (H,W) uint8 0-255 | `/test_crop_handler.py`, `/test_inpaint_executor.py` |
| **7. Are there Gaussian weighting examples?** | YES, in `/0414/app.py` lines 135-144 | `/0414/app.py` |
| **8. How is memory managed?** | MemoryManager state machine (Unit 1 complete) | `/memory_manager.py` |

---

## Next Steps for Unit 3 Implementation

1. **Read:** MemoryManager API documentation (already summarized above)
2. **Verify:** Available LaMa model checkpoint (HuggingFace hub or local weights)
3. **Implement:** `LamaInpainter` class with:
   - Model loading (transformers.AutoModelForImageInpainting)
   - Resolution detection (≤2048×2048 vs. >2048×2048)
   - Tiling + Gaussian blending for high-res
   - NaN detection + logging
4. **Test:** Create `/tests/test_lama_tiling.py` with scenarios in Section 5 of requirements
5. **Integration:** Update `/src/watermark_removal/inpaint/__init__.py` to export LamaInpainter

---

**Research Completed:** 2026-04-16
**Status:** Ready for implementation
