import os, json, boto3, uuid
from flask import Flask, request, send_file, jsonify
from auth import validate
from auth_svc import access
from storage import util
from werkzeug.middleware.dispatcher import DispatcherMiddleware
from prometheus_client import Counter
from io import BytesIO
from flask_cors import CORS

server = Flask(__name__)
CORS(server)

unauth_count = Counter('unauthorized_requests_total', 'Total number of unauthorized requests')

#Initialize boto3 clients for S3 and SQS using IAM roles
print("Initializing AWS clients...")
print(f"AWS Region: {os.environ.get('AWS_REGION')}")
print(f"S3 Video Bucket: {os.environ.get('S3_BUCKET_VIDEOS')}")
print(f"S3 MP3 Bucket: {os.environ.get('S3_BUCKET_MP3S')}")

s3_client = boto3.client(
    "s3",
    region_name=os.environ.get("AWS_REGION", "eu-west-1")
)
s3_bucket_videos = os.environ.get("S3_BUCKET_VIDEOS", "your-video-buckets")
s3_bucket_mp3s = os.environ.get("S3_BUCKET_MP3S", "your-mp3-uckets")

sqs_client = boto3.client(
    "sqs",
    region_name=os.environ.get("AWS_REGION", 'eu-west-1')
)
sqs_queue_url = os.environ.get("SQS_VIDEO_QUEUE_URL", "https://sqs.eu-west-1.amazonaws.com/180294222815/your_sqs_url.fifo")

@server.route("/login", methods=["POST"])
def login():
    token, err = access.login(request)

    if not err:
        return token
    else:
        return err

@server.route("/upload", methods=["POST"])
def upload():
    access_data, err = validate.token(request)

    if err:
        unauth_count.inc()
        return err

    access_data = json.loads(access_data)
    print('this side works')
    if access_data["admin"]:
        if len(request.files) > 1 or len(request.files) < 1:
            return "exactly 1 file required", 400

        for _, f in request.files.items():
            video_key, err = util.upload(
                f,
                s3_client,
                s3_bucket_videos,
                sqs_client,
                sqs_queue_url,
                access_data
            )
            if err:
                return err

        return jsonify({"video_key": video_key}), 200
    else:
        return "not authorized", 401

@server.route("/check-audio/<video_key>", methods=["GET"])
def check_audio_status(video_key):
    access_data, err = validate.token(request)

    if err:
        unauth_count.inc()
        return err

    access_data = json.loads(access_data)

    if access_data["admin"]:
        # Audio key is simply video key + .mp3
        audio_key = f"{video_key}.mp3"
        
        try:
            # Check if audio file exists
            s3_client.head_object(Bucket=s3_bucket_mp3s, Key=audio_key)
            return jsonify({
                "status": "completed",
                "audio_key": audio_key
            }), 200
        except:
            return jsonify({"status": "processing"}), 202
    else:
        return "not authorized", 401

@server.route("/download", methods=["GET"])
def download():
    access_data, err = validate.token(request)

    if err:
        unauth_count.inc()
        return err

    access_data = json.loads(access_data)

    if access_data["admin"]:
        fid_string = request.args.get("fid")

        if not fid_string:
            return "fid is required", 400

        try:
            s3_object = s3_client.get_object(Bucket=s3_bucket_mp3s, Key=fid_string)
            file_stream = BytesIO(s3_object['Body'].read())
            return send_file(file_stream, download_name=f"{fid_string}")
        except Exception as err:
            print(err)
            return "internal server error", 500

    return "not authorized", 401

if __name__ == "__main__":
    server.run(host="0.0.0.0", port=8080)
