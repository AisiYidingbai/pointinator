FROM --platform=linux/amd64 ubuntu:latest

WORKDIR /
SHELL ["/bin/bash", "-c"]

RUN apt-get update && \
  apt-get install --no-install-recommends -y \
  python3 python3-pip git g++ ca-certificates && \
  git clone https://github.com/AisiYidingbai/pointinator.git && \
  python3 -m pip install --break-system-packages -r /pointinator/requirements.txt

VOLUME /pointinator
WORKDIR /pointinator

CMD ["python3", "pointinator.py", "-o", "/pointinator"]
