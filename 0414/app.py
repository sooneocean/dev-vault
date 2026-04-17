import os
import gc
import cv2
import torch
import numpy as np
import gradio as gr
from PIL import Image
from transformers import AutoProcessor, AutoModelForCausalLM
from simple_lama_inpainting import SimpleLama

# ==========================================
# 資源管理器 (Resource Manager)
# 負責模型生命週期管理與顯存最佳化
# ==========================================
class ResourceManager:
    def __init__(self, device="cuda" if torch.cuda.is_available() else "cpu"):
        self.device = device
        self.detector_model = None
        self.detector_processor = None
        self.inpainter_model = None

    def load_detector(self):
        """載入 Florence-2 模型並移動至 GPU"""
        if self.detector_model is None:
            print("[INFO] 正在載入 Florence-2 偵測模型...")
            model_id = "microsoft/Florence-2-large"
            self.detector_processor = AutoProcessor.from_pretrained(model_id, trust_remote_code=True)
            self.detector_model = AutoModelForCausalLM.from_pretrained(
                model_id, 
                trust_remote_code=True, 
                torch_dtype=torch.float16 if self.device == "cuda" else torch.float32
            ).to(self.device)
            self.detector_model.eval()
        else:
            self.detector_model.to(self.device)

    def offload_detector(self):
        """將偵測模型卸載至 CPU 以釋放顯存"""
        if self.detector_model is not None:
            self.detector_model.to("cpu")
            self.clear_cache()

    def load_inpainter(self):
        """載入 LaMa 模型並移動至 GPU"""
        if self.inpainter_model is None:
            print("[INFO] 正在載入 LaMa 修補模型...")
            # SimpleLama 內部會處理模型下載與載入
            self.inpainter_model = SimpleLama()
        # SimpleLama 本身不直接支援 .to('cuda')，但內部實作會優先使用 cuda
        pass

    def offload_inpainter(self):
        """清理修補模組相關資源 (由於 SimpleLama 封裝限制，主要依賴 cache 清理)"""
        self.clear_cache()

    def clear_cache(self):
        """強制回收記憶體與清理 CUDA 緩存"""
        gc.collect()
        if self.device == "cuda":
            torch.cuda.empty_cache()

# ==========================================
# 智能偵測模組 (Watermark Detector)
# 使用 Florence-2 進行物件落地偵測
# ==========================================
class WatermarkDetector:
    def __init__(self, resource_manager):
        self.rm = resource_manager

    def detect(self, pil_image, prompt="watermark, text, logo"):
        self.rm.load_detector()
        
        task_prompt = "<CAPTION_TO_PHRASE_GROUNDING>"
        full_prompt = task_prompt + prompt
        
        inputs = self.rm.detector_processor(text=full_prompt, images=pil_image, return_tensors="pt").to(self.rm.device)
        if self.rm.device == "cuda":
            inputs = {k: v.to(torch.float16) if v.dtype == torch.float32 else v for k, v in inputs.items()}

        with torch.no_grad():
            generated_ids = self.rm.detector_model.generate(
                input_ids=inputs["input_ids"],
                pixel_values=inputs["pixel_values"],
                max_new_tokens=1024,
                early_stopping=False,
                do_sample=False,
                num_beams=3,
            )
        
        results = self.rm.detector_processor.batch_decode(generated_ids, skip_special_tokens=False)[0]
        parsed_answer = self.rm.detector_processor.post_process_generation(
            results, 
            task=task_prompt, 
            image_size=(pil_image.width, pil_image.height)
        )
        
        bboxes = []
        # 解析 Florence-2 輸出的座標格式
        if task_prompt in parsed_answer:
            data = parsed_answer[task_prompt]
            if 'bboxes' in data:
                bboxes = data['bboxes']
        
        self.rm.offload_detector()
        return bboxes

