import os
import time
import boto3
import json
import sys
from convert import to_mp3
from botocore.exceptions import ClientError

def main():
    # Initialize boto3 clients using IAM roles
    s3_client = boto3.client("s3", region_name=os.environ.get("AWS_REGION", "eu-west-1"))
    sqs_client = boto3.client("sqs", region_name=os.environ.get("AWS_REGION", "eu-west-1"))

    s3_video_bucket = os.environ.get("S3_BUCKET_VIDEOS", "your-video-buckets")
    s3_mp3_bucket = os.environ.get("S3_BUCKET_MP3S", 'your-mp3-uckets')
    video_queue_url = os.environ.get("SQS_VIDEO_QUEUE_URL", "https://sqs.eu-west-1.amazonaws.com/180294222815/your_sqs_url.fifo")
    mp3_queue_url = os.environ.get("SQS_MP3_QUEUE_URL", "https://sqs.eu-west-1.amazonaws.com/180294222815/mp3_sqs_queue.fifo")

    print("✅ Initialized S3 and SQS clients")
    print("📦 S3 Video Bucket:", s3_video_bucket)
    print("🎵 S3 MP3 Bucket:", s3_mp3_bucket)
    print("📬 SQS Video Queue URL:", video_queue_url)
    print("📬 SQS MP3 Queue URL:", mp3_queue_url)
    print("🔄 Waiting for messages from SQS, to exit press CTRL+C")

    while True:
        response = sqs_client.receive_message(
            QueueUrl=video_queue_url,
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
                err = to_mp3.start(
                    body,
                    s3_client,
                    s3_video_bucket,
                    s3_mp3_bucket,
                    sqs_client,
                    mp3_queue_url
                )

                if err:
                    print(f"🚨 Error returned by to_mp3.start(): {err}")
                else:
                    print("✅ MP3 conversion succeeded")

                # Always delete message after processing
                print("🧹 Deleting message from queue...")
                sqs_client.delete_message(
                    QueueUrl=video_queue_url,
                    ReceiptHandle=receipt_handle
                )
                print("✅ Message deleted")

            except ClientError as e:
                error_code = e.response["Error"]["Code"]
                if error_code == "404":
                    print("🚨 S3 file not found (404), deleting message to avoid retries.")
                    sqs_client.delete_message(
                        QueueUrl=video_queue_url,
                        ReceiptHandle=receipt_handle
                    )
                else:
                    print(f"🚨 AWS ClientError: {str(e)} — will not delete message.")
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
