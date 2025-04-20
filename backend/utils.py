import boto3
import uuid
from datetime import datetime
import pymysql
import os
from dotenv import load_dotenv
load_dotenv()

# AWS S3 Configuration
AWS_BUCKET = "defecscan-uploads"
AWS_REGION = "ap-south-1"
ACCESS_KEY = os.getenv("AWS_ACCESS_KEY_ID")
SECRET_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")

# Upload image to S3 and return public URL
def upload_to_s3(file_path, filename):
    s3 = boto3.client(
        's3',
        region_name=AWS_REGION,
        aws_access_key_id=ACCESS_KEY,
        aws_secret_access_key=SECRET_KEY
    )
    s3.upload_file(file_path, AWS_BUCKET, filename)
    return f"https://{AWS_BUCKET}.s3.{AWS_REGION}.amazonaws.com/{filename}"

# Store quick metadata in DynamoDB
def store_metadata_dynamodb(prediction, image_url):
    dynamodb = boto3.resource(
        'dynamodb',
        region_name=AWS_REGION,
        aws_access_key_id=ACCESS_KEY,
        aws_secret_access_key=SECRET_KEY
    )
    table = dynamodb.Table('DefecScanMetadata')
    image_id = str(uuid.uuid4())
    timestamp = datetime.utcnow().isoformat()

    table.put_item(Item={
        'image_id': image_id,
        'prediction': prediction,
        'timestamp': timestamp,
        'image_url': image_url
    })

    return image_id

# Store structured history in MySQL RDS
def insert_into_rds(user_email, prediction, image_url):
    conn = pymysql.connect(
        host="defecscan-db.c4l4qi86u89b.us-east-1.rds.amazonaws.com",  # Replace with your actual RDS endpoint
        user="admin",
        password="Defec123!",
        db="defecscan_db"
    )
    try:
        with conn.cursor() as cursor:
            sql = """
                INSERT INTO scan_history (user_email, prediction, image_url)
                VALUES (%s, %s, %s)
            """
            cursor.execute(sql, (user_email, prediction, image_url))
        conn.commit()
    finally:
        conn.close()
