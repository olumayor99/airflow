# Stage 1: Build Stage
FROM apache/airflow:2.7.3-python3.10 AS builder

USER airflow

# Copy and install Python dependencies
COPY requirements.txt .
RUN pip install -r requirements.txt

# Install Node.js and npm
USER root
RUN apt-get update && \
    apt-get install -y curl && \
    curl -sL https://deb.nodesource.com/setup_20.x | bash - && \
    apt-get install -y nodejs 

RUN apt-get install -y wget
RUN wget -q https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
RUN apt-get install -y ./google-chrome-stable_current_amd64.deb

RUN apt-get update &&\
    apt-get install -yq net-tools gconf-service libasound2 libatk1.0-0 libc6 libcairo2 libcups2 libdbus-1-3 \
    libexpat1 libfontconfig1 libgcc1 libgconf-2-4 libgdk-pixbuf2.0-0 libglib2.0-0 libgtk-3-0 libnspr4 \
    libpango-1.0-0 libpangocairo-1.0-0 libstdc++6 libx11-6 libx11-xcb1 libxcb1 libxcomposite1 \
    libxcursor1 libxdamage1 libxext6 libxfixes3 libxi6 libxrandr2 libxrender1 libxss1 libxtst6 \
    ca-certificates fonts-liberation libappindicator1 libnss3 lsb-release xdg-utils \
    xvfb x11vnc x11-xkb-utils xfonts-100dpi xfonts-75dpi xfonts-scalable xfonts-cyrillic x11-apps 

RUN node -v \
    npm install -g npm@latest


# Install Puppeteer with bundled Chromium
RUN npm install puppeteer@20.7.2

RUN mkdir -p /home/airflow/Downloads/

# Install Chrome using puppeteer's command
#RUN npx puppeteer browsers install chrome
# Allow the airflow user to run commands as root without a password prompt
RUN echo "airflow ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers






