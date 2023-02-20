FROM python:3

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt -vvv

COPY . .

#CMD ["sleep", "9999999999"]
CMD [ "python", "./main.py" ]