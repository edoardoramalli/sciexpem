rm -r ./CurveMatching/migrations
rm -r ./ExperimentManager/migrations
rm -r ./FrontEnd/migrations
rm -r ./OpenSmoke/migrations
rm -r ./ReSpecTh/migrations

rm -r ./staticfiles

###### HANDLE DB
#
#
######

python manage.py makemigrations CurveMatching
python manage.py makemigrations ExperimentManager
python manage.py makemigrations FrontEnd
python manage.py makemigrations OpenSmoke
python manage.py makemigrations ReSpecTh

python manage.py migrate

python manage.py createsuperuser

python manage.py create_groups

python manage.py add_permission_group

python manage.py collectstatic