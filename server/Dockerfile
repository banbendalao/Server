FROM python:3.9-slim

#[1/2]本地调试默认源太慢，使用科大源，调试时可以取消注释。
RUN sed -i 's#deb.debian.org#opentuna.cn#g' /etc/apt/sources.list

#[2/2]本地调试Pip默认源太慢，使用清华源，调试时可以取消注释。
# RUN pip install -i https://opentuna.cn/pypi/web/simple pip -U
RUN pip config set global.index-url https://opentuna.cn/pypi/web/simple

COPY ./app/requirements.txt ./
COPY ./oci_build/DockerfileRUN.sh ./
RUN ./DockerfileRUN.sh && rm ./DockerfileRUN.sh
COPY ./boot_container.sh ./
COPY ./app ./app
COPY ./config.ini ./
COPY ./uwsgi.ini ./

ENTRYPOINT [ "bash", "./boot_container.sh" ]
