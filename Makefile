coverage:
	python -m pytest --cov=app/services --cov-branch --cov-fail-under=100
	python -m pytest --cov=app --cov-branch --cov-fail-under=80
