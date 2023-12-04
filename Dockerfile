FROM python:3.10.10-buster

WORKDIR /code

COPY ./requirements.txt /code

COPY . /code

RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

CMD ["uvicorn", "Api:app", "--proxy-headers", "--reload", "--workers", "1", "--host", "0.0.0.0", "--port", "3006"]
