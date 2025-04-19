from flask import Flask, request, jsonify
import os
from model_loader import WallDefectClassifier
from utils import upload_to_s3, store_metadata_dynamodb, insert_into_rds

UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

classifier = WallDefectClassifier(model_path='../ai_model/model.pt', labels=['crack', 'damp', 'peeling', 'no_defect'])

@app.route("/")
def home():
    return "DefecScan API Running"

@app.route("/detect", methods=['POST'])
def detect_defect():
    if 'image' not in request.files:
        return jsonify({"error": "No image uploaded"}), 400

    image = request.files['image']
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], image.filename)
    image.save(file_path)

    prediction = classifier.predict(file_path)
    url = upload_to_s3(file_path, image.filename)
    store_metadata_dynamodb(prediction, url)
    insert_into_rds("demo_user@defec.com", prediction, url)

    return jsonify({"prediction": prediction, "image_url": url})

if __name__ == '__main__':
    app.run(debug=True)
