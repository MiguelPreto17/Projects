## Rest API

### How to use

```
cd web-application

```

With Docker:

```
docker-compose build rest-api
docker-compose up -d rest-api

```

Without Docker:

```
pip install -r requirements.txt
uvicorn Api:app --reload --port 3006
```
