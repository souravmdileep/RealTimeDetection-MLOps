import React, { useRef, useState, useEffect } from "react";
import { Link } from "react-router-dom";
import "./App.css";

function Home() {
  const videoRef = useRef(null);
  const canvasRef = useRef(null);
  const fileInputRef = useRef(null);
  
  const [model, setModel] = useState("v2"); 
  const [fps, setFps] = useState(0);
  const [isWebcamActive, setIsWebcamActive] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  
  const isLooping = useRef(false); 
  const currentStaticImage = useRef(null);
  const lastDetections = useRef([]); 
  const isProcessingFrame = useRef(false);

  // --- STANDARD MODEL SWITCHING ---
  const handleModelChange = async (e) => {
    const newModel = e.target.value;
    setIsProcessing(true);
    isLooping.current = false; 

    try {
      await fetch(`http://localhost:8000/switch_model?version=${newModel}`, { method: "POST" });
      setModel(newModel);
      lastDetections.current = [];
      if (!isWebcamActive && currentStaticImage.current) await sendFrameToBackend(currentStaticImage.current, true);
    } catch (err) { alert("Backend offline!"); } 
    finally {
      setIsProcessing(false);
      if (isWebcamActive) { isLooping.current = true; loopDetection(); }
    }
  };

  const startWebcam = async () => {
    if (isWebcamActive) return;
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ video: { width: 640, height: 480 } });
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
        videoRef.current.onloadedmetadata = () => {
            videoRef.current.play();
            setIsWebcamActive(true);
            isLooping.current = true;
            currentStaticImage.current = null;
            lastDetections.current = [];
            isProcessingFrame.current = false;
            loopDetection();
        };
      }
    } catch (err) { alert("Camera denied!"); }
  };

  const stopWebcam = () => {
    isLooping.current = false;
    setIsWebcamActive(false);
    setFps(0);
    lastDetections.current = [];
    if (videoRef.current && videoRef.current.srcObject) {
      videoRef.current.srcObject.getTracks().forEach(track => track.stop());
      videoRef.current.srcObject = null;
    }
  };

  const handleUploadClick = () => fileInputRef.current.click();
  const handleFileChange = (e) => {
    if (e.target.files && e.target.files[0]) {
      stopWebcam();
      const file = e.target.files[0];
      const imgUrl = URL.createObjectURL(file);
      currentStaticImage.current = imgUrl;
      const img = new Image();
      img.src = imgUrl;
      img.onload = () => {
        const canvas = canvasRef.current;
        const ctx = canvas.getContext("2d");
        const scale = Math.min(640 / img.width, 480 / img.height);
        canvas.width = img.width * scale;
        canvas.height = img.height * scale;
        ctx.drawImage(img, 0, 0, canvas.width, canvas.height);
        sendFrameToBackend(imgUrl, true);
      };
    }
  };

  const loopDetection = async () => {
    if (!isLooping.current || !videoRef.current || !canvasRef.current || isProcessing) return;
    if (isProcessingFrame.current) { setTimeout(loopDetection, 50); return; }
    
    const video = videoRef.current;
    const canvas = canvasRef.current;
    if (video.readyState === video.HAVE_ENOUGH_DATA) {
      canvas.width = video.videoWidth;
      canvas.height = video.videoHeight;
      const ctx = canvas.getContext("2d");
      ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
      if (lastDetections.current.length > 0) drawBoxes(lastDetections.current, ctx);
      canvas.toBlob((blob) => { if(!blob) return; sendBlob(blob); }, 'image/jpeg');
    } else { setTimeout(loopDetection, 100); }
  };

  const sendBlob = async (blob) => {
      isProcessingFrame.current = true;
      const formData = new FormData();
      formData.append("file", blob, "frame.jpg");
      const startTime = performance.now();
      try {
        const res = await fetch("http://localhost:8000/predict", { method: "POST", body: formData });
        if (res.status === 200) {
            const data = await res.json();
            setFps(Math.round(1000 / (performance.now() - startTime)));
            lastDetections.current = data.detections;
            const ctx = canvasRef.current.getContext("2d");
            drawBoxes(data.detections, ctx);
        }
      } catch (e) { } 
      finally {
        isProcessingFrame.current = false; 
        if (isLooping.current) loopDetection(); 
      }
  }

  const sendFrameToBackend = async (dataUrl, isStatic = false) => {
    try {
        const res = await fetch(dataUrl);
        const blob = await res.blob();
        const formData = new FormData();
        formData.append("file", blob, "frame.jpg");
        const resAPI = await fetch("http://localhost:8000/predict", { method: "POST", body: formData });
        const data = await resAPI.json();
        lastDetections.current = data.detections;
        if (isStatic) {
            const canvas = canvasRef.current;
            const ctx = canvas.getContext("2d");
            const img = new Image();
            img.src = dataUrl;
            img.onload = () => {
                ctx.drawImage(img, 0, 0, canvas.width, canvas.height);
                drawBoxes(data.detections, ctx);
            }
        }
    } catch (e) { console.error(e); }
  };

  const drawBoxes = (detections, ctx) => {
    if (!detections) return;
    const unique = [];
    const classesSeen = new Set();
    [...detections].sort((a,b) => b.score - a.score).forEach(d => {
        if(!classesSeen.has(d.class)) { unique.push(d); classesSeen.add(d.class); }
    });
    unique.forEach(det => {
      const [x, y, w, h] = det.box;
      ctx.strokeStyle = "#00f2ff";
      ctx.lineWidth = 3;
      ctx.strokeRect(x, y, w, h);
      ctx.fillStyle = "rgba(0, 0, 0, 0.7)";
      const text = `${det.class} ${Math.round(det.score * 100)}%`;
      const textWidth = ctx.measureText(text).width;
      ctx.fillRect(x, y > 25 ? y - 25 : 0, textWidth + 10, 25);
      ctx.fillStyle = "#fff";
      ctx.font = "bold 14px Inter";
      ctx.fillText(text, x + 5, y > 25 ? y - 7 : 17);
    });
  };

  return (
    <div className="App">
      <div className="header">
        <h1>General Object Detection</h1>
        <p>Standard Inference Mode (No Alerts)</p>
      </div>

      <div className="viewport">
        {isProcessing && <div className="processing-overlay"><div className="spinner"></div><p>Switching Brain...</p></div>}
        <div className="stats"><span>FPS: {fps}</span><span>|</span><span>Mode: {model.toUpperCase()}</span></div>
        <video ref={videoRef} style={{display: isWebcamActive ? 'block' : 'none'}} />
        <canvas ref={canvasRef} />
        {!isWebcamActive && !currentStaticImage.current && <div className="placeholder"><div className="placeholder-icon">📷</div><p>Start Camera or Upload Image</p></div>}
      </div>

      <div className="controls">
        <select value={model} onChange={handleModelChange} className="model-select" disabled={isProcessing}>
            <option value="v1">v1 (MobileNet)</option>
            <option value="v2">v2 (YOLOv8)</option>
        </select>
        {!isWebcamActive ? (
            <button className="btn btn-primary" onClick={startWebcam} disabled={isProcessing}><span>▶</span> Start Webcam</button>
        ) : (
            <button className="btn btn-secondary" onClick={stopWebcam}><span>⏹</span> Stop</button>
        )}
        <input type="file" accept="image/*" ref={fileInputRef} onChange={handleFileChange} className="file-input" />
        <button className="btn btn-secondary" onClick={handleUploadClick} disabled={isProcessing}><span>Tb</span> Upload</button>
        
        <Link to="/monitor" style={{textDecoration:'none'}}>
            <button className="btn btn-warning" style={{marginLeft:'20px'}}>
                🛡️ Secure Mode
            </button>
        </Link>
      </div>
    </div>
  );
}

export default Home;
