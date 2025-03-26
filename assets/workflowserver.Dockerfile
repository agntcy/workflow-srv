# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

FROM python:3.12

ENV POETRY_VERSION=2.1.1

RUN set -ex; pip install --trusted-host pypi.org --trusted-host pypi.python.org --trusted-host files.pythonhosted.org poetry==$POETRY_VERSION;

WORKDIR /opt/agent-workflow-server

COPY . .

RUN poetry config virtualenvs.create true
RUN poetry config virtualenvs.in-project true
RUN poetry install --no-interaction

EXPOSE 8000

CMD ["poetry" ,"run", "server"]
