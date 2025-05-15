import boto3
import os
import json

def notification(message):
    try:
        # Parse the incoming message
        message_data = json.loads(message)
        
        # Handle the actual message structure from converter service
        mp3_s3_key = message_data.get("mp3_s3_key")
        username = message_data.get("username")
        
        if not mp3_s3_key or not username:
            print(f"Invalid message format: {message_data}")
            return "Missing required fields: mp3_s3_key or username"
        
        # Initialize SNS client
        sns_client = boto3.client(
            "sns",
            region_name=os.environ.get("AWS_REGION", "eu-west-1")
        )
        
        # Get SNS topic ARN from environment
        topic_arn = os.environ.get("SNS_TOPIC_ARN", "arn:aws:sns:eu-west-1:180294222815:Audio_Update")
        
        # Prepare email message (without showing the audio key)
        subject = "MP3 Download Ready"
        message_body = f"""
Hello {username},

Your MP3 file is now ready for download!

You can download it from your account dashboard.

Best regards,
Video to MP3 Converter Service
        """
        
        # Publish message to SNS topic with filter policy attributes
        response = sns_client.publish(
            TopicArn=topic_arn,
            Message=message_body,
            Subject=subject,
            MessageAttributes={
                'type': {  # Filter policy attribute
                    'DataType': 'String',
                    'StringValue': 'email_notification'  # Subscribers can filter on this
                },
                'username': {  # Additional filter attribute
                    'DataType': 'String', 
                    'StringValue': username
                }
            }
        )
        
        print(f"SNS message sent successfully. MessageId: {response['MessageId']}")
        return None
        
    except json.JSONDecodeError as e:
        print(f"JSON parsing error: {str(e)}")
        return str(e)
    except Exception as e:
        print(f"Error sending SNS notification: {str(e)}")
        return str(e)