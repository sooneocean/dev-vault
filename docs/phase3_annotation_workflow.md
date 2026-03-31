# Phase 3: Annotation Workflow Guide

## Overview

The Phase 3 annotation system integrates with Label Studio to crowdsource watermark detection and enable active learning. This guide covers Label Studio setup, annotation project creation, integration with the streaming service, quality control workflows, and model retraining loops.

## Architecture

```
Streaming Service ──→ Frame Export ──→ Label Studio ──→ Annotators
                                           ↓
                                      COCO JSON/
                                      YOLO Format
                                           ↓
                                    Model Retraining
                                           ↓
                                    Deployment
```

## Label Studio Setup

### 1. Docker Deployment

File: `docker-compose.label-studio.yml`

```yaml
version: "3.9"

services:
  label-studio:
    image: heartexlabs/label-studio:latest
    container_name: label-studio

    ports:
      - "8080:8080"

    environment:
      - LABEL_STUDIO_LOCAL_FILES_SERVING_ENABLED=true
      - LABEL_STUDIO_LOCAL_FILES_DOCUMENT_ROOT=/label-studio/data/media

    volumes:
      - label_studio_data:/label-studio/data
      - ./data/media:/label-studio/data/media

    restart: unless-stopped

volumes:
  label_studio_data:
```

### 2. Start and Access

```bash
# Start Label Studio
docker-compose -f docker-compose.label-studio.yml up -d

# Access
# http://localhost:8080

# Initial setup
# - Create account
# - Create organization
# - Set up project (see step 3)
```

### 3. Create Annotation Project

```
Home → Create → New Project
├── Project Name: "Watermark Detection"
├── Data Import Type: Upload Files
│   └── Upload sample frames (PNG/JPG)
├── Labeling Interface: Choose Template
│   └── Select: Object Detection (Bounding Box)
├── Instructions
│   └── "Draw boxes around all watermarks visible in frame"
```

### 4. Configure Label Interface

Sample Label Studio XML for watermark detection:

```xml
<View>
  <Image name="image" value="$image"/>

  <View style="padding: 10px; border-radius: 5px; background-color: #f1f3f4;">
    <Header value="Watermark Detection Instructions:"/>
    <Text>
      <p>1. Draw bounding boxes around all watermarks</p>
      <p>2. Label each box with watermark type (logo, text, etc.)</p>
      <p>3. Mark confidence (high/medium/low)</p>
      <p>4. Flag if watermark partially visible</p>
    </Text>
  </View>

  <RectangleLabels name="label" toName="image">
    <Label value="logo" background="blue"/>
    <Label value="text" background="green"/>
    <Label value="channel_bug" background="red"/>
    <Label value="timestamp" background="yellow"/>
  </RectangleLabels>

  <Choices name="confidence" toName="image" choice="single">
    <Choice value="high"/>
    <Choice value="medium"/>
    <Choice value="low"/>
  </Choices>

  <Checkbox name="partial" toName="image">
    <CheckboxOption value="partially_visible"/>
  </Checkbox>
</View>
```

## Data Export and Format Conversion

### Exporting from Label Studio

```
Projects → Watermark Detection → Export
└── Choose Format: COCO JSON (recommended)
```

### Format 1: COCO JSON (Recommended)

Structure for YOLO training:

```json
{
  "info": {
    "description": "Watermark Detection Dataset",
    "version": "1.0",
    "year": 2026
  },
  "licenses": [{"id": 1, "name": "CC BY 4.0"}],
  "images": [
    {
      "id": 1,
      "file_name": "frame_0001.png",
      "height": 1080,
      "width": 1920,
      "date_captured": "2026-03-31T10:00:00"
    }
  ],
  "annotations": [
    {
      "id": 1001,
      "image_id": 1,
      "category_id": 1,
      "bbox": [100, 50, 200, 150],
      "area": 30000,
      "iscrowd": 0,
      "metadata": {
        "confidence": "high",
        "partially_visible": false
      }
    }
  ],
  "categories": [
    {"id": 1, "name": "logo", "supercategory": "watermark"},
    {"id": 2, "name": "text", "supercategory": "watermark"},
    {"id": 3, "name": "channel_bug", "supercategory": "watermark"}
  ]
}
```

