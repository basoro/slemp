# =======================
# Makefile
# =======================
.PHONY: build up down restart shell logs supervisorctl

build:
	docker-compose build

up:
	docker-compose up -d

down:
	docker-compose down

restart:
	docker-compose restart

shell:
	docker exec -it fullstack_slemp bash

logs:
	docker-compose logs -f

supervisorctl:
	docker exec -it fullstack_slemp supervisorctl $(filter-out $@,$(MAKECMDGOALS))

# Usage:
# make supervisorctl start nginx
# make supervisorctl stop mariadb
# make supervisorctl status
# make supervisorctl reread
# make supervisorctl update
