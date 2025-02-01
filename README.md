# Lost Item Finder

Lost Item Finder is a real-time object detection system that helps users locate misplaced items using computer vision and deep learning. The application supports both video file analysis and live camera feed monitoring to track and find objects of interest.

## Features

- **Multi-mode Detection**
  - Video file upload and analysis
  - Real-time camera monitoring
  - Historical detection tracking

- **Smart Object Detection**
  - Powered by YOLOv8 object detection model
  - Real-time object tracking
  - Confidence-based filtering
  - Motion trail visualization

- **Interactive Web Interface**
  - User-friendly dashboard
  - Real-time detection visualization
  - Historical detection review
  - Confidence trend analysis
  - Responsive design with Tailwind CSS

## Technical Stack

- **Frontend**
  - React
  - Tailwind CSS
  - Recharts for data visualization
  - Lucide icons
  - ShadCN UI components

- **Backend**
  - Flask
  - OpenCV
  - YOLOv8
  - SQLite
  - Threading for concurrent processing

## Installation

1. Clone the repository:
```bash
git clone https://github.com/makalin/Lost-Item-Finder.git
cd Lost-Item-Finder
```

2. Install Python dependencies:
```bash
pip install flask opencv-python ultralytics torch numpy
```

3. Install Node.js dependencies:
```bash
cd frontend
npm install
```

4. Set up the database:
```bash
# The database will be automatically initialized when running the application
```

## Usage

1. Start the Flask backend:
```bash
python lost-item-finder.py
```

2. Start the React frontend:
```bash
cd frontend
npm start
```

3. Access the application at `http://localhost:3000`

## Using the Application

1. **Video Upload Mode**
   - Enter target objects (e.g., "keys, wallet, phone")
   - Upload a video file
   - Click "Analyze Video" to process
   - View detected items and their locations

2. **Live Camera Mode**
   - Enter target objects
   - Click "Start Camera" to begin monitoring
   - Real-time detections will be displayed
   - Click "Stop Camera" to end monitoring

3. **History Mode**
   - View past detections
   - Analyze detection confidence trends
   - Review detection screenshots

## Development

### Project Structure

```
lost-item-finder/
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   └── lost-item-finder.tsx
│   │   └── ...
├── backend/
│   ├── lost-item-finder.py
│   └── detection_history.db
└── ...
```

### Key Components

- `LostItemFinder` class: Core detection and tracking logic
- `ObjectTracker` class: Manages object tracking and persistence
- `DetectionHistory` class: Handles detection storage and retrieval
- React frontend: Manages UI and user interactions

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- YOLOv8 for object detection
- OpenCV for image processing
- Flask for backend services
- React and Tailwind CSS for frontend implementation