**Advantages**:
- Standard format for YOLO training
- Rich metadata support
- Community tooling available

### Format 2: YOLO Darknet Format

Convert COCO JSON to YOLO format:

```python
import json
from pathlib import Path

def coco_to_yolo(coco_json_path: str, output_dir: Path):
    """Convert COCO JSON to YOLO format."""
    with open(coco_json_path) as f:
        coco = json.load(f)

    # Build image ID → file map
    id_to_file = {
        img["id"]: img["file_name"]
        for img in coco["images"]
    }

    # Build category ID → class name map
    id_to_class = {
        cat["id"]: cat["name"]
        for cat in coco["categories"]
    }

    # Group annotations by image
    image_annotations = {}
    for ann in coco["annotations"]:
        img_id = ann["image_id"]
        if img_id not in image_annotations:
            image_annotations[img_id] = []
        image_annotations[img_id].append(ann)

    # Generate YOLO files
    output_dir.mkdir(exist_ok=True)
    for img_id, annotations in image_annotations.items():
        filename = Path(id_to_file[img_id]).stem
        yolo_file = output_dir / f"{filename}.txt"

        lines = []
        for ann in annotations:
            bbox = ann["bbox"]  # [x, y, w, h]
            img_data = next(img for img in coco["images"] if img["id"] == img_id)

            # Normalize coordinates
            x_center = (bbox[0] + bbox[2]/2) / img_data["width"]
            y_center = (bbox[1] + bbox[3]/2) / img_data["height"]
            width = bbox[2] / img_data["width"]
            height = bbox[3] / img_data["height"]

            class_id = ann["category_id"] - 1  # 0-indexed
            lines.append(f"{class_id} {x_center:.4f} {y_center:.4f} {width:.4f} {height:.4f}")

        yolo_file.write_text("\n".join(lines))

# Usage
coco_to_yolo("export.json", Path("./yolo_annotations"))
```

## Integration with Streaming Service

### 1. Automatic Frame Export

Configuration: `config/annotation.yaml`

```yaml
annotation:
  enabled: true
  output_format: "coco_json"      # or "yolo"
  export_interval_frames: 10      # Export every 10 frames
  export_dir: /data/annotation_exports

  label_studio:
    api_url: http://label-studio:8080
    api_key: ${LABEL_STUDIO_API_KEY}
    project_id: 1
    auto_import: true            # Auto-import to Label Studio
```

### 2. Automatic Upload to Label Studio

```python
import requests
from pathlib import Path

class LabelStudioExporter:
    def __init__(self, api_url: str, api_key: str, project_id: int):
        self.api_url = api_url
        self.api_key = api_key
        self.project_id = project_id
        self.headers = {"Authorization": f"Token {api_key}"}

    def upload_frame(self, frame_path: Path):
        """Upload frame to Label Studio project."""
        with open(frame_path, "rb") as f:
            files = {"file": f}
            response = requests.post(
                f"{self.api_url}/api/projects/{self.project_id}/import",
                headers=self.headers,
                files=files
            )
        return response.status_code == 200

    def upload_batch(self, frame_dir: Path):
        """Upload batch of frames."""
        success = 0
        for frame_file in sorted(frame_dir.glob("*.png")):
            if self.upload_frame(frame_file):
                success += 1
        return success

# Usage in streaming service
exporter = LabelStudioExporter(
    api_url="http://label-studio:8080",
    api_key=os.environ["LABEL_STUDIO_API_KEY"],
    project_id=1
)

# In frame processing loop
if frame_id % export_interval == 0:
    exporter.upload_frame(frame_path)
```

## Quality Control Workflow

### 1. Inter-Annotator Agreement (IAA)

Multi-annotator validation:

