.PHONY: install migrate test run demo-check

install:
	python -m pip install -r requirements.txt

migrate:
	python manage.py makemigrations analysis
	python manage.py migrate

test:
	python manage.py test

run:
	python manage.py runserver 0.0.0.0:3000

demo-check:
	python manage.py check
	python manage.py test
