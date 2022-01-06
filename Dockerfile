FROM python:3.10.1-alpine

WORKDIR /python-docker

## add user
RUN adduser -D user
RUN chown -R user:user /python-docker && chmod -R 755 /python-docker

RUN apk update && \
    apk add --virtual build-deps gcc  musl-dev && \
    apk add postgresql-dev

RUN pip3 install --upgrade pip
COPY flask-docker/requirements.txt requirements.txt
RUN pip3 install -r requirements.txt

COPY . .

RUN chmod +x ./flask-docker/init_setup.sh

USER user

ENTRYPOINT ./flask-docker/init_setup.sh
