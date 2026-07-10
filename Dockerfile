FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# System deps + Playwright browsers
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl wget gnupg ca-certificates \
    && curl -fsSL https://deb.playwright.dev/ubuntu-22.04/ppa/ubuntu-archive-keyring.gpg \
       -o /usr/share/keyrings/playwright-archive-keyring.gpg \
    && echo "deb [signed-by=/usr/share/keyrings/playwright-archive-keyring.gpg] https://deb.playwright.dev/ubuntu-22.04/ppa/ stable main" \
       > /etc/apt/sources.list.d/playwright.list \
    && apt-get update && apt-get install -y --no-install-recommends \
       libnss3 libnspr4 libatk1.0-0 libatk-bridge2.0-0 libcups2 libdrm2 \
       libdbus-1-3 libxkbcommon0 libxcomposite1 libxdamage1 libxfixes3 libxrandr2 \
       libgbm1 libpango-1.0-0 libcairo2 libasound2 libatspi2.0-0 fonts-liberation \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install -r requirements.txt

# Install Playwright Chromium
RUN python -m playwright install --with-deps chromium

COPY . .

CMD ["python", "run.py"]
