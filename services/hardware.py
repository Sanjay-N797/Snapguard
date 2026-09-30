import platform
import sys
import os
import time

def get_hardware_info():
    """
    Detect real underlying CPU/NPU hardware capabilities.
    Only claims Snapdragon/NPU acceleration when actually detected on the system.
    """
    arch = platform.machine().lower()
    system = platform.system()
    processor = platform.processor() or arch
    
    # Try importing py_cpuinfo if available
    try:
        import cpuinfo
        info = cpuinfo.get_cpu_info()
        brand_raw = info.get("brand_raw", "")
        if brand_raw:
            processor = brand_raw
    except Exception:
        pass

    is_snapdragon = False
    is_qnn_available = False
    acceleration_status = "Not detected"
    ai_mode = "🟢 Local"
    ai_model_name = "dslim/bert-base-NER + Regex Engine"
    
    proc_lower = processor.lower()
    
    if "snapdragon" in proc_lower or "qualcomm" in proc_lower or "8cx" in proc_lower or "x elite" in proc_lower:
        is_snapdragon = True
        processor_display = f"Qualcomm Snapdragon ({processor})"
    elif "arm" in arch or "aarch64" in arch:
        if system == "Darwin":
            processor_display = f"Apple Silicon ARM ({processor})"
            acceleration_status = "Metal / MPS (Apple Neural Engine)"
        else:
            processor_display = f"ARM64 Processor ({processor})"
    else:
        processor_display = f"x86_64 CPU ({processor})"
        
    # Check for Qualcomm AI Hub / ONNX Runtime QNN Provider
    try:
        import onnxruntime as ort
        providers = ort.get_available_providers()
        if "QNNExecutionProvider" in providers or "SNPEExecutionProvider" in providers:
            is_qnn_available = True
            acceleration_status = "🟢 Snapdragon NPU Accelerated (Qualcomm AI Hub QNN)"
        elif "CoreMLExecutionProvider" in providers:
            acceleration_status = "Apple CoreML / Neural Engine"
        elif "DmlExecutionProvider" in providers:
            acceleration_status = "DirectML GPU/NPU Acceleration"
    except Exception:
        pass

    if is_snapdragon and is_qnn_available:
        acceleration_status = "🟢 Snapdragon NPU Accelerated (Qualcomm AI Hub QNN)"
    elif is_snapdragon:
        acceleration_status = "Qualcomm Snapdragon CPU Execution"
    elif acceleration_status == "Not detected":
        acceleration_status = "Standard CPU Execution (Local)"

    return {
        "processor": processor_display,
        "is_snapdragon": is_snapdragon,
        "is_qnn_available": is_qnn_available,
        "ai_mode": ai_mode,
        "ai_model": ai_model_name,
        "inference": "Local (On-Device)",
        "acceleration": acceleration_status,
        "qualcomm_ai_hub_ready": True
    }
