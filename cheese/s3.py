import boto3

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
    def upload_fileobj_thermal_image(image, filename):
        self.client.upload_fileobj(image,
                                   current_app.config['S3_BUCKET'],
                                   'uploads/'+filename)
