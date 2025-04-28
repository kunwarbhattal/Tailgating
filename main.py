import cv2
import time
import base64
import google.generativeai as genai
from config import VIDEO_URL, CAPTURE_INTERVAL_SECONDS, GEMINI_API_KEY, LLM_QUESTION

def capture_frame(cap):
    """Capture a single frame from the video stream"""
    ret, frame = cap.read()
    if not ret:
        raise Exception("Failed to capture frame from video stream")
    return frame

def save_frame(frame, filename="temp_frame.jpg"):
    """Save frame to a temporary file"""
    cv2.imwrite(filename, frame)
    return filename

def encode_image_to_base64(image_path):
    """Convert image to base64 string"""
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

def analyze_image_with_gemini(image_base64):
    """Send image to Gemini API for analysis"""
    # Configure the Gemini API
    genai.configure(api_key=GEMINI_API_KEY)
    
    # Create the model
    model = genai.GenerativeModel('gemini-pro-vision')
    
    # Prepare the image data
    image_data = {
        'mime_type': 'image/jpeg',
        'data': image_base64
    }
    
    # Generate content
    response = model.generate_content([LLM_QUESTION, image_data])
    return response.text

def main():
    print("Starting video stream processing...")
    
    # Initialize video stream
    cap = cv2.VideoCapture(VIDEO_URL)
    if not cap.isOpened():
        raise Exception("Failed to open video stream")
    
    try:
        while True:
            # Capture frame
            frame = capture_frame(cap)
            
            # Save frame
            image_path = save_frame(frame)
            
            # Convert to base64
            image_base64 = encode_image_to_base64(image_path)
            
            # Analyze with Gemini
            print("\nProcessing new frame...")
            analysis_results = analyze_image_with_gemini(image_base64)
            
            # Display results
            print("\nAnalysis Results:")
            print(analysis_results)
            
            # Wait for the specified interval
            time.sleep(CAPTURE_INTERVAL_SECONDS)
            
    except KeyboardInterrupt:
        print("\nStopping stream processing...")
    finally:
        cap.release()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    main() 