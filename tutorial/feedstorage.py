from scrapy.extensions.feedexport import S3FeedStorage as Parent
from botocore.exceptions import ClientError, ParamValidationError
import boto3

class S3FeedStorage(Parent):
    def __init__(self, uri):
        super(S3FeedStorage, self).__init__(uri)
        assert(self.is_botocore)
        try:
            self.s3_client.head_bucket(Bucket=self.bucketname)
        except ClientError:
            self.s3_client.create_bucket(ACL='private', Bucket=self.bucketname, CreateBucketConfiguration={ 'LocationConstraint': boto3.Session().region_name })
        except ParamValidationError:
            # this would mean self.bucketname is not the hydrated one
            # see feedexport.py:_get_storage() for the hydrated one
            pass
        

