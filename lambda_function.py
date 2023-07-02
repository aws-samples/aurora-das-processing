#This Lambda function reads the Kinesis Firehose records as Input, decrypt the log records using KMS key, unzip the records and then categories the event type into S3 folder structure. 
from __future__ import print_function
import os
import json
import boto3
import base64
import zlib
import aws_encryption_sdk
from aws_encryption_sdk import CommitmentPolicy
from aws_encryption_sdk.internal.crypto import WrappingKey
from aws_encryption_sdk.key_providers.raw import RawMasterKeyProvider
from aws_encryption_sdk.identifiers import WrappingAlgorithm, EncryptionKeyType
import datetime

REGION_NAME = os.environ['region_name'] # 'us-east-1'
RESOURCE_ID = os.environ['resource_id'] #'cluster-2VRZBI263EBXMYD3BQUFSIQ554'
BUCKET_NAME = os.environ['bucket_name'] # 'dastestbucket'

enc_client = aws_encryption_sdk.EncryptionSDKClient(commitment_policy=CommitmentPolicy.REQUIRE_ENCRYPT_ALLOW_DECRYPT)
kms = boto3.client('kms', region_name=REGION_NAME)
s3 = boto3.client('s3')
todays_date = datetime.datetime.now()

class MyRawMasterKeyProvider(RawMasterKeyProvider):
    provider_id = "BC"
    def __new__(cls, *args, **kwargs):
        obj = super(RawMasterKeyProvider, cls).__new__(cls)
        return obj
    def __init__(self, plain_key):
        RawMasterKeyProvider.__init__(self)
        self.wrapping_key = WrappingKey(wrapping_algorithm=WrappingAlgorithm.AES_256_GCM_IV12_TAG16_NO_PADDING,
                                        wrapping_key=plain_key, wrapping_key_type=EncryptionKeyType.SYMMETRIC)
    def _get_raw_key(self, key_id):
        return self.wrapping_key

def decrypt_payload(payload, data_key):
    my_key_provider = MyRawMasterKeyProvider(data_key)
    my_key_provider.add_master_key("DataKey")
    #Decrypt the records using the master key.
    decrypted_plaintext, header = enc_client.decrypt(
        source=payload,
        materials_manager=aws_encryption_sdk.materials_managers.default.DefaultCryptoMaterialsManager(master_key_provider=my_key_provider))
    return decrypted_plaintext

def decrypt_decompress(payload, key):
    decrypted = decrypt_payload(payload, key)
    #Decompress the records using zlib library.
    decrypted = zlib.decompress(decrypted, zlib.MAX_WBITS + 16)
    return decrypted

#Lambda Handler entry point
def lambda_handler(event, context):
    output = []
    print("Received event: " + json.dumps(event, indent=2))
    for dasRecord in event['records']:
        recID = dasRecord['recordId']
        data = base64.b64decode(dasRecord['data'])
        # Do processing here
        val = processDASRecord(recID,data)
        #Record count has to match when we return to Firehose. If we don’t want certain records to reach destination – result should be equal to Dropped. 
        if len(val)>0:
            output_record = {
                'recordId': dasRecord['recordId'],
                'result': 'Ok',
                'data': base64.b64encode(json.dumps(val).encode("utf-8"))
            }
        else:
            output_record = {
                'recordId': dasRecord['recordId'],
                'result': 'Dropped',
                'data': base64.b64encode(b'this is a dropped event')
            }
        output.append(output_record)

    print('Successfully processed {} records.'.format(len(event['records'])))
    return {'records': output}

def processDASRecord(rID, rec):
    record = json.loads(rec)
    if record['type'] == 'DatabaseActivityMonitoringRecords':
        dbEvents = record["databaseActivityEvents"]
        dataKey = base64.b64decode(record["key"])
        try:
            #Decrypt the envelope master key using KMS
            data_key_decrypt_result = kms.decrypt(CiphertextBlob=dataKey, EncryptionContext={'aws:rds:dbc-id':RESOURCE_ID})
        except Exception as e:
            print(e)
            raise e

        try:
            plaintextEvents = decrypt_decompress(base64.b64decode(dbEvents), data_key_decrypt_result['Plaintext'])
        except Exception as e:
            print(e)
            raise e
        
        retObj = []
        #parse thru all activity and categorize it.
        try:
            events = json.loads(plaintextEvents)
            for dbEvent in events['databaseActivityEventList']:
                #filter out events which you don't want to log.
                if dbEvent['type']== "heartbeat": #or  eventType == "READ":
                    print ("Heart beat event - ignored event, dropping it.")
                    continue

                if not (dbEvent.get('command') is None):
                    eventType = dbEvent['command']
                    #use this section to log all events in separate S3 folder. 
                    #parse and write individual type of events to separate S3 folders. 
                    s3suffix = '/' + str(todays_date.year) + '/' + str(todays_date.month) + '/' + str(todays_date.day) + '/' + rID + '.txt' 
                    s3.put_object(Body=json.dumps(dbEvent, ensure_ascii=False), Bucket=BUCKET_NAME, Key = 'parsed/'+ eventType + s3suffix )

            retObj.append(dbEvent)

        except Exception as e:
            print (e)
            raise e
        
        return retObj
