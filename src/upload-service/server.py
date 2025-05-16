import os, boto3, json, uuid, traceback
from flask import Flask, request, jsonify
from werkzeug.middleware.dispatcher import DispatcherMiddleware
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
from flask_cors import CORS
from io import BytesIO
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize Flask application
server = Flask(__name__)
CORS(server)

# Prometheus metrics
upload_count = Counter('upload_requests_total', 'Total number of upload requests')
error_count = Counter('upload_errors_total', 'Total number of upload errors')
upload_duration = Histogram('upload_duration_seconds', 'Time spent processing uploads')
file_size = Histogram('upload_file_size_bytes', 'Size of uploaded files')
sqs_message_count = Counter('sqs_messages_sent_total', 'Total number of SQS messages sent')

# Add metrics endpoint
@server.route('/metrics')
def metrics():
    return generate_latest(), 200, {'Content-Type': CONTENT_TYPE_LATEST}

# Load configuration from environment variables
print("\n=== Upload Service Starting ===")
print("Initializing AWS clients for Upload Service...")

# AWS configuration from environment variables
aws_region = os.environ["AWS_REGION"]
s3_bucket_videos = os.environ["S3_BUCKET_VIDEOS"]
sqs_queue_url = os.environ["SQS_VIDEO_QUEUE_URL"]

print(f"AWS Region: {aws_region}")
print(f"S3 Video Bucket: {s3_bucket_videos}")
print(f"SQS Queue URL: {sqs_queue_url}")

# Initialize AWS clients
s3_client = boto3.client("s3", region_name=aws_region)
sqs_client = boto3.client("sqs", region_name=aws_region)

print("✅ AWS clients initialized successfully\n")

class UploadService:
    """
    Service class to handle video file uploads to S3 and message sending to SQS
    """
    def __init__(self, s3_client, s3_bucket, sqs_client, sqs_queue_url):
        self.s3_client = s3_client
        self.s3_bucket = s3_bucket
        self.sqs_client = sqs_client
        self.sqs_queue_url = sqs_queue_url

    def validate_request(self, files, user_data_str):
        print("\n🔍 Validating upload request...")
        if not user_data_str:
            print("❌ Missing user data")
            error_count.inc()
            return False, ("Missing user data", 401)
            
        try:
            user_data = json.loads(user_data_str)
            print("✅ User data validated")
        except Exception:
            print("❌ Invalid user data format")
            error_count.inc()
            return False, ("Invalid user data format", 400)
        
        if len(files) > 1 or len(files) < 1:
            print("❌ Invalid number of files")
            error_count.inc()
            return False, ("exactly 1 file required", 400)
        
        return True, user_data
    
    def process_upload(self, file, username):
        print(f"\n📤 Processing upload for user: {username}")
        try:
            file_id = str(uuid.uuid4())
            print(f"Generated file ID: {file_id}")
            print(f"Uploading to bucket: {self.s3_bucket}")
            
            # Record file size
            file.seek(0, os.SEEK_END)
            size = file.tell()
            file.seek(0)
            file_size.observe(size)
            
            with upload_duration.time():
                self.s3_client.upload_fileobj(file, self.s3_bucket, file_id)
            print("✅ File uploaded to S3 successfully")
        except Exception as err:
            print("❌ S3 Upload Error:")
            print(f"Error Type: {type(err).__name__}")
            print(f"Error Message: {str(err)}")
            print("Full traceback:")
            print(traceback.format_exc())
            error_count.inc()
            return None, "internal server error, s3 level"

        message = {
            "video_s3_key": file_id,
            "mp3_s3_key": None,
            "username": username,
        }

        try:
            print("\n📨 Sending message to SQS...")
            self.sqs_client.send_message(
                QueueUrl=self.sqs_queue_url,
                MessageBody=json.dumps(message),
                MessageGroupId="video-group",
                MessageDeduplicationId=str(uuid.uuid4())
            )
            sqs_message_count.inc()
            print("✅ Message sent to SQS successfully")
        except Exception as err:
            print(f"❌ SQS Error: {err}")
            print("Cleaning up S3 object...")
            self.s3_client.delete_object(Bucket=self.s3_bucket, Key=file_id)
            error_count.inc()
            return None, f"internal server error sqs issue, {err}"

        return file_id, None
    
    def handle_upload(self, files, user_data_str):
        """
        Main method to handle the upload request
        Args:
            files: Dictionary of uploaded files
            user_data_str: JSON string containing user data
        Returns:
            Response tuple (response, status_code)
        """
        print("\n=== New Upload Request ===")
        upload_count.inc()
        
        # Validate request
        valid, result = self.validate_request(files, user_data_str)
        if not valid:
            error_count.inc()
            return result
        
        user_data = result
        username = user_data.get("username", "anonymous")
        
        # Process the file upload
        for _, file in files.items():
            video_key, err = self.process_upload(file, username)
            if err:
                return err
        
        return jsonify({"video_key": video_key}), 200

# Initialize the upload service
upload_service = UploadService(s3_client, s3_bucket_videos, sqs_client, sqs_queue_url)

@server.route("/upload", methods=["POST"])
def upload():
    return upload_service.handle_upload(request.files, request.form.get('user_data'))

@server.route("/health", methods=["GET"])
def health_check():
    print("\n🏥 Health check requested")
    return jsonify({"status": "healthy", "service": "upload-service"}), 200

if __name__ == "__main__":
    # Get port from environment variable or use default
    port = int(os.environ.get("PORT", 8081))
    print(f"\n🚀 Starting Upload Service on port {port}")
    server.run(host="0.0.0.0", port=port) 