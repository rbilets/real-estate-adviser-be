FROM mcr.microsoft.com/azure-functions/python:4-python3.10

RUN apt-get update && \
    apt-get install -y build-essential

# Download and install unixodbc 2.3.12. See README.md.
RUN curl -sO https://www.unixodbc.org/unixODBC-2.3.12.tar.gz && \
    gunzip unixODBC*.tar.gz && \
    tar xvf unixODBC*.tar && \
    cd unixODBC-2.3.12 && \
    ./configure && \
    make && \
    make install && \
    cd .. && \
    rm -rf unixODBC-2.3.12

# Install dependencies of msodbcsql18 except unixodbc and then install msodbcsql18 ignoring unixodbc dependency.
RUN apt-get update && \
    apt-get install -y libc6 libstdc++6 libkrb5-3 openssl debconf odbcinst && \
    curl -s https://packages.microsoft.com/keys/microsoft.asc | tee /etc/apt/trusted.gpg.d/microsoft.asc && \
    curl -s https://packages.microsoft.com/config/debian/11/prod.list | tee /etc/apt/sources.list.d/mssql-release.list && \
    apt-get download msodbcsql18 && \
    dpkg --ignore-depends=unixodbc -i msodbcsql18*.deb

RUN pip install --upgrade pip && \
    pip install --no-cache-dir poetry && \
    poetry config virtualenvs.create false

WORKDIR /home/site/wwwroot

COPY poetry.lock pyproject.toml ./

# Allow installing dev dependencies to run tests
ARG INSTALL_DEV=false
RUN bash -c "if [ $INSTALL_DEV == 'true' ] ; then poetry install --no-root ; else poetry install --no-root --no-dev ; fi"

COPY real_estate_adviser_service /home/site/wwwroot/

# Further steps under user "app". Add user and set permissions for its home directory.
RUN useradd -m -d /home/site/wwwroot -s /bin/bash app && \
    chown -R app:app /home/site/wwwroot/* && \
    chmod -R 755 /home/site/wwwroot
USER app

EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--log-level", "info"]
