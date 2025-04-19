import boto3
import uuid
from datetime import datetime
import pymysql

AWS_BUCKET = "defecscan-uploads"
AWS_REGION = "ap-south-1"
ACCESS_KEY = "your-access-key"
SECRET_KEY = "your-secret-key"

def upload_to_s3(file_path, filename):
    s3 = boto3.client('s3',
                      region_name=AWS_REGION,
                      aws_access_key_id=ACCESS_KEY,
                      aws_secret_access_key=SECRET_KEY)
    s3.upload_file(file_path, AWS_BUCKET, filename)
    return f"https://{AWS_BUCKET}.s3.{AWS_REGION}.amazonaws.com/{filename}"

def store_metadata_dynamodb(prediction, image_url):
    dynamodb = boto3.resource('dynamodb',
                               region_name=AWS_REGION,
                               aws_access_key_id=ACCESS_KEY,
                               aws_secret_access_key=SECRET_KEY)
    table = dynamodb.Table('DefecScanMetadata')
    image_id = str(uuid.uuid4())
    timestamp = datetime.utcnow().isoformat()
    table.put_item(Item={
        'image_id': image_id,
        'prediction': prediction,
        'timestamp': timestamp,
        'image_url': image_url
    })

def insert_into_rds(user_email, prediction, image_url):
    conn = pymysql.connect(
        host="your-db-endpoint",
        user="admin",
        password="Defec123!",
        db="defecscan_db"
    )
    try:
        with conn.cursor() as cursor:
            sql = "INSERT INTO scan_history (user_email, prediction, image_url) VALUES (%s, %s, %s)"
            cursor.execute(sql, (user_email, prediction, image_url))
        conn.commit()
    finally:
        conn.close()
