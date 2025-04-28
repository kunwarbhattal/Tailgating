import cv2
import time
import base64
import google.generativeai as genai
from config import VIDEO_URL, CAPTURE_INTERVAL_SECONDS, GEMINI_API_KEY, LLM_QUESTION
import os
import json

# Path to user config file
USER_CONFIG_PATH = "user_config.json"

def get_config_value(var_name, prompt, default=None, is_int=False):
    # Try to load from user_config.json
    config = {}
    if os.path.exists(USER_CONFIG_PATH):
        with open(USER_CONFIG_PATH, "r") as f:
            config = json.load(f)
    # Try to import from config.py
    try:
        from config import VIDEO_URL, CAPTURE_INTERVAL_SECONDS, GEMINI_API_KEY, LLM_QUESTION
        value = globals().get(var_name)
        if value is not None and value != "":
            config[var_name] = value
    except Exception:
        pass
    # If not present or invalid, prompt user
    if var_name not in config or config[var_name] in [None, ""]:
        user_input = input(f"{prompt} " + (f"[default: {default}]: " if default else ": "))
        if user_input == "" and default is not None:
            user_input = default
        if is_int:
            user_input = int(user_input)
        config[var_name] = user_input
        # Save to file
        with open(USER_CONFIG_PATH, "w") as f:
            json.dump(config, f)
    return config[var_name]

# Get config values (prompt if missing)
VIDEO_URL = get_config_value("VIDEO_URL", "Enter video URL or device index (e.g. 0 for webcam):")
CAPTURE_INTERVAL_SECONDS = int(get_config_value("CAPTURE_INTERVAL_SECONDS", "Enter capture interval in seconds:", default="5", is_int=True))
GEMINI_API_KEY = get_config_value("GEMINI_API_KEY", "Enter your Gemini API key:")
LLM_QUESTION = get_config_value("LLM_QUESTION", "Enter the LLM question to ask about the image:")

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
    model = genai.GenerativeModel('gemini-1.5-flash')
    
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
            ret, frame = cap.read()
            if not ret:
                print("Failed to capture frame from video stream")
                break

            # Show the frame in a window
            cv2.imshow("Video Feed (Press 's' to analyze, 'q' to quit)", frame)

            # Wait for key press for 1ms
            key = cv2.waitKey(1) & 0xFF

            if key == ord('s'):
                # Save frame
                image_path = save_frame(frame)

                # Convert to base64
                image_base64 = encode_image_to_base64(image_path)

                # Analyze with Gemini
                print("\nProcessing current frame...")
                analysis_results = analyze_image_with_gemini(image_base64)

                # Display results
                print("\nAnalysis Results:")
                print(analysis_results)

            elif key == ord('q'):
                print("\nStopping stream processing...")
                break

    finally:
        cap.release()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    main() 