import json
import boto3
import sys
import os
import requests

def cfnsend(event, context, status, **kwargs):
    responseBody = {
      'Status': status,
      'Reason': kwargs.get('reason', ''),
      'StackId': event['StackId'],
      'RequestId': event['RequestId'],
      'PhysicalResourceId': kwargs.get('id', None),
      'LogicalResourceId': event['LogicalResourceId'],
      'NoEcho': kwargs.get('noEcho', False),
      'Data': kwargs.get('data', {})
    }
    json_responseBody = json.dumps(responseBody)
    headers = {
        'content-type' : '',
        'content-length' : str(len(json_responseBody))
    }
    requests.put(event['ResponseURL'],
                 data=json_responseBody,
                 headers=headers)

def lambda_handler(event, context):

  print("Original Event: " + json.dumps(event))

  try:
    client = boto3.client('s3')
    type = event['RequestType']
    bucket = event['ResourceProperties']['Bucket']
    key = event['ResourceProperties']['Key']
    content = event['ResourceProperties']['Content']
  except:
    cfnsend(event, context, 'FAILED', 
      reason='Bucket, Key or Content missing, event is malformed, or boto3 client issues')

  if type == 'Create' or type == 'Update':
    try:
      client.put_object(
        ACL='public-read',
        Bucket=bucket,
        Key=key,
        ContentType='text/html',
        Body=content.encode()
      )
    except:
      pass
  elif type == 'Delete':
    try:
      client.delete_object(
        Bucket=bucket,
        Key=key
      )
    except:
      pass
  cfnsend(event, context, 'SUCCESS', id=bucket+'/'+key, reason=type+' Done')
