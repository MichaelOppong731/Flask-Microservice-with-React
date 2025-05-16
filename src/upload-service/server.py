import os, boto3, json, uuid, traceback
from flask import Flask, request, jsonify
from werkzeug.middleware.dispatcher import DispatcherMiddleware
from prometheus_client import Counter
from flask_cors import CORS
from io import BytesIO

server = Flask(__name__)
CORS(server)

# Metrics
upload_count = Counter('upload_requests_total', 'Total number of upload requests')
error_count = Counter('upload_errors_total', 'Total number of upload errors')

# AWS configuration
print("Initializing AWS clients for Upload Service...")
print(f"AWS Region: {os.environ.get('AWS_REGION', 'eu-west-1')}")
print(f"S3 Video Bucket: {os.environ.get('S3_BUCKET_VIDEOS', 'your-video-buckets')}")

aws_region = os.environ.get("AWS_REGION", "eu-west-1")
s3_bucket_videos = os.environ.get("S3_BUCKET_VIDEOS", "your-video-buckets")
sqs_queue_url = os.environ.get("SQS_VIDEO_QUEUE_URL", "https://sqs.eu-west-1.amazonaws.com/180294222815/your_sqs_url.fifo")

# Initialize AWS clients
s3_client = boto3.client("s3", region_name=aws_region)
sqs_client = boto3.client("sqs", region_name=aws_region)

class UploadService:
    def __init__(self, s3_client, s3_bucket, sqs_client, sqs_queue_url):
        self.s3_client = s3_client
        self.s3_bucket = s3_bucket
        self.sqs_client = sqs_client
        self.sqs_queue_url = sqs_queue_url

    def validate_request(self, files, user_data_str):
        """Validate upload request"""
        if not user_data_str:
            return False, ("Missing user data", 401)
            
        try:
            user_data = json.loads(user_data_str)
        except Exception:
            return False, ("Invalid user data format", 400)
        
        if len(files) > 1 or len(files) < 1:
            return False, ("exactly 1 file required", 400)
        
        return True, user_data
    
    def process_upload(self, file, username):
        """Process file upload to S3 and send message to SQS"""
        try:
            # Generate a unique file name
            file_id = str(uuid.uuid4())
            print(f"Attempting to upload to bucket: {self.s3_bucket}")
            self.s3_client.upload_fileobj(file, self.s3_bucket, file_id)
        except Exception as err:
            print("S3 Upload Error Details:")
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
            self.sqs_client.send_message(
                QueueUrl=self.sqs_queue_url,
                MessageBody=json.dumps(message),
                MessageGroupId="video-group",
                MessageDeduplicationId=str(uuid.uuid4())
            )
        except Exception as err:
            print(err)
            # Optionally, delete the file from S3 if SQS fails
            self.s3_client.delete_object(Bucket=self.s3_bucket, Key=file_id)
            error_count.inc()
            return None, f"internal server error sqs issue, {err}"

        return file_id, None  # Return video key and no error
    
    def handle_upload(self, files, user_data_str):
        """Main method to handle the upload request"""
        upload_count.inc()
        
        # Validate request
        valid, result = self.validate_request(files, user_data_str)
        if not valid:
            error_count.inc()
            return result
        
        user_data = result
        username = user_data.get("username", "anonymous")
        
        # Get the file
        for _, file in files.items():
            video_key, err = self.process_upload(file, username)
            if err:
                return err
        
        return jsonify({"video_key": video_key}), 200

# Initialize the upload service
upload_service = UploadService(s3_client, s3_bucket_videos, sqs_client, sqs_queue_url)

@server.route("/upload", methods=["POST"])
def upload():
    """Handle file upload requests"""
    return upload_service.handle_upload(request.files, request.form.get('user_data'))

@server.route("/health", methods=["GET"])
def health_check():
    """Health check endpoint"""
    return jsonify({"status": "healthy", "service": "upload-service"}), 200

if __name__ == "__main__":
    # Run on port 8081 instead of the original gateway port (8080)
    server.run(host="0.0.0.0", port=8081) 