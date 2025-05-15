import boto3
import json
import tempfile
import os
import moviepy.editor

def start(message, s3_client, s3_video_bucket, s3_mp3_bucket, sqs_client, mp3_queue_url):
    try:
        message = json.loads(message)

        # Download video from S3 to temp file
        video_key = message["video_s3_key"]
        tf = tempfile.NamedTemporaryFile(delete=False)
        s3_client.download_fileobj(s3_video_bucket, video_key, tf)
        tf.close()

        # Extract audio and save as mp3
        audio = moviepy.editor.VideoFileClip(tf.name).audio
        tf_mp3_path = os.path.join(tempfile.gettempdir(), f"{video_key}.mp3")
        audio.write_audiofile(tf_mp3_path)

        # Upload mp3 to S3 with deterministic naming
        mp3_key = f"{video_key}.mp3"  # Simply append .mp3 to video key
        with open(tf_mp3_path, "rb") as f:
            s3_client.upload_fileobj(f, s3_mp3_bucket, mp3_key)

        # Clean up temp files
        os.remove(tf.name)
        os.remove(tf_mp3_path)

        # Update message with mp3 key
        message["mp3_s3_key"] = mp3_key

        # Send message to SQS (FIFO example)
        sqs_client.send_message(
            QueueUrl=mp3_queue_url,
            MessageBody=json.dumps(message),
            MessageGroupId="mp3-group",
            MessageDeduplicationId=f"notif-{video_key}"  # Use video key for deduplication
        )

        return None  # success

    except Exception as err:
        # Clean up in case of partial failure
        if os.path.exists(tf.name):
            os.remove(tf.name)
        if 'tf_mp3_path' in locals() and os.path.exists(tf_mp3_path):
            os.remove(tf_mp3_path)
        if 'mp3_key' in locals():
            try:
                s3_client.delete_object(Bucket=s3_mp3_bucket, Key=mp3_key)
            except:
                pass
        return f"failed to process video: {err}"
