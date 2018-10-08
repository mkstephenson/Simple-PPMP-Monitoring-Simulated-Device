FROM python:3.7-alpine
WORKDIR /usr/src/app
RUN pip install --no-cache-dir unide-python
RUN pip install --no-cache-dir requests-futures
COPY . .
CMD [ "python", "./run.py" ]
