.PHONE: run build clean test build-test

clean: clean
	docker-compose rm -fsv
	rm -rf __pycache__

build:
	docker-compose build
run:
	docker-compose up

test:
	docker-compose -f docker-compose.yml -f docker-compose.test.yml run test

build-test: clean
	docker-compose -f docker-compose.yml -f docker-compose.test.yml build test