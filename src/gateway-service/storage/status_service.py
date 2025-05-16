from flask import jsonify

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