import os
import time
import boto3
import json
import sys
from send import email
from botocore.exceptions import ClientError

def main():
    # Initialize boto3 clients using IAM roles
    aws_region = os.environ["AWS_REGION"]
    sqs_client = boto3.client("sqs", region_name=aws_region)
    
    # Get SQS queue URL from environment
    mp3_queue_url = os.environ["SQS_MP3_QUEUE_URL"]

    print("✅ Initialized SQS client")
    print("📬 SQS MP3 Queue URL:", mp3_queue_url)
    print("🔄 Waiting for messages from SQS, to exit press CTRL+C")
    
    while True:
        response = sqs_client.receive_message(
            QueueUrl=mp3_queue_url,
            MaxNumberOfMessages=1,
            WaitTimeSeconds=10
        )
        
        messages = response.get("Messages", [])
        for msg in messages:
            print("📨 New message received from SQS")
            receipt_handle = msg["ReceiptHandle"]
            body = msg["Body"]
            print("📦 Raw Message Body:", body)
            
            try:
                # Process the notification
                err = email.notification(body)
                
                if err:
                    print(f"🚨 Error processing notification: {err}")
                else:
                    print("✅ Notification sent successfully")

                # Delete message after processing
                print("🧹 Deleting message from queue...")
                sqs_client.delete_message(
                    QueueUrl=mp3_queue_url,
                    ReceiptHandle=receipt_handle
                )
                print("✅ Message deleted")

            except Exception as e:
                print(f"🔥 Unexpected error: {e}")
        
        time.sleep(1)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n🛑 Interrupted by user")
        try:
            sys.exit(0)
        except SystemExit:
            os._exit(0)