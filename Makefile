ifdef OS
	py = ./.venv/Scripts/python.exe
else
	py = python
endif

manage = ./admission/manage.py

run.server.prod:
	daphne -b 0.0.0.0 -p 8000 admission.asgi:application

collectstatic:
	$(py) $(manage) collectstatic --no-input

migrate:
	$(py) $(manage) migrate

run.bot:
	$(py) -m bot

run.server.local:
	$(py) $(manage) runserver

run.bot.local:
	$(py) -m bot

makemigrations:
	$(py) $(manage) makemigrations

createsuperuser:
	$(py) $(manage) createsuperuser --email "" --username admin
