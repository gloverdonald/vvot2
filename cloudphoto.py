#!/usr/bin/python3
# !pip install boto3
# !pip install jinja2
import argparse
import fileinput
import sys
import boto3
from botocore.client import ClientError
from os import path
import os
import random
import shutil
import string
import pathlib
from pathlib import Path
from jinja2 import Template

ROOT_DIRECTORY = path.dirname(pathlib.Path(__file__))

file_path = f"~{os.sep}.config{os.sep}cloudphoto{os.sep}cloudphotorc"

SITE_CONFIGURATION = {
    "ErrorDocument": {
        "Key": "error.html"
    },
    "IndexDocument": {
        "Suffix": "index.html"
    },
}

IMG_EXTENSIONS = [".jpg", ".jpeg", ".JPG", ".JPEG"]
ACL = 'public-read'

parser = argparse.ArgumentParser(prog='cloudphoto')

command_parser = parser.add_subparsers(title='command',
                                       dest='command')

command_init = command_parser.add_parser('init',
                                         help='create a settings file and create a package')

command_list = command_parser.add_parser('list',
                                         help='list photo albums')

command_list.add_argument('--album',
                          metavar='ALBUM',
                          type=str,
                          help='Album name')

command_download = command_parser.add_parser('download',
                                             help="download photos")

command_download.add_argument('--album',
                              metavar='ALBUM',
                              type=str,
                              help='Photo album name',
                              required=True)

command_download.add_argument('--path',
                              metavar='PHOTOS_DIR',
                              type=str,
                              default='.',
                              help='Path to photos',
                              required=False)

command_upload = command_parser.add_parser('upload',
                                           help='upload photos')

command_upload.add_argument('--album',
                            metavar='ALBUM',
                            type=str,
                            help='Album name',
                            required=True)

command_upload.add_argument('--path',
                            metavar='PHOTOS_DIR',
                            type=str,
                            default='.',
                            help='Path to photos',
                            required=False)

command_delete = command_parser.add_parser('delete',
                                           help='delete album')

command_delete.add_argument('--album',
                            metavar='ALBUM',
                            type=str,
                            help='Album name')

command_delete.add_argument('--photo',
                            metavar='PHOTO',
                            type=str,
                            help='Photo name')

command_make_site = command_parser.add_parser('mksite',
                                              help='start website')

args = parser.parse_args()


def make_bucket(bkt, aws_access_key, secret, endpoint_url, region):
    session = boto3.session.Session()
    s3 = session.client(
        service_name='s3',
        endpoint_url=endpoint_url,
        aws_access_key_id=aws_access_key,
        aws_secret_access_key=secret,
        region_name=region
    )

    try:
        s3.head_bucket(Bucket=bkt)
        print(f"Bucket '{bkt}' exists.")
    except ClientError:
        s3.create_bucket(Bucket=bkt, ACL=ACL)


def get_albums(bkt, aws_access_key, secret, endpoint_url, region):
    session = boto3.session.Session()
    s3 = session.client(
        service_name='s3',
        endpoint_url=endpoint_url,
        aws_access_key_id=aws_access_key,
        aws_secret_access_key=secret,
        region_name=region
    )
    try:
        s3.list_objects(Bucket=bkt)['Contents']
    except:
        raise Exception("Bucket is empty")
    unique_albums = []
    for key in s3.list_objects(Bucket=bkt)['Contents']:
        if key['Key'].endswith("/") and key['Key'].split("/")[0] not in unique_albums:
            unique_albums.append(key['Key'].split("/")[0])
    for value in unique_albums:
        print(value)


def get_files(bkt, aws_access_key, secret, album, endpoint_url, region):
    session = boto3.session.Session()
    s3 = session.resource(
        service_name='s3',
        endpoint_url=endpoint_url,
        aws_access_key_id=aws_access_key,
        aws_secret_access_key=secret,
        region_name=region
    )
    my_bucket = s3.Bucket(bkt)
    count_objects = 0
    count_files = 0

    for my_bucket_object in my_bucket.objects.filter(Prefix=f'{album}/', Delimiter='/'):
        count_objects = count_objects + 1
        if my_bucket_object.key.endswith(".jpg") or my_bucket_object.key.endswith(".jpeg"):
            print(my_bucket_object.key.split(f'{album}/')[1])
            count_files = count_files + 1

    if count_objects == 0:
        raise Exception(f"{album} does not exist")
    if count_files == 0:
        raise Exception(f"{album} does not have files")


