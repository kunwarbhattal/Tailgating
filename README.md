# Video Stream Processing with Gemini API

This project captures frames from an HTTP video stream at configurable intervals and analyzes them using Google's Gemini API.

## Setup

1. Install the required dependencies:
```bash
pip install -r requirements.txt
```

2. Configure the application:
   - Open `config.py`
   - Set your HTTP video URL
   - Set your Gemini API key
   - Adjust the capture interval as needed
   - Modify the LLM question if desired

## Usage

Run the application:
```bash
python main.py
```

The application will:
1. Connect to the HTTP video stream
2. Capture frames at the specified interval
3. Send each frame to Gemini API for analysis
4. Display the analysis results in the console

## Configuration

All customizable settings are in `config.py`:
- `VIDEO_URL`: Your HTTP video URL
- `CAPTURE_INTERVAL_SECONDS`: Time between frame captures
- `GEMINI_API_KEY`: Your Gemini API key
- `LLM_QUESTION`: The question to ask about each frame

## Requirements

- Python 3.7+
- OpenCV
- Gemini API access
- Valid HTTP video stream URL 