# ==========================================
# 遮罩工程模組 (Mask Processor)
# 形態學優化與平滑處理
# ==========================================
class MaskProcessor:
    @staticmethod
    def generate_mask_from_bboxes(width, height, bboxes, dilation_kernel=15):
        mask = np.zeros((height, width), dtype=np.uint8)
        for bbox in bboxes:
            x1, y1, x2, y2 = map(int, bbox)
            cv2.rectangle(mask, (x1, y1), (x2, y2), 255, -1)
        
        if dilation_kernel > 0:
            kernel = np.ones((dilation_kernel, dilation_kernel), np.uint8)
            mask = cv2.dilate(mask, kernel, iterations=1)
        
        # 軟遮罩平滑處理
        mask = cv2.GaussianBlur(mask, (21, 21), 0)
        return mask

# ==========================================
# LaMa 修補與分塊融合模組 (Inpainter)
# 實作 Tiling 與高斯加權融合
# ==========================================
class SeamlessInpainter:
    def __init__(self, resource_manager):
        self.rm = resource_manager

    def _get_gaussian_mask(self, size):
        """產生 2D 高斯權重矩陣"""
        mask = np.zeros((size, size))
        sigma = size / 4
        center = size // 2
        for i in range(size):
            for j in range(size):
                dist_sq = (i - center)**2 + (j - center)**2
                mask[i, j] = np.exp(-dist_sq / (2 * sigma**2))
        return mask

    def process(self, image_np, mask_np, patch_size=512, stride=256):
        self.rm.load_inpainter()
        h, w, _ = image_np.shape
        
        # 填充影像至步長的倍數以利切割
        pad_h = (stride - h % stride) % stride
        pad_w = (stride - w % stride) % stride
        # 確保填充後至少大於 patch_size
        if h + pad_h < patch_size: pad_h += patch_size - (h + pad_h)
        if w + pad_w < patch_size: pad_w += patch_size - (w + pad_w)
        
        img_padded = np.pad(image_np, ((0, pad_h), (0, pad_w), (0, 0)), mode='reflect')
        mask_padded = np.pad(mask_np, ((0, pad_h), (0, pad_w)), mode='reflect')
        
        new_h, new_w = img_padded.shape[:2]
        accumulator = np.zeros((new_h, new_w, 3), dtype=np.float32)
        weight_map = np.zeros((new_h, new_w), dtype=np.float32)
        
        g_mask = self._get_gaussian_mask(patch_size)
        
        # 分塊處理邏輯
        for y in range(0, new_h - patch_size + 1, stride):
            for x in range(0, new_w - patch_size + 1, stride):
                img_patch = img_padded[y:y+patch_size, x:x+patch_size]
                mask_patch = mask_padded[y:y+patch_size, x:x+patch_size]
                
                # 如果該圖塊沒有需要修補的部分，直接使用原圖跳過推論以節省時間
                if np.max(mask_patch) < 10:
                    patch_result = img_patch.astype(np.float32)
                else:
                    pil_patch = Image.fromarray(img_patch)
                    pil_mask = Image.fromarray(mask_patch)
                    # LaMa 推論
                    with torch.no_grad():
                        # SimpleLama 內部已處理 autocast 或相關最佳化
                        patch_result = self.rm.inpainter_model(pil_patch, pil_mask)
                        patch_result = np.array(patch_result).astype(np.float32)
                
                # 加權累加
                for c in range(3):
                    accumulator[y:y+patch_size, x:x+patch_size, c] += patch_result[:, :, c] * g_mask
                weight_map[y:y+patch_size, x:x+patch_size] += g_mask
        
        # 正規化權重
        weight_map = np.expand_dims(weight_map, axis=-1)
        final_img = accumulator / (weight_map + 1e-8)
        final_img = np.clip(final_img, 0, 255).astype(np.uint8)
        
        # 裁切回原始大小
        result = final_img[:h, :w]
        
        self.rm.offload_inpainter()
        return result

