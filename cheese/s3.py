import boto3
from flask import current_app

class S3(object):
    def __init__(self, app=None):
        self.app = app
        if app is not None:
            self.init_app()
    def init_app(self, app):
        if self.app is None:
            self.app = app
        self.session = boto3.session.Session()
        self.client = self.session.client('s3',
                        region_name='ams3',
                        endpoint_url=app.config['S3_ENDPOINT_URL'],
                        aws_access_key_id=app.config['S3_ACCESS_KEY_ID'],
                        aws_secret_access_key=app.config['S3_SECRET_ACCESS_KEY'])
    def upload_fileobj_thermal_image(self, image, filename):
        if not current_app.config['DEBUG']:
            key = current_app.config['S3_PREFIX']+'/'+'uploads/'+filename
            self.client.upload_fileobj(image,
                                       current_app.config['S3_BUCKET'],
                                       key)
            response = self.client.put_object_acl(ACL='public-read',
                                                  Bucket=current_app.config['S3_BUCKET'],
                                                  Key=key)
        else:
            current_app.logger.info('Image upload disabled for development')
    def delete_thermal_image(self, key_suffix):
        if not current_app.config['DEBUG']:
            self.client.delete_object(Bucket=current_app.config['S3_BUCKET'],
                                      Key=current_app.config['S3_PREFIX']+'/'+key_suffix)
    def list_directory(self, key_suffix):
        response = self.client.list_objects(
                       Bucket=current_app.config['S3_BUCKET'],
                       Prefix=current_app.config['S3_PREFIX']+'/'+key_suffix)
        result = []
        for key in response['Contents']:
            key = key['Key']
            if key == current_app.config['S3_PREFIX']+'/'+key_suffix+'/':
                continue # Skip the directory key prefix
            key = key.replace(current_app.config['S3_PREFIX']+'/', '')
            result.append(key)
        return result
