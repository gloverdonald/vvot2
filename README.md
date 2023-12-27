### Столповский Михаил 11-002

Сделать конфиг вида: 
```text
bucket = INPUT_BUCKET_NAME 
aws_access_key_id = INPUT_AWS_ACCESS_KEY_ID 
aws_secret_access_key = INPUT_AWS_SECRET_ACCESS_KEY 
region = ru-central1 
endpoint_url = https://storage.yandexcloud.net 
```

по пути ```.config/cloudphoto/cloudphotorc```

```bash
pip install -r requirements.txt
python cloudphoto.py [-h] {upload, download, list, delete, mksite, init}
```

