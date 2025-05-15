import os
import time
import boto3
import json
from send import email

def main():
    # Initialize boto3 SQS client
    sqs_client = boto3.client(
        "sqs",
        region_name=os.environ.get("AWS_REGION", "eu-west-1")
    )
    
    mp3_queue_url = os.environ.get("SQS_MP3_QUEUE_URL", "https://sqs.eu-west-1.amazonaws.com/180294222815/mp3_sqs_queue.fifo")
    
    print("Waiting for messages from SQS. To exit press CTRL+C")
    
    while True:
        # Poll SQS for messages
        response = sqs_client.receive_message(
            QueueUrl=mp3_queue_url,
            MaxNumberOfMessages=1,
            WaitTimeSeconds=10
        )
        
        messages = response.get("Messages", [])
        for msg in messages:
            receipt_handle = msg["ReceiptHandle"]
            body = msg["Body"]
            
            err = email.notification(body)
            
            if err:
                print(f"Error sending notification: {err}")
                # Delete message even on error to avoid infinite retries
                # In production, consider implementing retry logic
            
            # Always delete message from SQS after processing attempt
            sqs_client.delete_message(
                QueueUrl=mp3_queue_url,
                ReceiptHandle=receipt_handle
            )
            print("Message processed and deleted from queue")
        
        time.sleep(1)  # Avoid tight loop

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("Interrupted")
        try:
            sys.exit(0)
        except SystemExit:
            os._exit(0)