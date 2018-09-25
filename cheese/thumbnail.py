import os
import requests
from flask import current_app
from PIL import Image
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
    image_url = current_app.config['S3_PREFIX'] + '/' + filepath
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
    image = Image.open(BytesIO(response.content))
    # Resize the image upto a maximum x OR y dimension.
    image.thumbnail(parse_size(size), Image.ANTIALIAS)
    image.save(thumb_path)
    return thumb_url
