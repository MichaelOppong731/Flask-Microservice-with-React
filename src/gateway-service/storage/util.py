import boto3
import json
import uuid
import traceback

def upload(f, s3_client, bucket_name, sqs_client, queue_url, access):
    try:
        # Generate a unique file name
        file_id = str(uuid.uuid4())
        print(f"Attempting to upload to bucket: {bucket_name}")
        s3_client.upload_fileobj(f, bucket_name, file_id)
    except Exception as err:
        print("S3 Upload Error Details:")
        print(f"Error Type: {type(err).__name__}")
        print(f"Error Message: {str(err)}")
        print("Full traceback:")
        print(traceback.format_exc())
        return None, "internal server error, s3 level"

    message = {
        "video_s3_key": file_id,
        "mp3_s3_key": None,
        "username": access["username"],
    }

    try:
        sqs_client.send_message(
            QueueUrl=queue_url,
            MessageBody=json.dumps(message),
            MessageGroupId="video-group",
            MessageDeduplicationId=str(uuid.uuid4())
        )
    except Exception as err:
        print(err)
        # Optionally, delete the file from S3 if SQS fails
        s3_client.delete_object(Bucket=bucket_name, Key=file_id)
        return None, f"internal server error sqs issue, {err}"

    return file_id, None  # Return video key and no error