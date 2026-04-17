"""Gradio Blocks interface for RTX 4090 dual-engine watermark removal."""

import logging
import gradio as gr
import numpy as np
from PIL import Image
from typing import Tuple

from .memory_manager import MemoryManager
from .florence2_detector import Florence2Detector
from .dual_engine_router import DualEngineRouter, InpaintEngine, InpaintEngineConfig

logger = logging.getLogger(__name__)


def create_app():
    """Create Gradio Blocks interface for watermark removal."""

    # Initialize managers
    memory_manager = MemoryManager(device="cuda")
    florence2 = Florence2Detector(device="cuda", confidence_threshold=0.5)
    router = None  # Lazy-init per request

    def detect_watermarks(
        image: Image.Image,
        enable_auto_detect: bool,
        confidence_threshold: float,
    ) -> Tuple[Image.Image, str]:
        """Detect watermarks using Florence-2."""
        if image is None:
            return None, "No image provided"

        try:
            if not enable_auto_detect:
                # Return all-white mask (no auto-detection)
                mask = Image.new("RGB", image.size, (255, 255, 255))
                return mask, "Auto-detection disabled (manual mask mode)"

            # Run Florence-2 detection
            mask_np, bboxes = florence2.detect(image)

            # Convert to PIL for display
            mask_pil = Image.fromarray(mask_np, "L")

            status = f"Detected {len(bboxes)} watermark regions"
            return mask_pil, status
        except Exception as e:
            return None, f"Detection failed: {e}"

    def inpaint_image(
        image: Image.Image,
        mask: Image.Image,
        engine: str,
        lama_tile_size: int,
        lama_overlap: int,
        flux_guidance: float,
        flux_steps: int,
        flux_offload: bool,
    ) -> Tuple[Image.Image, str]:
        """Inpaint using selected engine."""
        nonlocal router

        if image is None or mask is None:
            return None, "Image and mask required"

        try:
            # Initialize router if needed
            if router is None:
                router = DualEngineRouter(
                    InpaintEngineConfig(
                        engine=InpaintEngine.LAMA,
                        device="cuda",
                    ),
                    memory_manager=memory_manager,
                )

            # Update config based on UI selection
            target_engine = InpaintEngine.LAMA if "LaMa" in engine else InpaintEngine.FLUX
            router.config.engine = target_engine
            router.config.lama_tile_size = lama_tile_size
            router.config.lama_overlap = lama_overlap
            router.config.flux_guidance_scale = flux_guidance
            router.config.flux_num_steps = flux_steps
            router.config.flux_enable_sequential_offload = flux_offload

            # If LaMa config changed, recreate the instance to use new tile settings
            if router.lama and (
                router.lama.tile_size != lama_tile_size or router.lama.overlap != lama_overlap
            ):
                router.lama.cleanup()
                router.lama = None

            # Convert PIL to numpy
            image_np = np.array(image, dtype=np.uint8)
            mask_np = np.array(mask, dtype=np.uint8)

            # Run inpainting
            result_np = router.inpaint(image_np, mask_np)

            # Convert back to PIL
            result_pil = Image.fromarray(result_np, "RGB")

            status = f"Inpainting complete with {engine}"
            torch.cuda.synchronize() if __import__("importlib").util.find_spec("torch") else None

            return result_pil, status

        except Exception as e:
            return None, f"Inpainting failed: {e}"

    # Build UI
    with gr.Blocks(title="Watermark Removal - RTX 4090 Dual-Engine") as demo:
        gr.Markdown("# 🎬 Watermark Removal System (RTX 4090 Optimized)")
        gr.Markdown(
            "**Dual-engine watermark removal**: Choose **LaMa for speed** or **Flux for quality**"
        )

        with gr.Row():
            with gr.Column(scale=1):
                gr.Markdown("### Input & Detection")
                image_input = gr.Image(type="pil", label="Upload image")

                with gr.Group(label="Watermark Detection"):
                    auto_detect_cb = gr.Checkbox(
                        label="Auto-detect watermarks (Florence-2)",
                        value=False,
                        info="Adds ~2-3s, optional",
                    )
                    confidence_sl = gr.Slider(
                        minimum=0.3,
                        maximum=0.9,
                        step=0.05,
                        value=0.5,
                        label="Detection confidence",
                    )
                    detect_btn = gr.Button("Detect Watermarks", variant="secondary")

                mask_viewer = gr.Image(type="pil", label="Detected mask (editable)", interactive=False)
                status_detect = gr.Textbox(label="Status", interactive=False)

            with gr.Column(scale=1):
                gr.Markdown("### Inpainting Engine")

                with gr.Group(label="Engine Selection"):
                    engine_radio = gr.Radio(
                        choices=["LaMa (Fast ⚡)", "Flux.1-Fill (Quality ✨)"],
                        value="LaMa (Fast ⚡)",
                        label="Choose engine",
                    )

                # LaMa params
                with gr.Group(label="LaMa Parameters", visible=True) as lama_group:
                    lama_tile_sl = gr.Slider(
                        256,
                        1024,
                        value=512,
                        step=64,
                        label="Tile size (for 4K+)",
                    )
                    lama_overlap_sl = gr.Slider(
                        16, 128, value=64, step=8, label="Overlap pixels"
                    )

                # Flux params
                with gr.Group(label="Flux Parameters", visible=False) as flux_group:
                    flux_guidance_sl = gr.Slider(
                        1,
                        10,
                        value=3.5,
                        step=0.1,
                        label="Guidance scale",
                        info="Higher = stronger watermark removal",
                    )
                    flux_steps_sl = gr.Slider(
                        10,
                        100,
                        value=50,
                        step=5,
                        label="Inference steps",
                        info="More = better quality, slower",
                    )
                    flux_offload_cb = gr.Checkbox(
                        label="Sequential offload (slower, less VRAM)",
                        value=False,
                        info="Use if OOM on model offload",
                    )

                # Toggle visibility
                def update_params(engine_choice):
                    is_lama = "LaMa" in engine_choice
                    return (
                        gr.Group(visible=is_lama),  # lama_group
                        gr.Group(visible=(not is_lama)),  # flux_group
                    )

                engine_radio.change(
                    update_params,
                    inputs=[engine_radio],
                    outputs=[lama_group, flux_group],
                )

                inpaint_btn = gr.Button("🎨 Inpaint", variant="primary", size="lg")

        with gr.Row():
            output_image = gr.Image(type="pil", label="Inpainted result")
            status_inpaint = gr.Textbox(label="Status", interactive=False)

        # Event handlers
        detect_btn.click(
            detect_watermarks,
            inputs=[image_input, auto_detect_cb, confidence_sl],
            outputs=[mask_viewer, status_detect],
            queue=False,  # CPU operation
        )

        inpaint_btn.click(
            inpaint_image,
            inputs=[
                image_input,
                mask_viewer,
                engine_radio,
                lama_tile_sl,
                lama_overlap_sl,
                flux_guidance_sl,
                flux_steps_sl,
                flux_offload_cb,
            ],
            outputs=[output_image, status_inpaint],
            concurrency_limit=1,  # Serialize GPU ops
        )

    return demo


if __name__ == "__main__":
    app = create_app()
    app.launch(
        server_name="127.0.0.1",
        server_port=7860,
        share=False,
        queue=True,
        max_size=50,
    )
