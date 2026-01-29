from flask import Flask, render_template, Response , request, jsonify, send_from_directory
import numpy
import cv2 as cv
import base64
import os
import time

template_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../frontend'))
app = Flask(__name__, template_folder=template_dir)

def generate_frames():
    camera_index = 0
    while True:
        camera = cv.VideoCapture(camera_index)
        if not camera.isOpened():
            print(f"Error: Could not open camera with index {camera_index}, Trying next index...")
            camera_index += 1
            continue
        else:
            print(f"Successfully opened camera with index {camera_index}")
            break
    

    while True:
        success, frame = camera.read()
        if not success:
            print("Error: Could not read frame from camera")
        else:
            ret, buffer = cv.imencode('.jpg', frame)
            frame = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

    camera.release()

@app.route("/")
def index():
    # Serve the frontend file directly to avoid Jinja parsing JSX/JS syntax
    return send_from_directory(template_dir, 'index.html')


@app.route("/video_feed")
def video_feed():
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')


@app.route("/capture", methods=["POST"])
def capture(): 
    try:
        data = request.get_json()
        img_data = data['image']
        
        # Handle both formats: with and without data:image/png;base64, prefix
        if ',' in img_data:
            img_data = img_data.split(",")[1]
        
        img_bytes = base64.b64decode(img_data)
        nparr = numpy.frombuffer(img_bytes, numpy.uint8)
        img = cv.imdecode(nparr, cv.IMREAD_COLOR)
        
        if img is None:
            return jsonify({"status": "error", "message": "Failed to decode image"}), 400
        
        # Ensure images directory exists inside backend
        images_dir = os.path.join(os.path.dirname(__file__), 'images/saved')
        os.makedirs(images_dir, exist_ok=True)

        # Create timestamped filename
        filename = f"capture_{int(time.time())}.png"
        save_path = os.path.join(images_dir, filename)

        # Save image
        cv.imwrite(save_path, img)

        return jsonify({"status": "success", "message": "Image captured and saved.", "filename": filename})
    
    except Exception as e:
        print(f"Capture error: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500


if __name__ == "__main__":
    app.run(host='0.0.0.0', debug=True, port=5000, ssl_context="adhoc")