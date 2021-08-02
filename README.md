## Customizing Aurora - Database Activity Streams (DAS)  
This Lambda function reads the Kinesis Firehose records as Input, decrypt the log records using KMS key, unzip the records and then categories the event type into S3 folder structure. When you enable DAS on Aurora, it create a Kinesis streams for you. 

```
.
├── README.MD                   <-- This instructions file
├── lambda_function.py          <-- Source code for a lambda function
└── requirements.txt            <-- Lambda dependencies
├── template.yaml               <-- SAM template
```

## Requirements 
* AWS CLI already configured with Administrator permission
* SAM CLI - [Install the SAM CLI](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/serverless-sam-cli-install.html)
* docker [Install Docker community edition](https://hub.docker.com/search/?type=edition&offering=community)
* Python3.8 installed

## Getting started
This can all be deployed with AWS SAM.
```
$ sam build  
$ sam deploy --guided
```

See [Serverless Application Model (SAM)](https://github.com/aws/serverless-application-model/blob/master/HOWTO.md) HOWTO Guide for more details in how to get started.

## Security

See [CONTRIBUTING](CONTRIBUTING.md#security-issue-notifications) for more information.

## License

This library is licensed under the MIT-0 License. See the LICENSE file.

