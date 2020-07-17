FROM python:3.7.4
WORKDIR /app
# copy everything (except what in .dockerignore file)
COPY . /app/
# add excution permissions for wait-for-it.sh 
RUN chmod +x wait-for-it.sh
# installing all needed stuff
RUN pip install --no-cache-dir -r requirements.txt

# and FIRE IT UP ! 
CMD ["./wait-for-it.sh", "--timeout=60" , "db:3306", "--", "python3", "/app/src/main.py"]