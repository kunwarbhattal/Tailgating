import cv2
import numpy as np
from PIL import Image
from google.cloud import vision
import os
import safe
import time
from datetime import datetime

class MotionVisionAnalyzer:
    def __init__(self, rtsp_url, api_key_path, custom_question, 
                 frame_rate=30, motion_cooldown=5, api_cooldown=10, 
                 frame_sample_rate=3):
        """
        Initialize the analyzer with RTSP URL, Google Cloud credentials, and custom question
        
        Args:
            rtsp_url: RTSP stream URL
            api_key_path: Path to Google Cloud credentials
            custom_question: Custom question for analysis
            frame_rate: Target frame rate for processing (default: 30)
            motion_cooldown: Seconds to wait after motion detection before checking again (default: 5)
            api_cooldown: Seconds to wait between API calls (default: 10)
            frame_sample_rate: Process every Nth frame (default: 3)
        """
        self.rtsp_url = rtsp_url
        self.custom_question = custom_question
        self.previous_frame = None
        self.motion_threshold = 30  # Adjust this value to change motion sensitivity
        self.min_contour_area = 500  # Minimum area for motion detection
        
        # Optimization parameters
        self.frame_rate = frame_rate
        self.motion_cooldown = motion_cooldown
        self.api_cooldown = api_cooldown
        self.frame_sample_rate = frame_sample_rate
        
        # State tracking
        self.last_motion_time = 0
        self.last_api_call_time = 0
        self.frame_counter = 0
        
        # Set up Google Cloud Vision client
        os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = api_key_path
        self.vision_client = vision.ImageAnnotatorClient()
        
    def detect_motion(self, frame):
        """
        Detect motion in the current frame compared to the previous frame
        """
        if self.previous_frame is None:
            self.previous_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            return False
            
        current_gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        frame_diff = cv2.absdiff(current_gray, self.previous_frame)
        _, thresh = cv2.threshold(frame_diff, self.motion_threshold, 255, cv2.THRESH_BINARY)
        
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        motion_detected = False
        for contour in contours:
            if cv2.contourArea(contour) > self.min_contour_area:
                motion_detected = True
                break
                
        self.previous_frame = current_gray
        return motion_detected
    
    def analyze_image(self, image):
        """
        Send image to Google Cloud Vision API and get analysis
        """
        current_time = time.time()
        if current_time - self.last_api_call_time < self.api_cooldown:
            print(f"API call skipped - waiting {self.api_cooldown - (current_time - self.last_api_call_time):.1f} seconds")
            return None
            
        # Convert OpenCV image to bytes
        _, img_encoded = cv2.imencode('.jpg', image)
        content = img_encoded.tobytes()
        
        image = vision.Image(content=content)
        
        # Perform image analysis
        response = self.vision_client.annotate_image({
            'image': image,
            'features': [
                {'type_': vision.Feature.Type.OBJECT_LOCALIZATION},
                {'type_': vision.Feature.Type.LABEL_DETECTION},
                {'type_': vision.Feature.Type.TEXT_DETECTION}
            ]
        })
        
        self.last_api_call_time = current_time
        return response
    
    def process_video(self):
        """
        Main processing loop for the video feed
        """
        cap = cv2.VideoCapture(self.rtsp_url)
        
        if not cap.isOpened():
            print("Error: Cannot connect to RTSP stream")
            return
            
        print("Processing video feed... Press 'q' to quit")
        print(f"Frame rate: {self.frame_rate} FPS")
        print(f"Frame sampling: every {self.frame_sample_rate} frames")
        print(f"Motion cooldown: {self.motion_cooldown} seconds")
        print(f"API cooldown: {self.api_cooldown} seconds")
        
        # Calculate frame delay based on target frame rate
        frame_delay = 1.0 / self.frame_rate
        
        while True:
            ret, frame = cap.read()
            if not ret:
                print("Failed to grab frame")
                break
                
            self.frame_counter += 1
            
            # Skip frames based on sampling rate
            if self.frame_counter % self.frame_sample_rate != 0:
                continue
                
            current_time = time.time()
            
            # Check if we're in motion cooldown period
            if current_time - self.last_motion_time < self.motion_cooldown:
                cv2.imshow("Video Feed", frame)
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
                time.sleep(frame_delay)
                continue
                
            if self.detect_motion(frame):
                print("Motion detected!")
                self.last_motion_time = current_time
                
                # Save the frame
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"motion_{timestamp}.jpg"
                cv2.imwrite(filename, frame)
                
                # Analyze the image
                response = self.analyze_image(frame)
                
                if response:
                    # Print analysis results
                    print("\nAnalysis Results:")
                    print(f"Custom Question: {self.custom_question}")
                    
                    # Print detected objects
                    print("\nDetected Objects:")
                    for obj in response.localized_object_annotations:
                        print(f"- {obj.name} (confidence: {obj.score:.2f})")
                    
                    # Print labels
                    print("\nDetected Labels:")
                    for label in response.label_annotations:
                        print(f"- {label.description} (confidence: {label.score:.2f})")
                    
                    # Print text if any
                    if response.text_annotations:
                        print("\nDetected Text:")
                        print(response.text_annotations[0].description)
                    
                    print("\n" + "="*50 + "\n")
            
            # Display the frame
            cv2.imshow("Video Feed", frame)
            
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
                
            time.sleep(frame_delay)
                
        cap.release()
        cv2.destroyAllWindows()

def main():
    # Configuration - customize these values
    RTSP_URL = safe.RTSP_URL  # Replace with your RTSP URL
    API_KEY_PATH = safe.GOOGLE_API_KEY  # Replace with your credentials file path
    CUSTOM_QUESTION = safe.QUERY  # Replace with your custom question
    
    # Optimization parameters
    FRAME_RATE = 30  # Target frame rate
    MOTION_COOLDOWN = 5  # Seconds to wait after motion detection
    API_COOLDOWN = 10  # Seconds to wait between API calls
    FRAME_SAMPLE_RATE = 3  # Process every Nth frame
    
    analyzer = MotionVisionAnalyzer(
        RTSP_URL, 
        API_KEY_PATH, 
        CUSTOM_QUESTION,
        frame_rate=FRAME_RATE,
        motion_cooldown=MOTION_COOLDOWN,
        api_cooldown=API_COOLDOWN,
        frame_sample_rate=FRAME_SAMPLE_RATE
    )
    analyzer.process_video()

if __name__ == "__main__":
    main() 