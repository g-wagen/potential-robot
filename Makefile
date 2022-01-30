# Makefile
# -----------------------------------------------------------------------------

# LOOK FOR .env FILE
# -----------------------------------------------------------------------------
ifneq (,$(wildcard ./.env))
    include .env
    export
endif


# ----------------------------------
#          INSTALL & TEST
# ----------------------------------
install_requirements:
	@pip install -r requirements.txt

check_code:
	@flake8 scripts/* potential-robot/*.py

black:
	@black scripts/* potential-robot/*.py

test:
	@coverage run -m pytest tests/*.py
	@coverage report -m --omit="${VIRTUAL_ENV}/lib/python*"

ftest:
	@Write me

clean:
	@rm -f */version.txt
	@rm -f .coverage
	@rm -fr */__pycache__ */*.pyc __pycache__
	@rm -fr build dist
	@rm -fr potential-robot-*.dist-info
	@rm -fr potential-robot.egg-info

install:
	@pip install . -U

all: clean install test black check_code

count_lines:
	@find ./ -name '*.py' -exec  wc -l {} \; | sort -n| awk \
        '{printf "%4s %s\n", $$1, $$2}{s+=$$0}END{print s}'
	@echo ''
	@find ./scripts -name '*-*' -exec  wc -l {} \; | sort -n| awk \
		        '{printf "%4s %s\n", $$1, $$2}{s+=$$0}END{print s}'
	@echo ''
	@find ./tests -name '*.py' -exec  wc -l {} \; | sort -n| awk \
        '{printf "%4s %s\n", $$1, $$2}{s+=$$0}END{print s}'
	@echo ''


# ----------------------------------
#      UPLOAD PACKAGE TO PYPI
# ----------------------------------
PYPI_USERNAME=<AUTHOR>
build:
	@python setup.py sdist bdist_wheel

pypi_test:
	@twine upload -r testpypi dist/* -u $(PYPI_USERNAME)

pypi:
	@twine upload dist/* -u $(PYPI_USERNAME)


# ----------------------------------
#      DOCKER AND DATABASES
# ----------------------------------
datalake_container = ${LAKE_NAME}-mysql
datalake_volume = ${LAKE_NAME}-vol
datalake_ports = ${LAKE_PORT_EXTERN}:${LAKE_PORT_INTERN}

datawarehouse_container = ${WAREHOUSE_NAME}-mysql
datawarehouse_volume = ${WAREHOUSE_NAME}-vol
datawarehouse_ports = ${WAREHOUSE_PORT_EXTERN}:${WAREHOUSE_PORT_INTERN}

mysql_loc = /var/lib/mysql

# Deploy the docker containers
# ----------------------------------
deploy_datalake :
	@echo "\nCreating Datalake Docker Volume ... "
	@docker volume create ${datalake_volume}
	@echo "\nCreating Datalake Docker Container ... "
	@docker run --name ${datalake_container} \
	-v ${datalake_volume}:${mysql_loc} \
	-p ${datalake_ports} \
	-e MYSQL_ROOT_PASSWORD=${LAKE_ROOT_PW} \
	-e MYSQL_DATABASE=${LAKE_NAME} \
	-e MYSQL_USER=${DATA_LAKE_USER} \
	-e MYSQL_PASSWORD=${LAKE_USER_PW} \
	-d mysql:8.0

deploy_datawarehouse :
	@echo "\nCreating Warehouse Docker Volume ... "
	@docker volume create ${datawarehouse_container}
	@echo "\nCreating Warehouse Docker Container ... "
	@docker run --name ${datawarehouse_container} \
	-v ${datawarehouse_volume}:${mysql_loc} \
	-p ${datawarehouse_ports} \
	-e MYSQL_ROOT_PASSWORD=${WAREHOUSE_ROOT_PW} \
	-e MYSQL_DATABASE=${WAREHOUSE_NAME} \
	-e MYSQL_USER=${WAREHOUSE_USER} \
	-e MYSQL_PASSWORD=${WAREHOUSE_USER_PW} \
	-d mysql:8.0

deploy_databases : deploy_datalake deploy_datawarehouse


# Start the docker containers in case they aren't running
# ----------------------------------
start_datalake :
	@echo "\nStarting Datalake Container ... "
	@docker container start ${datalake_container}

start_datawarehouse :
	@echo "\nStarting Datawarehouse Container ... "
	@docker container start ${datawarehouse_container}

start_databases : start_datalake start_datawarehouse


# Stop the running containers
# ----------------------------------
stop_datalake :
	@echo "\nStopping Datalake Container ... "
	@docker container stop ${datalake_container}

stop_datawarehouse :
	@echo "\nStopping Datawarehouse Container ... "
	@docker container stop ${datawarehouse_container}

stop_databases : stop_datalake stop_datawarehouse


# Log-in to the mysql databases of the containers
# ----------------------------------
login_mysql_datalake:
	@docker exec -it ${datalake_container} \
	mysql -u ${LAKE_USER} --password=${LAKE_USER_PW}

login_mysql_datawarehouse:
	@docker exec -it ${datawarehouse_container} \
	mysql -u ${WAREHOUSE_USER} --password=${WAREHOUSE_USER_PW}


# Destroy the docker containers and all their data forever
# ----------------------------------
destroy_datalake : \
	stop_datalake
	@echo "\nDeleting Datalake Container ... "
	@docker container rm ${datalake_container}
	@echo "\nRemoving Datalake Container Volume ... "
	@docker volume rm ${datalake_volume}

destroy_datawarehouse : \
	stop_datawarehouse
	@echo "\nDeleting Datawarehouse Container ... "
	@docker container rm ${datawarehouse_container}
	@echo "\nRemoving Datawarehouse Container Volume ... "
	@docker volume rm ${datawarehouse_volume}

destroy_databases : destroy_datalake destroy_datawarehouse
