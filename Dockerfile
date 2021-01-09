FROM python:3-alpine
WORKDIR /tmp

COPY dist/poker*.whl /tmp/poker-0.30.2-py3-none-any.whl

RUN pip install /tmp/poker-0.30.2-py3-none-any.whl
