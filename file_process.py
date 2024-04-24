import boto3
import os
from botocore.exceptions import ClientError

s3 = boto3.client('s3')
sns = boto3.client('sns')

supported_formats = ['pdf', 'doc', 'docx', 'jpeg', 'png']
sns_topic_arn = os.environ.get('SNS_TOPIC_ARN')

def lambda_handler(event, context):
    # Get the bucket name and key (file path) from the event
    bucket = event['Records'][0]['s3']['bucket']['name']
    key = event['Records'][0]['s3']['object']['key']

    # Check if the file extension is supported
    file_extension = key.split('.')[-1].lower()
    if file_extension not in supported_formats:
        print(f"File format not supported: {file_extension}")
        return

    # Trigger the format conversion process (e.g., using a third-party library or service)
    converted_file_key = f"converted/{key}"
    convert_file(bucket, key, converted_file_key)

    # Publish a notification to SNS
    message = f"File {key} has been converted to {converted_file_key}"
    publish_notification(message)

    print('File conversion completed successfully')

def convert_file(bucket, source_key, destination_key, file_extension):
    if file_extension == 'pdf':
        convert_pdf(bucket, source_key, destination_key)
    elif file_extension in ['doc', 'docx']:
        convert_docx(bucket, source_key, destination_key)
    else:
        print(f"Unsupported file format: {file_extension}")

def convert_pdf(bucket, source_key, destination_key):
    # Download the PDF file from S3
    local_file = '/tmp/file.pdf'
    s3.download_file(bucket, source_key, local_file)

    # Convert PDF to PNG using pdf2image
    images = pdf2image.convert_from_path(local_file)

    # Upload the converted PNG files to S3
    for i, image in enumerate(images):
        png_key = f"{destination_key.split('.')[0]}_{i}.png"
        image.save('/tmp/image.png')
        s3.upload_file('/tmp/image.png', bucket, png_key)

    # Clean up the local files
    os.remove(local_file)
    os.remove('/tmp/image.png')

def convert_docx(bucket, source_key, destination_key):
    # Download the DOCX file from S3
    local_file = '/tmp/file.docx'
    s3.download_file(bucket, source_key, local_file)

    # Convert DOCX to PDF using python-docx
    doc = docx.Document(local_file)
    pdf_path = '/tmp/file.pdf'
    doc.save(pdf_path)

    # Upload the converted PDF file to S3
    s3.upload_file(pdf_path, bucket, destination_key)

    # Clean up the local files
    os.remove(local_file)
    os.remove(pdf_path)

def publish_notification(message):
    try:
        response = sns.publish(
            TopicArn=sns_topic_arn,
            Message=message
        )
        print('Notification published successfully')
    except ClientError as e:
        print(f"Error publishing notification: {e.response['Error']['Message']}") 
