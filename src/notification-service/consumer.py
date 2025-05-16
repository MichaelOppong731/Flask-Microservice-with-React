import os, boto3, json, time, traceback
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST, start_http_server
from flask import Flask
from flask_cors import CORS

# Initialize Flask application for metrics
server = Flask(__name__)
CORS(server)

# Prometheus metrics
notification_count = Counter('notification_requests_total', 'Total number of notification requests')
notification_duration = Histogram('notification_duration_seconds', 'Time spent sending notifications')
error_count = Counter('notification_errors_total', 'Total number of notification errors')
sqs_message_count = Counter('sqs_messages_processed_total', 'Total number of SQS messages processed')

# Add metrics endpoint
@server.route('/metrics')
def metrics():
    return generate_latest(), 200, {'Content-Type': CONTENT_TYPE_LATEST}

# Load configuration from environment variables
print("\n=== Notification Service Starting ===")
print("Initializing AWS clients for Notification Service...")

# AWS configuration from environment variables
aws_region = os.environ["AWS_REGION"]
sqs_mp3_queue_url = os.environ["SQS_MP3_QUEUE_URL"]
sns_topic_arn = os.environ["SNS_TOPIC_ARN"]

print(f"AWS Region: {aws_region}")
print(f"SQS MP3 Queue URL: {sqs_mp3_queue_url}")
print(f"SNS Topic ARN: {sns_topic_arn}")

# Initialize AWS clients
sqs_client = boto3.client("sqs", region_name=aws_region)
sns_client = boto3.client("sns", region_name=aws_region)

print("✅ AWS clients initialized successfully\n")

class NotificationService:
    def __init__(self, sqs_client, sqs_mp3_queue_url, sns_client, sns_topic_arn):
        self.sqs_client = sqs_client
        self.sqs_mp3_queue_url = sqs_mp3_queue_url
        self.sns_client = sns_client
        self.sns_topic_arn = sns_topic_arn

    def process_message(self, message):
        print("\n=== Processing New Message ===")
        notification_count.inc()
        sqs_message_count.inc()
        
        try:
            body = json.loads(message["Body"])
            mp3_key = body["mp3_s3_key"]
            username = body["username"]
            
            print(f"Sending notification for MP3: {mp3_key} to user: {username}")
            
            # Send notification
            with notification_duration.time():
                self.sns_client.publish(
                    TopicArn=self.sns_topic_arn,
                    Message=f"Your MP3 conversion is ready! File: {mp3_key}",
                    Subject="MP3 Conversion Complete",
                    MessageAttributes={
                        'username': {
                            'DataType': 'String',
                            'StringValue': username
                        }
                    }
                )
            
            print("✅ Notification sent successfully")
            return True
            
        except Exception as err:
            print("❌ Notification Error:")
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
                    QueueUrl=self.sqs_mp3_queue_url,
                    MaxNumberOfMessages=1,
                    WaitTimeSeconds=20
                )
                
                if "Messages" in response:
                    for message in response["Messages"]:
                        if self.process_message(message):
                            self.sqs_client.delete_message(
                                QueueUrl=self.sqs_mp3_queue_url,
                                ReceiptHandle=message["ReceiptHandle"]
                            )
                
            except Exception as err:
                print(f"❌ Error consuming messages: {err}")
                error_count.inc()
                time.sleep(5)

# Initialize the notification service
notification_service = NotificationService(
    sqs_client,
    sqs_mp3_queue_url,
    sns_client,
    sns_topic_arn
)

if __name__ == "__main__":
    # Start Prometheus metrics server
    start_http_server(8084)
    print(f"\n📊 Prometheus metrics server started on port 8084")
    
    # Start the notification service
    notification_service.start_consuming()