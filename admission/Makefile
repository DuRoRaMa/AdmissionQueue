ifdef OS
	py = ../.venv/Scripts/python.exe
else
	py = python
endif

manage = ./manage.py

run.server.prod:
	daphne -b 0.0.0.0 -p 8000 admission.asgi:application

run.server.local:
	$(py) $(manage) runserver

run.bot:
	$(py) -m bot

run.rqworker:
	$(py) $(manage) rqworker default --with-scheduler

manage:
	$(py) $(manage) $(ARGS)

shell:
	$(py) $(manage) shell

collectstatic:
	$(py) $(manage) collectstatic --no-input

migrate:
	$(py) $(manage) migrate

makemigrations:
	$(py) $(manage) makemigrations

createsuperuser:
	$(py) $(manage) createsuperuser --email "" --username admin
