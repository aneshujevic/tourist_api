FROM postgres

ENV POSTGRES_PASSWORD=postgres_secret_passwd
ENV POSTGRES_USER=postgres_secret_user

VOLUME ["/data/postgresql"]

COPY *.sql /docker-entrypoint-initdb.d/