```python
import json
from pathlib import Path

def compute_iaa(annotations_dir: Path) -> float:
    """Compute inter-annotator agreement (IoU-based)."""
    from scipy.spatial.distance import jaccard

    # Load all annotator versions
    annotators = {}
    for json_file in annotations_dir.glob("*.json"):
        annotator_id = json_file.stem
        with open(json_file) as f:
            annotators[annotator_id] = json.load(f)

    # Compare bboxes frame-by-frame
    total_iou = 0
    comparisons = 0

    for frame_id in annotators["annotator_1"]["annotations"]:
        bboxes_1 = annotators["annotator_1"]["annotations"][frame_id]
        bboxes_2 = annotators["annotator_2"]["annotations"][frame_id]

        # Match boxes and compute IoU
        for bbox_1 in bboxes_1:
            for bbox_2 in bboxes_2:
                iou = compute_iou(bbox_1, bbox_2)
                total_iou += iou
                comparisons += 1

    return total_iou / comparisons if comparisons > 0 else 0

def compute_iou(box1, box2) -> float:
    """Compute intersection over union."""
    x1 = max(box1[0], box2[0])
    y1 = max(box1[1], box2[1])
    x2 = min(box1[0] + box1[2], box2[0] + box2[2])
    y2 = min(box1[1] + box1[3], box2[1] + box2[3])

    if x2 < x1 or y2 < y1:
        return 0.0

    intersection = (x2 - x1) * (y2 - y1)
    union = (box1[2] * box1[3]) + (box2[2] * box2[3]) - intersection

    return intersection / union if union > 0 else 0
```

**Quality thresholds**:

- **IAA > 0.8** ✓ High quality, ready for training
- **0.6 < IAA ≤ 0.8** ⚠ Review disagreements
- **IAA ≤ 0.6** ✗ Needs more clarification or retraining

### 2. Review Workflow

1. **Assign reviewers**:
   - Label Studio → Project → Team → Add Reviewers

2. **Review disagreements**:
   - Filter frames with low IAA
   - Multiple annotators re-examine
   - Consensus labeling

3. **Quality metrics**:
   - Track accuracy per annotator
   - Identify difficult frames
   - Document edge cases

### 3. Consensus Labeling

For frames with IAA < 0.8, use consensus strategy:

```python
def consensus_bbox(bboxes: list) -> list:
    """Generate consensus bboxes from multiple annotations."""
    if not bboxes:
        return []

    # Average coordinates
    avg_x = sum(b[0] for b in bboxes) / len(bboxes)
    avg_y = sum(b[1] for b in bboxes) / len(bboxes)
    avg_w = sum(b[2] for b in bboxes) / len(bboxes)
    avg_h = sum(b[3] for b in bboxes) / len(bboxes)

    return [avg_x, avg_y, avg_w, avg_h]

# Apply to low-IAA frames
for frame_id, agreement in frame_iaa.items():
    if agreement < 0.8:
        bboxes_to_consensus = [
            annotations[frame_id]
            for annotations in all_annotators.values()
        ]
        consensus = consensus_bbox(bboxes_to_consensus)
        final_annotations[frame_id] = consensus
```

## Model Retraining Loop

### 1. Prepare Training Dataset

```python
import json
from pathlib import Path

def prepare_training_set(coco_json_path: str, output_dir: Path, split=(0.8, 0.1, 0.1)):
    """Split COCO dataset into train/val/test."""
    with open(coco_json_path) as f:
        coco = json.load(f)

    images = coco["images"]
    train_size = int(len(images) * split[0])
    val_size = int(len(images) * split[1])

    train_ids = {img["id"] for img in images[:train_size]}
    val_ids = {img["id"] for img in images[train_size:train_size + val_size]}
    test_ids = {img["id"] for img in images[train_size + val_size:]}

    # Create split datasets
    for split_name, split_ids in [("train", train_ids), ("val", val_ids), ("test", test_ids)]:
        split_coco = {
            "info": coco["info"],
            "licenses": coco["licenses"],
            "images": [img for img in coco["images"] if img["id"] in split_ids],
            "annotations": [ann for ann in coco["annotations"] if ann["image_id"] in split_ids],
            "categories": coco["categories"]
        }

        output_file = output_dir / f"{split_name}_annotations.json"
        with open(output_file, "w") as f:
            json.dump(split_coco, f, indent=2)

# Usage
prepare_training_set("export.json", Path("./datasets"))
```

### 2. YOLO Training

```bash
# Install YOLOv8
pip install ultralytics

# Train
python -m ultralytics yolo detect train \
  data=datasets/watermark_dataset.yaml \
  model=yolov8m.pt \
  epochs=100 \
  imgsz=1920 \
  device=0
```

