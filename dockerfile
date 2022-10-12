# syntax = docker/dockerfile:experimental
FROM python:3.8
WORKDIR /app
COPY ./requirements.txt /app/
COPY ./wait-for-it.sh /app/
# installing all needed stuff
RUN --mount=type=cache,mode=0755,target=/root/.cache/ \
    pip install -r requirements.txt
# add excution permissions for wait-for-it.sh 
RUN chmod +x wait-for-it.sh
# copy everything (except what in .dockerignore file)
COPY . /app/

EXPOSE 80
# and FIRE IT UP ! 
CMD ["./wait-for-it.sh", "--timeout=60" , "db:3306", "--", "python3", "/app/src/main.py"]