# ==========================================
# Gradio 應用程式整合
# ==========================================
class WatermarkApp:
    def __init__(self):
        self.rm = ResourceManager()
        self.detector = WatermarkDetector(self.rm)
        self.mask_proc = MaskProcessor()
        self.inpainter = SeamlessInpainter(self.rm)

    def auto_process(self, input_img, prompt, dilation):
        if input_img is None: return None, None
        
        pil_img = Image.fromarray(input_img).convert("RGB")
        
        # 1. 偵測
        bboxes = self.detector.detect(pil_img, prompt)
        
        # 2. 生成遮罩
        mask = self.mask_proc.generate_mask_from_bboxes(
            pil_img.width, pil_img.height, bboxes, dilation
        )
        
        # 3. 修補 (Tiling)
        result_np = self.inpainter.process(input_img, mask)
        
        return result_np, mask

    def manual_process(self, dict_data, dilation):
        # Gradio Image Editor 傳回的是一個字典，包含 'background' 和 'layers'
        if dict_data is None: return None
        
        background = dict_data['background'] # PIL Image
        # 合併所有繪製層產生的遮罩
        layers = dict_data['layers']
        if not layers: return background
        
        # 將繪製層轉換為單一遮罩
        full_mask = np.zeros((background.height, background.width), dtype=np.uint8)
        for layer in layers:
            layer_np = np.array(layer.convert("L"))
            full_mask = cv2.bitwise_or(full_mask, layer_np)
        
        # 遮罩優化
        if dilation > 0:
            kernel = np.ones((dilation, dilation), np.uint8)
            full_mask = cv2.dilate(full_mask, kernel, iterations=1)
        full_mask = cv2.GaussianBlur(full_mask, (21, 21), 0)
        
        # 修補
        bg_np = np.array(background.convert("RGB"))
        result_np = self.inpainter.process(bg_np, full_mask)
        
        return result_np

    def launch(self):
        with gr.Blocks(title="工業級自動去浮水印系統") as demo:
            gr.Markdown("# 🚀 高解析度自動去浮水印系統\n基於 Florence-2 偵測與 LaMa 分塊修補技術")
            
            with gr.Tabs():
                # 分頁 1: 全自動模式
                with gr.TabItem("✨ 全自動模式"):
                    with gr.Row():
                        with gr.Column():
                            auto_input = gr.Image(label="輸入圖片", type="numpy")
                            auto_prompt = gr.Textbox(label="偵測標籤 (逗號分隔)", value="watermark, text, logo")
                            auto_dilation = gr.Slider(label="遮罩擴張大小", minimum=0, maximum=50, value=15, step=1)
                            auto_btn = gr.Button("開始處理", variant="primary")
                        with gr.Column():
                            auto_output = gr.Image(label="處理結果")
                            auto_mask_out = gr.Image(label="生成的遮罩 (預覽)")
                    
                    auto_btn.click(
                        self.auto_process, 
                        inputs=[auto_input, auto_prompt, auto_dilation], 
                        outputs=[auto_output, auto_mask_out]
                    )

                # 分頁 2: 手動遮罩模式
                with gr.TabItem("🖌️ 手動修補模式"):
                    with gr.Row():
                        with gr.Column():
                            manual_input = gr.ImageMask(label="在上圖塗抹浮水印區域", type="pil")
                            manual_dilation = gr.Slider(label="遮罩擴張大小", minimum=0, maximum=50, value=5, step=1)
                            manual_btn = gr.Button("開始修補", variant="primary")
                        with gr.Column():
                            manual_output = gr.Image(label="處理結果")
                    
                    manual_btn.click(
                        self.manual_process,
                        inputs=[manual_input, manual_dilation],
                        outputs=manual_output
                    )

            gr.Markdown("---")
            gr.Markdown("💡 **技術提示：** 本系統針對 8GB VRAM 進行優化，支援 4K 超大圖分塊處理。")
            
        demo.launch(share=False)

if __name__ == "__main__":
    app = WatermarkApp()
    app.launch()
