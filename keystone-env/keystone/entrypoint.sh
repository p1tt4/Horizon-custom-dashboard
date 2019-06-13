# !/bin/sh
#
#

# set -e

keystone_group='keystone'
keystone_url='http://controller:5000/v3/'

cd /
echo -e "# This is the default ansible 'hosts' file.\n#\n# It should live in /etc/ansible/hosts\n\nlocalhost ansible_connection=local" > /etc/ansible/hosts
/bin/sh -c "ansible-playbook playbook.yml"

echo "Populating the Identity service database"
/bin/sh -c "keystone-manage db_sync" "${DATABASE_NAME}"

echo "Initializing Fernet key repositories"
`keystone-manage fernet_setup --keystone-user ${DB_USER} --keystone-group "${keystone_group}"`
`keystone-manage credential_setup --keystone-user ${DB_USER} --keystone-group "${keystone_group}"`

echo "Bootstraping the Identity service"
`keystone-manage bootstrap --bootstrap-password ${USER_PASSWD} --bootstrap-admin-url "${keystone_url}" --bootstrap-internal-url "${keystone_url}" --bootstrap-public-url "${keystone_url}" --bootstrap-region-id RegionOne`

echo Updating Apache2 conf file
echo "ServerName controller" >> /etc/apache2/apache2.conf

echo "Setting env variables"
export OS_USERNAME=admin
export OS_PASSWORD=secret
export OS_PROJECT_NAME=admin
export OS_USER_DOMAIN_NAME=Default
export OS_PROJECT_DOMAIN_NAME=Default
export OS_AUTH_URL=http://controller:5000/v3
export OS_IDENTITY_API_VERSION=3

#echo "Restarting Apache server"
/etc/init.d/apache2 restart

