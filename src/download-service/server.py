import os, boto3
from flask import Flask, request, jsonify, send_file
from werkzeug.middleware.dispatcher import DispatcherMiddleware
from prometheus_client import Counter
from flask_cors import CORS
from io import BytesIO

server = Flask(__name__)
CORS(server)

# Metrics
download_count = Counter('download_requests_total', 'Total number of download requests')
status_count = Counter('status_requests_total', 'Total number of status check requests')
error_count = Counter('download_service_errors_total', 'Total number of errors in download service')

# AWS configuration
print("Initializing AWS clients for Download Service...")
print(f"AWS Region: {os.environ.get('AWS_REGION', 'eu-west-1')}")
print(f"S3 MP3 Bucket: {os.environ.get('S3_BUCKET_MP3S', 'your-mp3-uckets')}")

aws_region = os.environ.get("AWS_REGION", "eu-west-1")
s3_bucket_mp3s = os.environ.get("S3_BUCKET_MP3S", "your-mp3-uckets")

# Initialize AWS clients
s3_client = boto3.client("s3", region_name=aws_region)

class DownloadService:
    def __init__(self, s3_client, s3_bucket):
        self.s3_client = s3_client
        self.s3_bucket = s3_bucket
    
    def validate_request(self, file_id):
        """Validate download request"""
        if not file_id:
            return False, ("fid is required", 400)
        return True, None
    
    def download_file(self, file_id):
        """Download file from S3"""
        try:
            # Get the object from S3
            s3_object = self.s3_client.get_object(Bucket=self.s3_bucket, Key=file_id)
            # Create a file-like object in memory
            file_stream = BytesIO(s3_object['Body'].read())
            # Return the file for download
            return send_file(file_stream, download_name=f"{file_id}")
        except Exception as err:
            print(f"Error downloading file {file_id}: {err}")
            error_count.inc()
            return "internal server error", 500
    
    def handle_download(self, file_id):
        """Main method to handle download request"""
        download_count.inc()
        
        # Validate request
        valid, error = self.validate_request(file_id)
        if not valid:
            error_count.inc()
            return error
        
        # Download the file
        return self.download_file(file_id)

class StatusService:
    def __init__(self, s3_client, s3_bucket):
        self.s3_client = s3_client
        self.s3_bucket = s3_bucket
    
    def check_audio_status(self, video_key):
        """Check if audio file exists for a given video key"""
        # Audio key is simply video key + .mp3
        audio_key = f"{video_key}.mp3"
        
        try:
            # Check if audio file exists in S3
            self.s3_client.head_object(Bucket=self.s3_bucket, Key=audio_key)
            return jsonify({
                "status": "completed",
                "audio_key": audio_key
            }), 200
        except Exception as err:
            # If audio file doesn't exist, it's still processing
            print(f"Audio file {audio_key} not found, still processing: {err}")
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
    status_count.inc()
    return status_service.check_audio_status(video_key)

@server.route("/health", methods=["GET"])
def health_check():
    """Health check endpoint"""
    return jsonify({"status": "healthy", "service": "download-service"}), 200

if __name__ == "__main__":
    # Run on port 8082 (different from both gateway and upload service)
    server.run(host="0.0.0.0", port=8082) 