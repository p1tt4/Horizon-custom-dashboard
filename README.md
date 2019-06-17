# Simple Horizon dashboard

Horizon, the OpenStack web user interface, allows developers to integrate new components. This repository holds code of a simple extension of <a href="https://docs.openstack.org/horizon/latest/">Horizon</a>, which itself is based on <a href="https://docs.djangoproject.com">Django</a>. This dashboard allows a user to create and schedule backup jobs orchestrated by Mistral, and works only if integrated within Horizon.

Two steps are required to make it work:
<ol>
	<li> setup the dockerized keystone environment </li>
	<li> download Horizon and Mistral repositories and install those repositories </li>
</ol>

### Setup Keystone identity service

Move inside directory `keystone-env`. First initialize the database service, by running

```
docker-compose up [db name]
```

and wait for ```ready for connections``` line

```
keystone-db   | 
keystone-db   | 
keystone-db   | MySQL init process done. Ready for start up.
keystone-db   | 
keystone-db   | 2019-06-17  9:39:47 0 [Note] mysqld (mysqld 10.3.14-MariaDB-1:10.3.14+maria~bionic) starting as process 1 ...
keystone-db   | 2019-06-17  9:39:47 0 [Note] InnoDB: Using Linux native AIO
keystone-db   | 2019-06-17  9:39:48 0 [Note] Reading of all Master_info entries succeded
keystone-db   | 2019-06-17  9:39:48 0 [Note] Added new Master_info '' to hash table
keystone-db   | 2019-06-17  9:39:48 0 [Note] mysqld: ready for connections.
keystone-db   | Version: '10.3.14-MariaDB-1:10.3.14+maria~bionic'  socket: '/var/run/mysqld/mysqld.sock'  port: 3306  mariadb.org binary distribution
```

then `Ctrl+C` and lift up all the containers, respectively the Keystone container, the database and a simple *memcached* component listening on port 11211, with `docker-compose up -d`.

The keystone container is built from a Dockerfile. During the process of image building, docker copies a bash script to the filesystem root `/` and an Ansible playbook. I wrote this playbook to automate some steps which otherwise would have to be executed manually.


### Install Horizon, Mistral

Launch the script `source setup_horizon_mistral.sh`. The reason behind using the bash builtin `source`, is that the script, among other tasks, activates the virtualenv, which should be run within the same context.
After donwloading the repositories (mind that Horizon repo is 1GB large), installing dependencies the two dashboards, this one and Mistral, are enabled, so that Horizon can load them when executed. The `tox -evenv python manage.py migrate` populates the database with the initial Django tables.


