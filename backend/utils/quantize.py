import os
from onnxruntime.quantization import quantize_dynamic, QuantType

# Paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INPUT_MODEL = os.path.join(BASE_DIR, "models/v2/yolov8m.onnx")
OUTPUT_MODEL = os.path.join(BASE_DIR, "models/v2/yolov8m_int8.onnx")

def quantize():
    print(f"Optimizing model: {INPUT_MODEL}...")
    
    if not os.path.exists(INPUT_MODEL):
        print("Error: Input model not found!")
        return

    # Apply Dynamic Quantization (Float32 -> Int8)
    quantize_dynamic(
        model_input=INPUT_MODEL,
        model_output=OUTPUT_MODEL,
        weight_type=QuantType.QUInt8  # Convert weights to 8-bit unsigned integers
    )
    
    print(f"✅ Success! Optimized model saved to: {OUTPUT_MODEL}")
    
    # Compare sizes
    orig_size = os.path.getsize(INPUT_MODEL) / (1024 * 1024)
    new_size = os.path.getsize(OUTPUT_MODEL) / (1024 * 1024)
    print(f"Original Size: {orig_size:.2f} MB")
    print(f"Optimized Size: {new_size:.2f} MB")

if __name__ == "__main__":
    quantize()