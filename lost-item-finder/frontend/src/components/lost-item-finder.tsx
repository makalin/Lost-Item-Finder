import React, { useState, useEffect } from 'react';
import { Camera, Upload, History, X } from 'lucide-react';
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

const LostItemFinder = () => {
  const [activeTab, setActiveTab] = useState('upload');
  const [targetObjects, setTargetObjects] = useState('');
  const [selectedFile, setSelectedFile] = useState(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [detections, setDetections] = useState([]);
  const [cameraActive, setCameraActive] = useState(false);
  const [error, setError] = useState(null);
  const [history, setHistory] = useState([]);
  const [confidenceData, setConfidenceData] = useState([]);

  useEffect(() => {
    if (activeTab === 'history') {
      fetchHistory();
    }
  }, [activeTab]);

  const fetchHistory = async () => {
    try {
      const response = await fetch('/history');
      const data = await response.json();
      setHistory(data.history);
      
      // Process data for confidence chart
      const chartData = data.history.reduce((acc, detection) => {
        const date = detection[1].split(' ')[0];
        const existingEntry = acc.find(entry => entry.date === date);
        if (existingEntry) {
          existingEntry.confidence = (existingEntry.confidence + detection[3]) / 2;
        } else {
          acc.push({ date, confidence: detection[3] });
        }
        return acc;
      }, []);
      setConfidenceData(chartData);
    } catch (err) {
      setError('Failed to fetch detection history');
    }
  };

  const handleFileChange = (event) => {
    setSelectedFile(event.target.files[0]);
    setError(null);
  };

  const handleSubmit = async (event) => {
    event.preventDefault();
    setIsProcessing(true);
    setError(null);

    const formData = new FormData();
    formData.append('video', selectedFile);
    formData.append('target_objects', targetObjects);

    try {
      const response = await fetch('/analyze', {
        method: 'POST',
        body: formData,
      });
      const data = await response.json();
      
      if (data.error) {
        throw new Error(data.error);
      }
      
      setDetections(data.detections);
    } catch (err) {
      setError(err.message || 'Failed to process video');
    } finally {
      setIsProcessing(false);
    }
  };

  const toggleCamera = async () => {
    try {
      if (!cameraActive) {
        await fetch('/start_camera');
        setCameraActive(true);
      } else {
        await fetch('/stop_camera');
        setCameraActive(false);
      }
    } catch (err) {
      setError('Failed to toggle camera');
    }
  };

  return (
    <div className="max-w-6xl mx-auto p-6">
      <Card>
        <CardHeader>
          <CardTitle className="text-2xl font-bold text-center">Lost Item Finder</CardTitle>
        </CardHeader>
        <CardContent>
          {/* Tab Navigation */}
          <div className="flex space-x-4 mb-6 border-b">
            {[
              { id: 'upload', icon: Upload, label: 'Video Upload' },
              { id: 'camera', icon: Camera, label: 'Live Camera' },
              { id: 'history', icon: History, label: 'Detection History' }
            ].map(({ id, icon: Icon, label }) => (
              <button
                key={id}
                onClick={() => setActiveTab(id)}
                className={`flex items-center space-x-2 px-4 py-2 border-b-2 transition-colors ${
                  activeTab === id ? 'border-blue-500 text-blue-500' : 'border-transparent'
                }`}
              >
                <Icon className="w-5 h-5" />
                <span>{label}</span>
              </button>
            ))}
          </div>

          {error && (
            <Alert variant="destructive" className="mb-6">
              <X className="w-4 h-4" />
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          )}

          {/* Tab Content */}
          <div className="space-y-6">
            {activeTab === 'upload' && (
              <form onSubmit={handleSubmit} className="space-y-4">
                <div>
                  <label className="block text-sm font-medium mb-1">Target Objects</label>
                  <input
                    type="text"
                    value={targetObjects}
                    onChange={(e) => setTargetObjects(e.target.value)}
                    placeholder="e.g., keys, wallet, phone"
                    className="w-full p-2 border rounded"
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium mb-1">Video File</label>
                  <input
                    type="file"
                    accept="video/*"
                    onChange={handleFileChange}
                    className="w-full p-2 border rounded"
                  />
                </div>

                <button
                  type="submit"
                  disabled={isProcessing || !selectedFile}
                  className={`w-full p-2 rounded text-white ${
                    isProcessing || !selectedFile ? 'bg-gray-400' : 'bg-blue-500 hover:bg-blue-600'
                  }`}
                >
                  {isProcessing ? 'Processing...' : 'Analyze Video'}
                </button>

                {detections.length > 0 && (
                  <div className="mt-6">
                    <h3 className="text-lg font-medium mb-2">Detections</h3>
                    <div className="space-y-2">
                      {detections.map((detection, index) => (
                        <div key={index} className="p-4 bg-gray-50 rounded">
                          <p className="font-medium">{detection.class_name}</p>
                          <p className="text-sm text-gray-600">
                            Confidence: {(detection.confidence * 100).toFixed(1)}%
                          </p>
                          <p className="text-sm text-gray-600">{detection.frame_location}</p>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </form>
            )}

            {activeTab === 'camera' && (
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium mb-1">Target Objects</label>
                  <input
                    type="text"
                    value={targetObjects}
                    onChange={(e) => setTargetObjects(e.target.value)}
                    placeholder="e.g., keys, wallet, phone"
                    className="w-full p-2 border rounded"
                  />
                </div>

                <button
                  onClick={toggleCamera}
                  className={`w-full p-2 rounded text-white ${
                    cameraActive ? 'bg-red-500 hover:bg-red-600' : 'bg-green-500 hover:bg-green-600'
                  }`}
                >
                  {cameraActive ? 'Stop Camera' : 'Start Camera'}
                </button>

                {cameraActive && (
                  <div className="mt-4">
                    <img
                      src={`/video_feed?objects=${encodeURIComponent(targetObjects)}`}
                      alt="Live camera feed"
                      className="w-full rounded"
                    />
                  </div>
                )}
              </div>
            )}

            {activeTab === 'history' && (
              <div className="space-y-6">
                <div className="h-64">
                  <ResponsiveContainer width="100%" height="100%">
                    <LineChart data={confidenceData}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="date" />
                      <YAxis domain={[0, 1]} />
                      <Tooltip />
                      <Line type="monotone" dataKey="confidence" stroke="#3b82f6" />
                    </LineChart>
                  </ResponsiveContainer>
                </div>

                <div className="space-y-2">
                  {history.map((detection, index) => (
                    <div key={index} className="p-4 bg-gray-50 rounded">
                      <p className="font-medium">{detection[2]}</p>
                      <p className="text-sm text-gray-600">
                        Confidence: {(detection[3] * 100).toFixed(1)}%
                      </p>
                      <p className="text-sm text-gray-600">{detection[1]}</p>
                      {detection[6] && (
                        <img
                          src={detection[6]}
                          alt="Detection"
                          className="mt-2 rounded max-h-40"
                        />
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default LostItemFinder;
