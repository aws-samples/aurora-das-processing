## Customizing Aurora - Database Activity Streams (DAS)  
This Lambda function reads the Kinesis Firehose records as Input, decrypt the log records using KMS key, unzip the records and then categories the event type into S3 folder structure. When you enable DAS on Aurora, it create a Kinesis streams for you. 

## Getting started
This can all be deployed with AWS SAM.

$ sam build
$ sam deploy --guided

## Security

See [CONTRIBUTING](CONTRIBUTING.md#security-issue-notifications) for more information.

## License

This library is licensed under the MIT-0 License. See the LICENSE file.

