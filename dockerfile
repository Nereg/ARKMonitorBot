FROM python:3.7.4
WORKDIR /app
# copy everything (except what in .dockerignore file)
COPY . /app/
# install menus extension because it is beta 
RUN pip install -U git+https://github.com/Rapptz/discord-ext-menus
# installing all needed stuff
RUN pip install --no-cache-dir -r requirements.txt
# migrating (if db file is not present or not formated as needed it will create it)
#RUN python3 /app/src/migration.py

# and FIRE IT UP ! 
CMD ["./wait-for-it.sh", "--timeout=60" , "db:3306", "--", "python3", "/app/src/main.py"]