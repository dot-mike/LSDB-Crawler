FROM python:3

ENV DEBIAN_FRONTEND=noninteractive

EXPOSE 6023

WORKDIR /app

RUN apt update -y && apt install telnet -y

COPY requirements.txt ./

RUN pip3 install --no-cache-dir -r requirements.txt

COPY . .

COPY entrypoint.sh  /
RUN chmod 755 /entrypoint.sh

ENTRYPOINT [ "/entrypoint.sh" ]