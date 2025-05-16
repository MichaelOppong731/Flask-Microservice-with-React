import os, boto3, json, time, traceback
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST, start_http_server
from flask import Flask
from flask_cors import CORS
from io import BytesIO
import uuid

# Initialize Flask application for metrics
server = Flask(__name__)
CORS(server)

# Prometheus metrics
conversion_count = Counter('conversion_requests_total', 'Total number of conversion requests')
conversion_duration = Histogram('conversion_duration_seconds', 'Time spent converting files')
error_count = Counter('conversion_errors_total', 'Total number of conversion errors')
file_size = Histogram('conversion_file_size_bytes', 'Size of files being converted')
sqs_message_count = Counter('sqs_messages_processed_total', 'Total number of SQS messages processed')

# Add metrics endpoint
@server.route('/metrics')
def metrics():
    return generate_latest(), 200, {'Content-Type': CONTENT_TYPE_LATEST}

# Load configuration from environment variables
print("\n=== Converter Service Starting ===")
print("Initializing AWS clients for Converter Service...")

# AWS configuration from environment variables
aws_region = os.environ["AWS_REGION"]
s3_bucket_videos = os.environ["S3_BUCKET_VIDEOS"]
s3_bucket_mp3s = os.environ["S3_BUCKET_MP3S"]
sqs_video_queue_url = os.environ["SQS_VIDEO_QUEUE_URL"]
sqs_mp3_queue_url = os.environ["SQS_MP3_QUEUE_URL"]

print(f"AWS Region: {aws_region}")
print(f"S3 Video Bucket: {s3_bucket_videos}")
print(f"S3 MP3 Bucket: {s3_bucket_mp3s}")
print(f"SQS Video Queue URL: {sqs_video_queue_url}")
print(f"SQS MP3 Queue URL: {sqs_mp3_queue_url}")

# Initialize AWS clients
s3_client = boto3.client("s3", region_name=aws_region)
sqs_client = boto3.client("sqs", region_name=aws_region)

print("✅ AWS clients initialized successfully\n")

class ConverterService:
    def __init__(self, s3_client, s3_bucket_videos, s3_bucket_mp3s, sqs_client, sqs_mp3_queue_url):
        self.s3_client = s3_client
        self.s3_bucket_videos = s3_bucket_videos
        self.s3_bucket_mp3s = s3_bucket_mp3s
        self.sqs_client = sqs_client
        self.sqs_mp3_queue_url = sqs_mp3_queue_url

    def process_message(self, message):
        print("\n=== Processing New Message ===")
        conversion_count.inc()
        sqs_message_count.inc()
        
        try:
            body = json.loads(message["Body"])
            video_key = body["video_s3_key"]
            username = body["username"]
            
            print(f"Processing video: {video_key} for user: {username}")
            
            # Get video file size
            try:
                response = self.s3_client.head_object(Bucket=self.s3_bucket_videos, Key=video_key)
                file_size.observe(response['ContentLength'])
            except Exception as err:
                print(f"❌ Error getting file size: {err}")
            
            # Convert video to MP3
            with conversion_duration.time():
                # Your conversion logic here
                # This is where you'd implement the actual video to MP3 conversion
                time.sleep(2)  # Simulated conversion time
                
                # Upload converted MP3
                mp3_key = f"{video_key}.mp3"
                self.s3_client.upload_fileobj(
                    BytesIO(b"dummy mp3 content"),  # Replace with actual MP3 content
                    self.s3_bucket_mp3s,
                    mp3_key
                )
            
            # Send notification
            notification = {
                "mp3_s3_key": mp3_key,
                "username": username
            }
            
            self.sqs_client.send_message(
                QueueUrl=self.sqs_mp3_queue_url,
                MessageBody=json.dumps(notification),
                MessageGroupId="mp3-group",
                MessageDeduplicationId=str(uuid.uuid4())
            )
            
            print("✅ Conversion completed successfully")
            return True
            
        except Exception as err:
            print("❌ Conversion Error:")
            print(f"Error Type: {type(err).__name__}")
            print(f"Error Message: {str(err)}")
            print("Full traceback:")
            print(traceback.format_exc())
            error_count.inc()
            return False

    def start_consuming(self):
        print("\n🚀 Starting message consumption...")
        while True:
            try:
                response = self.sqs_client.receive_message(
                    QueueUrl=sqs_video_queue_url,
                    MaxNumberOfMessages=1,
                    WaitTimeSeconds=20
                )
                
                if "Messages" in response:
                    for message in response["Messages"]:
                        if self.process_message(message):
                            self.sqs_client.delete_message(
                                QueueUrl=sqs_video_queue_url,
                                ReceiptHandle=message["ReceiptHandle"]
                            )
                
            except Exception as err:
                print(f"❌ Error consuming messages: {err}")
                error_count.inc()
                time.sleep(5)

# Initialize the converter service
converter_service = ConverterService(
    s3_client,
    s3_bucket_videos,
    s3_bucket_mp3s,
    sqs_client,
    sqs_mp3_queue_url
)

if __name__ == "__main__":
    # Start Prometheus metrics server
    start_http_server(8083)
    print(f"\n📊 Prometheus metrics server started on port 8083")
    
    # Start the converter service
    converter_service.start_consuming()
