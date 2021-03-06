import os
import requests
from flask import current_app
from PIL import Image, ExifTags
from io import BytesIO

def parse_size(size):
    # <max-x-dim-size>x<max-y-dim-size>
    tokens = size.split('x')
    return (int(tokens[0]), int(tokens[1]))

def get_thumbnail(filepath, size):
    """
    Return a URL of a thumbnail for an image at a URL. Generate the thumbnail
    if it doesn't already exist.
    """
    image_url = current_app.config['S3_URL_PREFIX'] + '/' + filepath
    thumb_filename = os.path.splitext(filepath)[0] + '_' + size + os.path.splitext(filepath)[1]
    thumb_path = os.path.join(current_app.config['THUMBNAIL_ROOT'], thumb_filename)
    thumb_dir = os.path.dirname(thumb_path)
    thumb_url = current_app.config['THUMBNAIL_URL']+'/'+thumb_filename
    # Return the thumb if it exists.
    if os.path.exists(thumb_path):
        return thumb_url
    # Create the directories if they don't exist.
    if not os.path.exists(thumb_dir):
        os.makedirs(thumb_dir)
    response = requests.get(image_url)
    if response.status_code != 200:
        current_app.logger.warning('Image for thumbnail not found:' + image_url)
        return image_url
    image = Image.open(BytesIO(response.content))
    # Rotate if recorded in metadata.
    # https://stackoverflow.com/questions/4228530/pil-thumbnail-is-rotating-my-image
    if image.format == 'JPEG' or \
       image.format == 'TIFF':
        for orientation in ExifTags.TAGS.keys():
            if ExifTags.TAGS[orientation]=='Orientation':
                break
        if image._getexif():
            exif=dict(image._getexif().items())
            if orientation in exif:
                if exif[orientation] == 3:
                    image=image.rotate(180, expand=True)
                elif exif[orientation] == 6:
                    image=image.rotate(270, expand=True)
                elif exif[orientation] == 8:
                    image=image.rotate(90, expand=True)
    # Resize the image upto a maximum x OR y dimension.
    image.thumbnail(parse_size(size), Image.ANTIALIAS)
    image.save(thumb_path)
    return thumb_url
