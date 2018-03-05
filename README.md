# python-getting-started

A barebones Python app, which can easily be deployed to Heroku.

This application supports the [Getting Started with Python on Heroku](https://devcenter.heroku.com/articles/getting-started-with-python) article - check it out.

## Stress-Testing
Install Siege using `brew install siege`
I use the following scripts:
```sh
$ siege -c 100 -r 10 http://localhost:8000/ics/tasks/simple/?team=1
$ siege -c 100 -r 10 http://localhost:8000/ics/tasks/9012/
$ siege -c 100 -r 10 http://localhost:8000/ics/tasks/search/?team=1&is_open=false
```
In these tests, we vary `-c` and `-r`, which represent the number of concurrent users and requests per user, respectively. To simulate a high-traffic scenario, we typically bring `-c` to 100, and vary `-r` between 5 and 10. To simulate a high-volume scenario, we typically bring `-c` to 10, and bring `-r` to 100. To simulate a high-pressure (high-traffic and high volume), we typically bring `-c` to 100 and `-r` to 50. 

## Running Locally

Make sure you have Python [installed properly](http://install.python-guide.org).  Also, install the [Heroku Toolbelt](https://toolbelt.heroku.com/) and [Postgres](https://devcenter.heroku.com/articles/heroku-postgresql#local-setup).

```sh
$ git clone git@github.com:heroku/python-getting-started.git
$ cd python-getting-started

$ pip install -r requirements.txt

$ createdb python_getting_started

$ python manage.py migrate
$ python manage.py collectstatic

$ heroku local
```

Your app should now be running on [localhost:5000](http://localhost:5000/).

## Deploying to Heroku

```sh
$ heroku create
$ git push heroku master

$ heroku run python manage.py migrate
$ heroku open
```
or

[![Deploy](https://www.herokucdn.com/deploy/button.png)](https://heroku.com/deploy)

## Documentation

For more information about using Python on Heroku, see these Dev Center articles:

- [Python on Heroku](https://devcenter.heroku.com/categories/python)