def delete_album(bkt, aws_access_key, secret, album, endpoint_url, region):
    session = boto3.session.Session()
    s3 = session.resource(
        service_name='s3',
        endpoint_url=endpoint_url,
        aws_access_key_id=aws_access_key,
        aws_secret_access_key=secret,
        region_name=region
    )
    my_bucket = s3.Bucket(bkt)
    try:
        s3.Object(bkt, f'{album}/').get()
        for my_bucket_object in my_bucket.objects.filter(Prefix=f'{album}/'):
            s3.Object(bkt, my_bucket_object.key).delete()
    except:
        raise Exception(f"Album '{album}' does not exist")


def delete_photo_in_album(bkt, aws_access_key, secret, album, photo, endpoint_url, region):
    session = boto3.session.Session()
    s3 = session.resource(
        service_name='s3',
        endpoint_url=endpoint_url,
        aws_access_key_id=aws_access_key,
        aws_secret_access_key=secret,
        region_name=region
    )
    s3.Bucket(bkt)
    try:
        s3.Object(bkt, f'{album}/').get()
    except:
        raise Exception(f"Album '{album}' does not exist")
    try:
        path = f'{album}/{photo}'
        s3.Object(bkt, path).get()
        s3.Object(bkt, path).delete()
    except:
        raise Exception(f"Photo '{photo}' does not exist")


def download_album(bucket, key_id, secret, album, path, endpoint_url, region):
    session = boto3.session.Session()
    s3 = session.client(
        service_name='s3',
        endpoint_url=endpoint_url,
        aws_access_key_id=key_id,
        aws_secret_access_key=secret,
        region_name=region
    )
    path = Path(path)
    if not is_album_exist(s3, bucket, album):
        raise Exception(f"Album {album} does not exist")

    if not path.is_dir():
        raise Exception(f"{str(path)} is not directory")

    list_object = s3.list_objects(Bucket=bucket, Prefix=album + '/', Delimiter='/')
    for key in list_object["Contents"]:
        if not key["Key"].endswith("/"):
            obj = s3.get_object(Bucket=bucket, Key=key["Key"])
            filename = Path(key['Key']).name

            filepath = path / filename
            with filepath.open("wb") as file:
                file.write(obj["Body"].read())


def upload_album(bucket, key_id, secret, album, path, endpoint_url, region):
    session = boto3.session.Session()
    s3 = session.client(
        service_name='s3',
        endpoint_url=endpoint_url,
        aws_access_key_id=key_id,
        aws_secret_access_key=secret,
        region_name=region
    )
    path = Path(path)
    check_album(album)
    count = 0

    if not path.is_dir():
        raise Exception(f"{str(path)} album does not exist")

    if not is_album_exist(s3, bucket, album):
        s3.put_object(Bucket=bucket, Key=(album + '/'))
        print(f"{album} album creating...")

    for file in path.iterdir():
        if is_image(file):
            try:
                print(f"{file.name} photo uploading...")
                key = f"{album}/{file.name}"
                s3.upload_file(str(file), bucket, key)
                count += 1
            except Exception:
                raise Exception(f"{str(path)} got error with uploading")


def is_image(file):
    return file.is_file() and file.suffix in IMG_EXTENSIONS


def get_albums_data(session, bucket: str):
    albums = {}
    list_objects = session.list_objects(Bucket=bucket)
    for key in list_objects["Contents"]:
        album_img = key["Key"].split("/")
        if len(album_img) != 2:
            continue
        album, img = album_img
        if img == '':
            continue
        if album in albums:
            albums[album].append(img)
        else:
            albums[album] = [img]

    return albums


def get_template(name):
    template_path = Path(ROOT_DIRECTORY) / "templates" / name
    with open(template_path, "r") as file:
        return file.read()


def save_temporary_template(template) -> str:
    filename = ''.join(random.choices(string.ascii_letters + string.digits, k=8)) + ".html"
    path = Path(ROOT_DIRECTORY) / "temp" / filename
    if not path.parent.exists():
        os.mkdir(path.parent)

    with open(path, "w") as file:
        file.write(template)

    return str(path)


def remove_temporary_dir():
    path = Path(ROOT_DIRECTORY) / "temp"
    shutil.rmtree(path)


