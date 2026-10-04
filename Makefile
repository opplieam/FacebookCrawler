PW_IMAGE := mcr.microsoft.com/playwright:v1.63.0-noble
PW_VERSION := 1.63.0
PW_PORT := 3000
PW_NAME := pw-server

FB_EMAIL ?=
FB_PASSWORD ?=
FB_PAGE_ID ?=
FB_OUTPUT ?= fb.json

.PHONY: pw-server-up pw-server-logs pw-server-down install check crawl freeze auth

auth:
	python save_auth.py

pw-server-up:
	docker run -d -p $(PW_PORT):3000 --name $(PW_NAME) --ipc=host \
		$(PW_IMAGE) /bin/sh -c "npx -y playwright@$(PW_VERSION) run-server --port 3000 --host 0.0.0.0"

pw-server-logs:
	docker logs -f $(PW_NAME)

pw-server-down:
	docker stop $(PW_NAME)
	docker rm $(PW_NAME)

install:
	pip install -r requirement.text

check:
	scrapy check

crawl:
	scrapy crawl fb_page -a page_id="$(FB_PAGE_ID)" -o $(FB_OUTPUT)

freeze:
	pip freeze > requirement.text
