import sys
import os
from struct import pack
import json
import urllib.parse
import boto3

print('Loading function')

s3 = boto3.client('s3')

# get pharagraph
def Get_Description(words):
  text = ''
  for word in words:
    for symbol in word.symbols:
      text += symbol.text
    text += ' '
  return text

# get paragraph's box
def Get_Box(vertices):
  x_list = []
  y_list = []
  for ver in vertices:
    x_list.append(ver.x)
    y_list.append(ver.y)
  return [min(x_list), min(y_list), max(x_list), max(y_list)]

# Call GCP Vision API
def detect_document(path):
    """Detects document features in an image."""
    from google.cloud import vision
    import io
    client = vision.ImageAnnotatorClient()

    # [START vision_python_migration_document_text_detection]
    with io.open(path, 'rb') as image_file:
        content = image_file.read()

    image = vision.Image(content=content)

    response = client.document_text_detection(image=image)
    if response.error.message:
        raise Exception(
            '{}\nFor more info on error messages, check: '
            'https://cloud.google.com/apis/design/errors'.format(
                response.error.message))
    # [END vision_python_migration_document_text_detection]
    return response.full_text_annotation.pages[0].blocks
        
        
def handler(event, context):
    # Get the object from the event and show its content type
    bucket = event['Records'][0]['s3']['bucket']['name']
    key = urllib.parse.unquote_plus(event['Records'][0]['s3']['object']['key'], encoding='utf-8')
    image_name = key.split('/')[-1]
    image_path = '/tmp/'+image_name

    #get credential_key and set path to the '$GOOGLE_APPLICATION_CREDENTIALS'
    credential_key = 'fabled-meridian-352009-e226c97ba30a.json'
    credential_name = credential_key
    credential_path = '/tmp/'+credential_name

    os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = credential_path

    try:
        S3_response = s3.get_object(Bucket=bucket, Key=key)
        print("CONTENT TYPE: " + S3_response['ContentType'])

        image_path = '/tmp/'+image_name
        s3.download_file(bucket, key, image_path)
        s3.download_file(bucket, credential_key, credential_path)

        response = detect_document(image_path)
        print('Detect_document is done')

    except Exception as e:
        print(e)
        print('Error getting object {} from bucket {}. Make sure they exist and your bucket is in the same region as this function.'.format(key, bucket))
        raise e

    # body = The list of Json
    body = []
    for res in response:
        for parag in res.paragraphs:
          body.append({
              'description' : Get_Description(parag.words),
              'box' : Get_Box(parag.bounding_box.vertices)
          })
    
    print('fixed and deployed by Code Pipeline')
    print(body, key)
    return{
        'body' : body,
        'bucket':bucket,
        'key': key
    }
