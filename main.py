import cv2
import time
import base64
import requests
import json
from config import RTSP_URL, CAPTURE_INTERVAL_SECONDS, GOOGLE_CLOUD_API_KEY, GOOGLE_CLOUD_PROJECT_ID, LLM_QUESTION

def capture_frame(cap):
    """Capture a single frame from the RTSP stream"""
    ret, frame = cap.read()
    if not ret:
        raise Exception("Failed to capture frame from RTSP stream")
    return frame

def save_frame(frame, filename="temp_frame.jpg"):
    """Save frame to a temporary file"""
    cv2.imwrite(filename, frame)
    return filename

def encode_image_to_base64(image_path):
    """Convert image to base64 string"""
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

def analyze_image_with_google_vision(image_base64):
    """Send image to Google Cloud Vision API"""
    url = f"https://vision.googleapis.com/v1/images:annotate?key={GOOGLE_CLOUD_API_KEY}"
    
    payload = {
        "requests": [
            {
                "image": {
                    "content": image_base64
                },
                "features": [
                    {
                        "type": "LABEL_DETECTION",
                        "maxResults": 10
                    },
                    {
                        "type": "OBJECT_LOCALIZATION",
                        "maxResults": 10
                    }
                ]
            }
        ]
    }
    
    headers = {
        "Content-Type": "application/json"
    }
    
    response = requests.post(url, json=payload, headers=headers)
    return response.json()

def process_vision_results(vision_results):
    """Process and format the vision API results"""
    if 'responses' not in vision_results or not vision_results['responses']:
        return "No objects detected"
    
    response = vision_results['responses'][0]
    results = []
    
    if 'labelAnnotations' in response:
        for label in response['labelAnnotations']:
            results.append(f"Label: {label['description']} (confidence: {label['score']:.2f})")
    
    if 'localizedObjectAnnotations' in response:
        for obj in response['localizedObjectAnnotations']:
            results.append(f"Object: {obj['name']} (confidence: {obj['score']:.2f})")
    
    return "\n".join(results)

def main():
    print("Starting RTSP stream processing...")
    
    # Initialize RTSP stream
    cap = cv2.VideoCapture(RTSP_URL)
    if not cap.isOpened():
        raise Exception("Failed to open RTSP stream")
    
    try:
        while True:
            # Capture frame
            frame = capture_frame(cap)
            
            # Save frame
            image_path = save_frame(frame)
            
            # Convert to base64
            image_base64 = encode_image_to_base64(image_path)
            
            # Analyze with Google Vision
            print("\nProcessing new frame...")
            vision_results = analyze_image_with_google_vision(image_base64)
            
            # Process and display results
            results = process_vision_results(vision_results)
            print("\nVision Analysis Results:")
            print(results)
            
            # Wait for the specified interval
            time.sleep(CAPTURE_INTERVAL_SECONDS)
            
    except KeyboardInterrupt:
        print("\nStopping stream processing...")
    finally:
        cap.release()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    main() 