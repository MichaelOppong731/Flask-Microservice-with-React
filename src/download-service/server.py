import os, boto3
from flask import Flask, request, jsonify, send_file
from werkzeug.middleware.dispatcher import DispatcherMiddleware
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
from flask_cors import CORS
from io import BytesIO
import logging
from botocore.exceptions import ClientError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize Flask application
server = Flask(__name__)
CORS(server)

# Prometheus metrics for monitoring
download_count = Counter('download_requests_total', 'Total number of download requests')
status_count = Counter('status_requests_total', 'Total number of status check requests')
error_count = Counter('download_service_errors_total', 'Total number of errors in download service')
download_duration = Histogram('download_duration_seconds', 'Time spent processing downloads')
file_size = Histogram('download_file_size_bytes', 'Size of downloaded files')

# Add metrics endpoint
@server.route('/metrics')
def metrics():
    return generate_latest(), 200, {'Content-Type': CONTENT_TYPE_LATEST}

# Load configuration from environment variables
print("\n=== Download Service Starting ===")
print("Initializing AWS clients for Download Service...")

# AWS configuration from environment variables
aws_region = os.environ["AWS_REGION"]
s3_bucket_mp3s = os.environ["S3_BUCKET_MP3S"]

print(f"AWS Region: {aws_region}")
print(f"S3 MP3 Bucket: {s3_bucket_mp3s}")

# Initialize AWS clients
s3_client = boto3.client("s3", region_name=aws_region)

print("✅ AWS client initialized successfully\n")

class DownloadService:
    """
    Service class to handle MP3 file downloads from S3
    """
    def __init__(self, s3_client, s3_bucket):
        self.s3_client = s3_client
        self.s3_bucket = s3_bucket
    
    def validate_request(self, file_id):
        print(f"\n🔍 Validating download request for file: {file_id}")
        if not file_id:
            print("❌ Missing file ID")
            error_count.inc()
            return False, ("fid is required", 400)
        print("✅ File ID validated")
        return True, None
    
    def download_file(self, file_id):
        print(f"\n📥 Downloading file: {file_id}")
        try:
            print(f"Fetching from bucket: {self.s3_bucket}")
            with download_duration.time():
                s3_object = self.s3_client.get_object(Bucket=self.s3_bucket, Key=file_id)
                file_stream = BytesIO(s3_object['Body'].read())
                file_size.observe(s3_object['ContentLength'])
            print("✅ File downloaded successfully")
            return send_file(file_stream, download_name=f"{file_id}")
        except Exception as err:
            print(f"❌ Download Error: {err}")
            error_count.inc()
            return "internal server error", 500
    
    def handle_download(self, file_id):
        print("\n=== New Download Request ===")
        download_count.inc()
        
        valid, error = self.validate_request(file_id)
        if not valid:
            error_count.inc()
            return error
        
        return self.download_file(file_id)

class StatusService:
    """
    Service class to check audio conversion status
    """
    def __init__(self, s3_client, s3_bucket):
        self.s3_client = s3_client
        self.s3_bucket = s3_bucket
    
    def check_audio_status(self, video_key):
        print(f"\n=== Checking Status for {video_key} ===")
        status_count.inc()
        audio_key = f"{video_key}.mp3"
        
        try:
            print(f"Checking if {audio_key} exists in bucket: {self.s3_bucket}")
            self.s3_client.head_object(Bucket=self.s3_bucket, Key=audio_key)
            print("✅ Audio file found - conversion complete")
            return jsonify({
                "status": "completed",
                "audio_key": audio_key
            }), 200
        except Exception as err:
            print(f"❌ Audio file not found - still processing: {err}")
            return jsonify({"status": "processing"}), 202

# Initialize services
download_service = DownloadService(s3_client, s3_bucket_mp3s)
status_service = StatusService(s3_client, s3_bucket_mp3s)

@server.route("/download", methods=["GET"])
def download():
    """Handle file download requests"""
    file_id = request.args.get("fid")
    return download_service.handle_download(file_id)

@server.route("/check-audio/<video_key>", methods=["GET"])
def check_audio_status(video_key):
    """Check audio conversion status"""
    print("\n=== Status Check Request ===")
    status_count.inc()
    return status_service.check_audio_status(video_key)

@server.route("/health", methods=["GET"])
def health_check():
    """Health check endpoint"""
    print("\n🏥 Health check requested")
    return jsonify({"status": "healthy", "service": "download-service"}), 200

if __name__ == "__main__":
    # Get port from environment variable or use default
    port = int(os.environ.get("PORT", 8082))
    print(f"\n🚀 Starting Download Service on port {port}")
    server.run(host="0.0.0.0", port=port) 