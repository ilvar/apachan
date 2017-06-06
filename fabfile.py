#!/bin/env python

# sudo easy_install fabric

from fabric.api import local, cd, run, hosts, sudo

@hosts('root@apachan.org')
def deploy():
    local('git pull')
    local('git push')
    with cd('/home/agurin/new.apachan.net/apachan/'):
        sudo('git pull', user='agurin')
        sudo('../ENV/bin/pip install -r requirements.txt', user='agurin')
        sudo('../ENV/bin/python ./manage.py migrate', user='agurin')
        sudo('../ENV/bin/python ./manage.py collectstatic --noinput', user='agurin')

        run('supervisorctl restart apachan')

@hosts('root@apachan.org')
def deploy_nginx():
    local('git pull')
    local('git push')

    with cd('/home/agurin/new.apachan.net/apachan/'):
        sudo('git pull', user='agurin')

    run('cp /home/agurin/new.apachan.net/apachan/conf/nginx.conf /etc/nginx/sites-enabled/apachan.net.conf')
    run('nginx -T')
    run('service nginx restart')