def make_site_album(bucket, key_id, secret, endpoint_url, region):
    session = boto3.session.Session()
    s3 = session.client(
        service_name='s3',
        endpoint_url=endpoint_url,
        aws_access_key_id=key_id,
        aws_secret_access_key=secret,
        region_name=region
    )
    url = f"https://{bucket}.website.yandexcloud.net"
    albums = get_albums_data(s3, bucket)

    template = get_template("album.html")

    albums_rendered = []
    i = 1
    for album, photos in albums.items():
        print(photos)
        template_name = f"album{i}.html"
        rendered_album = Template(template).render(album=album, images=photos, url=url)
        path = save_temporary_template(rendered_album)

        s3.upload_file(path, bucket, template_name)
        albums_rendered.append({"name": template_name, "album": album})
        i += 1

    template = get_template("index.html")
    rendered_index = Template(template).render(template_objects=albums_rendered)
    path = save_temporary_template(rendered_index)
    s3.upload_file(path, bucket, "index.html")

    template = get_template("error.html")
    path = save_temporary_template(template)
    s3.upload_file(path, bucket, "error.html")

    s3.put_bucket_website(Bucket=bucket, WebsiteConfiguration=SITE_CONFIGURATION)
    remove_temporary_dir()
    print(url)


def is_album_exist(session, bucket, album):
    list_objects = session.list_objects(
        Bucket=bucket,
        Prefix=album + '/',
        Delimiter='/',
    )
    if "Contents" in list_objects:
        for _ in list_objects["Contents"]:
            return True
    return False


def check_album(album: str):
    if album.count("/"):
        raise Exception("album cannot contain '/'")


def init(bkt, aws_access_key, secret):
    with fileinput.FileInput(os.path.expanduser(file_path), inplace=True) as file:
        for line in file:
            line = line.replace("INPUT_BUCKET_NAME", bkt)
            line = line.replace("INPUT_AWS_ACCESS_KEY_ID", aws_access_key)
            line = line.replace("INPUT_AWS_SECRET_ACCESS_KEY", secret)
            print(line, end='')
    bucket, key_id, secret, endpoint_url, region = get_params()
    make_bucket(bucket, key_id, secret, endpoint_url, region)


def get_list(album):
    bucket, key_id, secret, endpoint_url, region = get_params()

    if album is None:
        get_albums(bucket, key_id, secret, endpoint_url, region)
    else:
        get_files(bucket, key_id, secret, album, endpoint_url, region)


def delete(album, photo):
    bucket, key_id, secret, endpoint_url, region = get_params()
    if photo is None:
        delete_album(bucket, key_id, secret, album, endpoint_url, region)
    else:
        delete_photo_in_album(bucket, key_id, secret, album, photo, endpoint_url, region)


def download(album, path):
    bucket, key_id, secret, endpoint_url, region = get_params()
    download_album(bucket, key_id, secret, album, path, endpoint_url, region)


def upload(album, path):
    bucket, key_id, secret, endpoint_url, region = get_params()
    upload_album(bucket, key_id, secret, album, path, endpoint_url, region)


def make_site():
    bucket, key_id, secret, endpoint_url, region = get_params()
    make_site_album(bucket, key_id, secret, endpoint_url, region)


def get_params():
    config = {}
    with open(os.path.expanduser(file_path), 'r') as file:
        for line in file:
            name, value = line.strip().split(' = ', 1)
            config[name] = value

    bucket = config['bucket']
    key_id = config['aws_access_key_id']
    secret = config['aws_secret_access_key']
    endpoint_url = config['endpoint_url']
    region = config['region']
    if (bucket == "INPUT_BUCKET_NAME"
            or key_id == "INPUT_AWS_ACCESS_KEY_ID"
            or secret == "INPUT_AWS_SECRET_ACCESS_KEY"):
        raise Exception("Config file is not valid")
    return bucket, key_id, secret, endpoint_url, region


try:
    if args.command == 'init':
        bucket = input('bucket: ')
        aws_access_key_id = input('aws_access_key_id: ')
        aws_secret_access_key = input('aws_secret_access_key: ')
        init(bucket, aws_access_key_id, aws_secret_access_key)
        print("init done\n")
        print("Exit with status 0\n")
        sys.exit(os.EX_OK)
    elif args.command == 'list':
        get_list(args.album)
        print("list done\n")
        print("Exit with status 0\n")
        sys.exit(os.EX_OK)
    elif args.command == 'upload':
        upload(args.album, args.path)
        print("upload done\n")
        print("Exit with status 0\n")
        sys.exit(os.EX_OK)
    elif args.command == 'delete':
        delete(args.album, args.photo)
        print("delete done\n")
        print("Exit with status 0\n")
        sys.exit(os.EX_OK)
    elif args.command == 'download':
        download(args.album, args.path)
        print("dowload done\n")
        print("Exit with status 0\n")
        sys.exit(os.EX_OK)
    elif args.command == 'mksite':
        make_site()
        print("mksite done\n")
        print("Exit with status 0\n")
        sys.exit(os.EX_OK)
except Exception as err:
    print(f"Error: {err}\nExit with status 1")
    print(f"Exit with status 1\n")
    sys.exit(1)
