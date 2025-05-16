import os, boto3
from flask import Flask, request
from werkzeug.middleware.dispatcher import DispatcherMiddleware
from prometheus_client import Counter
from flask_cors import CORS

# Import the new service modules
from storage.upload_service import UploadService
from storage.download_service import DownloadService
from storage.status_service import StatusService

server = Flask(__name__)
CORS(server)

unauth_count = Counter('unauthorized_requests_total', 'Total number of unauthorized requests')

# Initialize AWS clients for S3 and SQS using IAM roles
print("Initializing AWS clients...")
print(f"AWS Region: {os.environ.get('AWS_REGION')}")
print(f"S3 Video Bucket: {os.environ.get('S3_BUCKET_VIDEOS')}")
print(f"S3 MP3 Bucket: {os.environ.get('S3_BUCKET_MP3S')}")

# AWS services configuration
aws_region = os.environ.get("AWS_REGION", "eu-west-1")
s3_bucket_videos = os.environ.get("S3_BUCKET_VIDEOS", "your-video-buckets")
s3_bucket_mp3s = os.environ.get("S3_BUCKET_MP3S", "your-mp3-uckets")
sqs_queue_url = os.environ.get("SQS_VIDEO_QUEUE_URL", "https://sqs.eu-west-1.amazonaws.com/180294222815/your_sqs_url.fifo")

# Initialize AWS clients
s3_client = boto3.client("s3", region_name=aws_region)
sqs_client = boto3.client("sqs", region_name=aws_region)

# Initialize service objects
upload_service = UploadService(s3_client, s3_bucket_videos, sqs_client, sqs_queue_url)
download_service = DownloadService(s3_client, s3_bucket_mp3s)
status_service = StatusService(s3_client, s3_bucket_mp3s)

@server.route("/upload", methods=["POST"])
def upload():
    """Handle file upload requests"""
    return upload_service.handle_upload(request.files, request.form.get('user_data'))

@server.route("/check-audio/<video_key>", methods=["GET"])
def check_audio_status(video_key):
    """Check audio conversion status"""
    return status_service.check_audio_status(video_key)

@server.route("/download", methods=["GET"])
def download():
    """Handle file download requests"""
    file_id = request.args.get("fid")
    return download_service.handle_download(file_id)

if __name__ == "__main__":
    server.run(host="0.0.0.0", port=8080)
