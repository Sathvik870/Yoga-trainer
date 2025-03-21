import streamlit as st
import cv2
import os
import av
import numpy as np
from streamlit_webrtc import webrtc_streamer, VideoProcessorBase, WebRtcMode
from datetime import datetime
from tempfile import NamedTemporaryFile

SNAPSHOT_DIR="snapshots"
# Ensure 'video_files' directory exists
VIDEO_DIR = "video_files"
os.makedirs(VIDEO_DIR, exist_ok=True)

# Video Processor for Live Camera with Recording
class VideoRecorder(VideoProcessorBase):
    def __init__(self):
        self.frames = []  # Stores frames for recording

    def recv(self, frame: av.VideoFrame):
        img = frame.to_ndarray(format="bgr24")  # Convert frame to numpy array

        # Store frame for saving video later
        self.frames.append(img)
        
        return av.VideoFrame.from_ndarray(img, format="bgr24")

    def save_video(self):
        if not self.frames:
            return None  # No frames recorded

        video_path = os.path.join(VIDEO_DIR, f"recorded_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4")

        height, width, _ = self.frames[0].shape
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')  
        out = cv2.VideoWriter(video_path, fourcc, 20.0, (width, height))

        for frame in self.frames:
            out.write(frame)

        out.release()
        print(f"Video saved at {video_path}")
        return video_path

def extract_frames(video_path, interval=5):
    cap = cv2.VideoCapture(video_path)
    
    if not cap.isOpened():
        st.error("Error: Could not open video.")
        return []

    fps = int(cap.get(cv2.CAP_PROP_FPS))  
    frame_interval = fps * interval  

    frame_count = 0
    snapshot_count = 0
    snapshots = []

    while True:
        ret, frame = cap.read()
        if not ret:
            break  

        if frame_count % frame_interval == 0:
            snapshot_path = os.path.join(SNAPSHOT_DIR, f"snapshot_{snapshot_count}.jpg")
            cv2.imwrite(snapshot_path, frame)  
            snapshots.append(snapshot_path)
            snapshot_count += 1

        frame_count += 1

    cap.release()
    return snapshots 

st.sidebar.title("Navigation")
page = st.sidebar.radio("Go to", ["Home", "Live Camera Recording", "Upload & Extract Snapshots"])

if page == "Home":
    st.title("🎥 Video Processing App")
    st.write("Use the sidebar to navigate between features.")

elif page == "Live Camera Recording":
    st.title("📷 Live Camera with Recording")

    # Initialize WebRTC Streamer with custom Video Processor
    ctx = webrtc_streamer(
        key="live_camera",
        mode=WebRtcMode.SENDRECV,
        video_processor_factory=VideoRecorder,
        media_stream_constraints={"video": True, "audio": False},
    )

    if ctx.video_processor:
        st.write("Recording in progress... Click 'Stop' to save the video.")
        if not ctx.state.playing:
            saved_video_path = ctx.video_processor.save_video()
            if saved_video_path:
                st.success(f"Video saved successfully: {saved_video_path}")
                st.video(saved_video_path)
                
elif page == "Upload & Extract Snapshots":
    st.title("📂 Upload a Video & Extract Snapshots")

    uploaded_video = st.file_uploader("Upload a Video File", type=["mp4", "avi", "mov"])

    if uploaded_video is not None:
        # Save uploaded file temporarily
        temp_video = NamedTemporaryFile(delete=False, suffix=".mp4")
        temp_video.write(uploaded_video.read())
        temp_video.close()

        st.video(temp_video.name)  

        if st.button("Extract Snapshots"):
            snapshots = extract_frames(temp_video.name, interval=5)

            if snapshots:
                st.write("Snapshots extracted successfully!")
                for snapshot in snapshots:
                    st.image(snapshot, caption="Snapshot", use_column_width=True)
            else:
                st.error("No snapshots extracted. Please try again.")
