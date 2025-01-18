from flask import Flask, render_template, request, jsonify, Response
import cv2
import numpy as np
from ultralytics import YOLO
import torch
import os
from datetime import datetime
import sqlite3
from pathlib import Path
import json
import threading
from queue import Queue

app = Flask(__name__)

class DetectionHistory:
    def __init__(self):
        self.db_path = 'detection_history.db'
        self.init_database()
    
    def init_database(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS detections (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT,
                    object_name TEXT,
                    confidence REAL,
                    location TEXT,
                    source TEXT,
                    image_path TEXT
                )
            ''')
    
    def add_detection(self, detection):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                INSERT INTO detections 
                (timestamp, object_name, confidence, location, source, image_path)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                detection['timestamp'],
                detection['class_name'],
                detection['confidence'],
                json.dumps(detection['bbox']),
                detection['source'],
                detection.get('image_path', '')
            ))
    
    def get_history(self, limit=100):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute('''
                SELECT * FROM detections 
                ORDER BY timestamp DESC 
                LIMIT ?
            ''', (limit,))
            return cursor.fetchall()

class ObjectTracker:
    def __init__(self):
        self.trackers = {}
        self.next_id = 0
        self.max_disappeared = 30  # Frames before considering object lost
        
    def update(self, objects):
        tracked_objects = {}
        
        # Update existing trackers with new detections
        for obj in objects:
            bbox = obj['bbox']
            center = ((bbox[0] + bbox[2]) / 2, (bbox[1] + bbox[3]) / 2)
            
            matched = False
            for track_id, tracker in self.trackers.items():
                if self._calculate_distance(center, tracker['center']) < 50:  # Distance threshold
                    tracker['center'] = center
                    tracker['bbox'] = bbox
                    tracker['disappeared'] = 0
                    tracker.update(obj)
                    tracked_objects[track_id] = tracker
                    matched = True
                    break
            
            if not matched:
                # Create new tracker
                self.trackers[self.next_id] = {
                    'center': center,
                    'bbox': bbox,
                    'disappeared': 0,
                    **obj
                }
                tracked_objects[self.next_id] = self.trackers[self.next_id]
                self.next_id += 1
        
        return tracked_objects
    
    def _calculate_distance(self, point1, point2):
        return np.sqrt((point1[0] - point2[0])**2 + (point1[1] - point2[1])**2)

class LostItemFinder:
    def __init__(self):
        self.model = YOLO('yolov8n.pt')
        self.confidence_threshold = 0.5
        self.history = DetectionHistory()
        self.tracker = ObjectTracker()
        self.camera_queue = Queue()
        self.is_camera_active = False
        
    def start_camera(self, camera_id=0):
        self.is_camera_active = True
        threading.Thread(target=self._camera_stream, args=(camera_id,), daemon=True).start()
    
    def stop_camera(self):
        self.is_camera_active = False
    
    def _camera_stream(self, camera_id):
        cap = cv2.VideoCapture(camera_id)
        while self.is_camera_active:
            ret, frame = cap.read()
            if ret:
                self.camera_queue.put(frame)
            else:
                break
        cap.release()
    
    def get_camera_frame(self):
        return self.camera_queue.get() if not self.camera_queue.empty() else None
    
    def process_frame(self, frame, target_objects=None):
        """
        Process a single frame to detect multiple objects
        """
        results = self.model(frame)
        detections = []
        
        for result in results:
            boxes = result.boxes
            for box in boxes:
                x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                confidence = box.conf.cpu().numpy()[0]
                class_id = box.cls.cpu().numpy()[0]
                class_name = self.model.names[int(class_id)]
                
                # Check if object matches any target objects
                if (target_objects is None or 
                    class_name.lower() in [obj.lower() for obj in target_objects]):
                    if confidence > self.confidence_threshold:
                        detection = {
                            'bbox': [int(x1), int(y1), int(x2), int(y2)],
                            'confidence': float(confidence),
                            'class_name': class_name,
                            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                            'frame_location': f"Frame center: ({int((x1+x2)/2)}, {int((y1+y2)/2)})"
                        }
                        detections.append(detection)
        
        # Update object tracking
        tracked_objects = self.tracker.update(detections)
        
        # Draw detections and tracking info
        self._draw_detections(frame, tracked_objects)
        
        return frame, tracked_objects
    
    def _draw_detections(self, frame, tracked_objects):
        for track_id, obj in tracked_objects.items():
            bbox = obj['bbox']
            
            # Draw bounding box
            cv2.rectangle(frame, (int(bbox[0]), int(bbox[1])), 
                         (int(bbox[2]), int(bbox[3])), (0, 255, 0), 2)
            
            # Draw label with tracking ID
            label = f"{obj['class_name']} ({track_id}): {obj['confidence']:.2f}"
            cv2.putText(frame, label, (int(bbox[0]), int(bbox[1])-10),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
            
            # Draw motion trail
            if 'trail' in obj:
                points = np.array(obj['trail'], dtype=np.int32)
                cv2.polylines(frame, [points], False, (255, 0, 0), 2)
    
    def analyze_video(self, video_path, target_objects):
        """
        Analyze video file for multiple target objects
        """
        detections = []
        cap = cv2.VideoCapture(video_path)
        frame_count = 0
        
        # Create output directory for detection images
        output_dir = Path('static/detections')
        output_dir.mkdir(exist_ok=True)
        
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break
            
            frame_count += 1
            if frame_count % 5 == 0:  # Process every 5th frame
                processed_frame, tracked_objects = self.process_frame(frame, target_objects)
                
                for obj in tracked_objects.values():
                    # Save frame with detection
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    image_path = output_dir / f"detection_{timestamp}_{obj['class_name']}.jpg"
                    cv2.imwrite(str(image_path), processed_frame)
                    
                    # Add to detection history
                    obj['source'] = 'video'
                    obj['image_path'] = str(image_path)
                    self.history.add_detection(obj)
                    detections.append(obj)
        
        cap.release()
        return detections

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/analyze', methods=['POST'])
def analyze():
    if 'video' not in request.files:
        return jsonify({'error': 'No video file provided'}), 400
    
    video = request.files['video']
    target_objects = request.form.get('target_objects', '').split(',')
    target_objects = [obj.strip() for obj in target_objects if obj.strip()]
    
    if not target_objects:
        return jsonify({'error': 'No target objects specified'}), 400
    
    video_path = f"temp_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4"
    video.save(video_path)
    
    try:
        detections = finder.analyze_video(video_path, target_objects)
        os.remove(video_path)
        
        return jsonify({
            'status': 'success',
            'detections': detections,
            'total_detections': len(detections)
        })
    
    except Exception as e:
        if os.path.exists(video_path):
            os.remove(video_path)
        return jsonify({'error': str(e)}), 500

@app.route('/start_camera')
def start_camera():
    finder.start_camera()
    return jsonify({'status': 'success'})

@app.route('/stop_camera')
def stop_camera():
    finder.stop_camera()
    return jsonify({'status': 'success'})

@app.route('/video_feed')
def video_feed():
    def generate_frames():
        target_objects = request.args.get('objects', '').split(',')
        target_objects = [obj.strip() for obj in target_objects if obj.strip()]
        
        while finder.is_camera_active:
            frame = finder.get_camera_frame()
            if frame is not None:
                processed_frame, tracked_objects = finder.process_frame(frame, target_objects)
                
                # Save significant detections to history
                for obj in tracked_objects.values():
                    if obj['confidence'] > 0.7:  # Higher threshold for camera feed
                        obj['source'] = 'camera'
                        finder.history.add_detection(obj)
                
                ret, buffer = cv2.imencode('.jpg', processed_frame)
                frame = buffer.tobytes()
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
    
    return Response(generate_frames(),
                   mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/history')
def get_history():
    limit = request.args.get('limit', 100, type=int)
    history = finder.history.get_history(limit)
    return jsonify({'history': history})

# Initialize finder
finder = LostItemFinder()

if __name__ == '__main__':
    app.run(debug=True)
