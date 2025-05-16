from io import BytesIO
from flask import send_file


class DownloadService:
    def __init__(self, s3_client, s3_bucket):
        self.s3_client = s3_client
        self.s3_bucket = s3_bucket
    
    def validate_request(self, file_id):
        """Validate download request"""
        if not file_id:
            return False, ("fid is required", 400)
        return True, None
    
    def download_file(self, file_id):
        """Download file from S3"""
        try:
            # Get the object from S3
            s3_object = self.s3_client.get_object(Bucket=self.s3_bucket, Key=file_id)
            # Create a file-like object in memory
            file_stream = BytesIO(s3_object['Body'].read())
            # Return the file for download
            return send_file(file_stream, download_name=f"{file_id}")
        except Exception as err:
            print(f"Error downloading file {file_id}: {err}")
            return "internal server error", 500
    
    def handle_download(self, file_id):
        """Main method to handle download request"""
        # Validate request
        valid, error = self.validate_request(file_id)
        if not valid:
            return error
        
        # Download the file
        return self.download_file(file_id) 