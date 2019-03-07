.PHONE: run build clean

clean:
	docker-compose rm -fsv

build:
	docker-compose build
run:
	docker-compose up