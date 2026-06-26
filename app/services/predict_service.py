import os
import io
import numpy as np
import tensorflow as tf
from PIL import Image

# Path to the TFLite model
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODEL_PATH = os.path.join(BASE_DIR, "model_ai", "model_sawit1_mobilenet.tflite")

# Global variables for caching the interpreter and input/output details
_interpreter = None
_input_details = None
_output_details = None

def get_interpreter():
    """Lazy load the TFLite interpreter and cache it for performance."""
    global _interpreter, _input_details, _output_details
    if _interpreter is None:
        if not os.path.exists(MODEL_PATH):
            raise FileNotFoundError(f"Model file not found at: {MODEL_PATH}")
        _interpreter = tf.lite.Interpreter(model_path=MODEL_PATH)
        _interpreter.allocate_tensors()
        _input_details = _interpreter.get_input_details()
        _output_details = _interpreter.get_output_details()
    return _interpreter, _input_details, _output_details

# The classes of our sawit classification model
CLASS_NAMES = ["Matang", "Mentah", "Terlalu Matang"]

def predict_sawit_image(image_bytes: bytes) -> tuple[str, str, str]:
    """
    Process image bytes, run inference on the TFLite model, and return:
    - tingkat_kematangan (str)
    - warna_dominan (str)
    - persentase (str, e.g., '95.4%')
    """
    interpreter, input_details, output_details = get_interpreter()

    # Load and process the image
    img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    # Resize to the model's required input size (160, 160)
    img_resized = img.resize((160, 160))
    img_array = np.array(img_resized, dtype=np.float32)
    img_array = np.expand_dims(img_array, axis=0)

    # Set input tensor and invoke
    interpreter.set_tensor(input_details[0]["index"], img_array)
    interpreter.invoke()

    # Get prediction output
    output = interpreter.get_tensor(output_details[0]["index"])[0]
    pred_idx = int(np.argmax(output))
    
    # Extract prediction results
    pred_class = CLASS_NAMES[pred_idx]
    confidence_val = float(output[pred_idx] * 100)
    persentase = f"{confidence_val:.1f}%"

    # Map classes to corresponding dominant colors
    color_map = {
        "Matang": "Oranye Kemerahan",
        "Terlalu Matang": "Cokelat Kehitaman",
        "Mentah": "Hijau"
    }
    warna_dominan = color_map.get(pred_class, "Oranye Kemerahan")

    return pred_class, warna_dominan, persentase
