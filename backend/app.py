import os
import uuid
import torch
import boto3
import logging
from flask import Flask, request, jsonify
from torchvision import models, transforms
from PIL import Image
from datetime import datetime
from flask_cors import CORS

# Setup Flask & CORS
app = Flask(__name__)
CORS(app)

# Setup logging
logging.basicConfig(level=logging.INFO)

# Load AWS credentials
AWS_BUCKET = "defecscan-uploads"
AWS_REGION = "ap-south-1"
ACCESS_KEY = os.getenv("AWS_ACCESS_KEY_ID") or "YOUR_ACCESS_KEY"
SECRET_KEY = os.getenv("AWS_SECRET_ACCESS_KEY") or "YOUR_SECRET_KEY"

if ACCESS_KEY == "YOUR_ACCESS_KEY" or SECRET_KEY == "YOUR_SECRET_KEY":
    logging.warning("⚠️  Using fallback AWS credentials! Set environment variables ASAP.")

# Class mapping
class_names = {
    0: "algae",
    1: "major_crack",
    2: "minor_crack",
    3: "peeling",
    4: "spalling",
    5: "stain",
    6: "normal"
}

# Load model
logging.info("🔄 Loading model...")
model = models.resnet18()
model.fc = torch.nn.Linear(model.fc.in_features, len(class_names))
model.load_state_dict(torch.load("defecscan_model.pth", map_location=torch.device("cpu")))
model.eval()
logging.info("✅ Model loaded and ready")

# Image transform
transform = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor()
])

# Predict function
def predict_image(image_path):
    image = Image.open(image_path).convert('RGB')
    image = transform(image).unsqueeze(0)
    with torch.no_grad():
        outputs = model(image)
        _, predicted = torch.max(outputs, 1)
    return predicted.item()

# Upload to S3
def upload_to_s3(file_path, filename):
    s3 = boto3.client(
        's3',
        region_name=AWS_REGION,
        aws_access_key_id=ACCESS_KEY,
        aws_secret_access_key=SECRET_KEY
    )
    s3.upload_file(file_path, AWS_BUCKET, filename)
    return f"https://{AWS_BUCKET}.s3.{AWS_REGION}.amazonaws.com/{filename}"

# Store metadata in DynamoDB
def store_metadata_dynamodb(prediction, image_url):
    dynamodb = boto3.resource(
        'dynamodb',
        region_name=AWS_REGION,
        aws_access_key_id=ACCESS_KEY,
        aws_secret_access_key=SECRET_KEY
    )
    table = dynamodb.Table("DefecScanMeta")
    table.put_item(Item={
        'id': str(uuid.uuid4()),
        'timestamp': datetime.utcnow().isoformat(),
        'prediction': prediction,
        'image_url': image_url
    })

# Hello test route
@app.route("/hello")
def hello():
    return "✅ Flask server is running."

# Main prediction route
@app.route("/predict", methods=["POST"])
def predict():
    logging.info("📩 Received /predict request")

    if 'image' not in request.files:
        logging.warning("🚫 No image part in request")
        return jsonify({"error": "No image provided"}), 400

    image = request.files['image']
    logging.info(f"🖼️ Image received: {image.filename}")

    filename = f"{uuid.uuid4()}.jpg"
    image_path = os.path.join("uploads", filename)
    os.makedirs("uploads", exist_ok=True)
    image.save(image_path)
    logging.info(f"💾 Image saved to: {image_path}")

    try:
        pred_index = predict_image(image_path)
        prediction = class_names[pred_index]
        logging.info(f"🧠 Prediction: {prediction}")

        image_url = upload_to_s3(image_path, filename)
        logging.info(f"🌐 Image uploaded to S3: {image_url}")

        store_metadata_dynamodb(prediction, image_url)
        logging.info("📊 Metadata stored in DynamoDB")

        os.remove(image_path)

        return jsonify({
            "prediction": prediction,
            "image_url": image_url
        })

    except Exception as e:
        logging.error("❌ Exception occurred during processing", exc_info=True)
        return jsonify({"error": str(e)}), 500

# Run app
if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
