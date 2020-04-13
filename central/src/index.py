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
    client = boto3.client('route53')
    hosted_zone_id = os.getenv('HOSTED_ZONE_ID')
  except:
    cfnsend(event, context, 'FAILED', reason='Something early in the process went wrong.')

  try:
    # when present, strip the SNS message headers
    if 'Records' in event:
      event = json.loads(event['Records'][0]['Sns']['Message'])
      print("Lambda Event: " + json.dumps(event))

    type = event['RequestType']
    domain_name = event['ResourceProperties']['DomainName']
    name_servers = event['ResourceProperties']['NameServers']

    resource_records = []
    for record in name_servers:
      resource_records.append({"Value": record})
  except:
    cfnsend(event, context, 'FAILED', 
      reason='DomainName or NameServers not specified or event is malformed.')

  if type == 'Create' or type == 'Update':
    try:
      response = client.change_resource_record_sets(
        HostedZoneId=hosted_zone_id,
        ChangeBatch= {
          'Changes': [{
            'Action': 'UPSERT',
            'ResourceRecordSet': {
              'Name': domain_name,
              'Type': 'NS',
              'TTL': 300,
              'ResourceRecords': resource_records
            }
          }]
        }
      )
      print(response)
    except:
      pass
  elif type == 'Delete':
    try:
      response = client.change_resource_record_sets(
        HostedZoneId=hosted_zone_id,
        ChangeBatch= {
          'Changes': [{
            'Action': 'DELETE',
            'ResourceRecordSet': {
              'Name': domain_name,
              'Type': 'NS',
              'TTL': 300,
              'ResourceRecords': resource_records
            }
          }]
        }
      )
      print(response)
    except:
      pass

  cfnsend(event, context, 'SUCCESS', id=domain_name, reason='RecordSet '+type+'d')
