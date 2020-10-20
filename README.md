# sciexpem

This prototype has been developed within the work for the paper
"Towards a scientific data framework to support scientific model development". The prototype contains a set of fully working features but also partially developed features and demo features. The main goal of this prototype was to better elicitate and refine the use cases and the requirements described in the paper.
This software is under active development and can not be considered stable for any usage.

Under the data folder there is a set of data examples.

### System requirements

Python >= 3.6.7

PostgreSQL >= 10.6

### Backend requirements

requirements.txt

### Frontend requirements

The frontend is already compiled in frontend/static/frontend/

If you want to edit and compile it, please install npm >= 5.60
and the requirements in package.json with `npm install`

### Configure the database

Update the settings under the DATABASES entry in settings.py

Only the postgresq engine is supported

Run

`python manage.py makemigrations experimentmanager`

`python manage.py makemigrations`

`python manage.py migrate`

### Import experiments

You can download experiments in the ReSpecTh format from http://respecth.hu/. To import them:

run the script 

`PYTHONPATH=/root/project/ python import_respecth.py --path <experiment-root>`

and then run the automatic fixes which are provided as a Django management command

`python manage.py execute_experiment_tweaks`

### Execute

You can launch the Django server with
`python manage.py runserver`
or host it in another server such as Apache. See: https://docs.djangoproject.com/en/2.1/howto/deployment/wsgi/modwsgi/

