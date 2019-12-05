from django.core.files import storage


S3Boto3Storage = storage.get_storage_class('storages.backends.s3boto3.S3Boto3Storage')
s3b3s = S3Boto3Storage()


def upload(fname, fcontent):
    fd = s3b3s.open(fname, 'w')
    fd.write(fcontent)
    fd.close()

    return s3b3s.url(fname)