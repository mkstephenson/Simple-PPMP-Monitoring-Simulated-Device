FROM python:3-alpine
RUN apk add git
RUN git clone https://github.com/eclipse/unide.python.git
RUN cd unide.python && python setup.py install
ADD run.py /
RUN pip install requests-futures
CMD [ "python", "./run.py", "-c", "options.ini" ]