Dataset YAML: `datasets/watermark_dataset.yaml`

```yaml
# Watermark detection dataset

path: /path/to/datasets  # Dataset root
train: train_images      # Train images
val: val_images          # Val images
test: test_images        # Test images

nc: 3                    # Number of classes
names:                   # Class names
  0: logo
  1: text
  2: channel_bug
```

### 3. Evaluation and Deployment

```python
from ultralytics import YOLO

# Load trained model
model = YOLO("runs/detect/train/weights/best.pt")

# Evaluate
metrics = model.val()
print(f"mAP50: {metrics.box.map50:.3f}")
print(f"mAP50-95: {metrics.box.map:.3f}")

# If metrics > threshold, deploy
if metrics.box.map > 0.7:
    model.export(format="onnx")  # Export for production
```

## Active Learning Loop

### 1. Identify Uncertain Predictions

```python
def get_uncertain_predictions(model, frames, uncertainty_threshold=0.5):
    """Identify frames with low-confidence predictions."""
    uncertain = []

    for frame_id, frame in enumerate(frames):
        results = model.predict(frame, conf=0.3)

        if results:
            confidences = [det.conf for det in results[0].boxes]
            if any(conf < uncertainty_threshold for conf in confidences):
                uncertain.append(frame_id)

    return uncertain

# Collect uncertain frames for annotation
uncertain_frames = get_uncertain_predictions(model, video_frames, 0.5)
# Export for human review in Label Studio
```

### 2. Human Annotation of Uncertain Frames

1. Export uncertain frames to Label Studio
2. Assign to annotators
3. Collect high-quality labels
4. Retrain model with new data

### 3. Continuous Improvement

Monitoring and feedback loop:

```python
# Track model performance over time
metrics_history = []

for iteration in range(num_iterations):
    # 1. Identify uncertain predictions
    uncertain = get_uncertain_predictions(model, new_frames, 0.5)

    # 2. Export for annotation
    export_frames_to_label_studio(uncertain)

    # 3. Collect annotations (human process)
    # ... wait for annotators ...

    # 4. Download annotations
    coco_export = download_from_label_studio()

    # 5. Prepare training set
    prepare_training_set(coco_export, "datasets")

    # 6. Retrain
    model = YOLO("yolov8m.pt")
    results = model.train(
        data="datasets/watermark_dataset.yaml",
        epochs=50
    )

    # 7. Evaluate
    metrics = model.val()
    metrics_history.append(metrics.box.map)

    # 8. Check convergence
    if len(metrics_history) > 2:
        improvement = metrics_history[-1] - metrics_history[-2]
        if improvement < 0.01:
            print("Converged!")
            break

print(f"Final mAP: {metrics_history[-1]:.3f}")
```

## Best Practices

1. **Start with small sample**
   - Annotate 100-200 frames first
   - Validate quality before scaling

2. **Establish guidelines**
   - Document what constitutes watermark
   - Provide visual examples
   - Handle edge cases explicitly

3. **Multi-annotator validation**
   - Aim for IAA > 0.75
   - Review low-agreement frames
   - Track per-annotator quality

4. **Iterative improvement**
   - Collect harder examples over time
   - Retrain as annotated data grows
   - Monitor production performance

5. **Version control annotations**
   - Export datasets with metadata
   - Track COCO version, date, annotators
   - Archive previous versions

## Troubleshooting

### Issue: Slow annotation speed

**Solution**: Simplify interface
```xml
<!-- Remove metadata fields for speed -->
<RectangleLabels name="label" toName="image">
  <Label value="watermark" background="red"/>
</RectangleLabels>
```

### Issue: Low inter-annotator agreement

**Solution**: Clearer instructions
```
1. Watermark = any overlay, logo, or text
2. Exclude subtitles
3. Include partially visible marks
4. Flag if uncertain
```

### Issue: Model not improving

**Solution**: More diverse data
- Include different video sources
- Vary lighting and video quality
- Capture edge cases

## Further Reading

- Label Studio Docs: https://labelstud.io/guide
- YOLO Training: https://docs.ultralytics.com/tasks/detect
- COCO Dataset Format: https://cocodataset.org
