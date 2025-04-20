@app.route("/detect", methods=['POST'])
def detect_defect():
    if 'image' not in request.files:
        return jsonify({"error": "No image uploaded"}), 400

    # Get the uploaded image
    image = request.files['image']
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], image.filename)
    image.save(file_path)

    # Run AI prediction
    prediction = classifier.predict(file_path)

    # Upload image to S3
    url = upload_to_s3(file_path, image.filename)

    # Get user email dynamically from the form
    user_email = request.form.get('user_email', 'anonymous@defecscan.com')

    # Store in DynamoDB and RDS
    store_metadata_dynamodb(prediction, url)
    insert_into_rds(user_email, prediction, url)

    # Return result
    return jsonify({
        "user_email": user_email,
        "prediction": prediction,
        "image_url": url
    })
