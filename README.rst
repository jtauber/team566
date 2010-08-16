======================================
Manoria by Team 566 at DjangoDash 2010
======================================

Manoria is an MMO city-building and resource management game by Team 566 built
for DjangoDash 2010. DjangoDash 2010 is a Django coding competition to build a
website in 48 hours.

Gameplay
=========

Players are located on a single continent and build settlements that progress
through homestead, hamlet, village and town. Settlers gather resources such as
wood, stone, iron, fish, wheat and gold by constructing buildings adjacent to
certain terrain types.

Implementation
==============

Details of terrain types, building types and resource types and the 
relationship between them is entirely stored in the database so game mechanics
can be developed and adjusted easily.

The implementation features draggable maps and asynchronous updates of
resource counts.



Installation
============

The tools we used to setup/run Manoria are:

 * Python 2.6
 * virtualenv 1.4.7+

Setting up environment
----------------------

Create a virtual environment where manoria dependencies will live::

    $ virtualenv --no-site-packages manoria
    $ source manoria/bin/activate
    (manoria)$

Install manoria project dependencies::

    (manoria)$ pip install -r requirements/project.txt

Setting up the database
-----------------------

By default the project is set up to run on a SQLite database. Run::

    (manoria)$ python manage.py syncdb --noinput

This will load the initial_data fixtures which will be the basis for game-play.
Setup an account in-game (if you want to access the admin you can run
createsuperuser if you like).

Running a web server
--------------------

Run::

    (manoria)$ python manage.py runserver 8006

We used port 8806 and the initial data fixtures rely on it. Not sure if it
really matters, but worth pointing out.

Also, we ran using Safari 5 and did not test other browsers. Would be best to
run in Safari 5.
