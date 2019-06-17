# !/bin/sh
#
#

# set -e

keystone_group='keystone'
controller_server_name='controller'

cd /
echo -e "# This is the default ansible 'hosts' file.\n#\n# It should live in /etc/ansible/hosts\n\nlocalhost ansible_connection=local" > /etc/ansible/hosts
/bin/sh -c "ansible-playbook playbook.yml"

echo "Populating the Identity service database"
/bin/sh -c "keystone-manage db_sync" "${DATABASE_NAME}"

echo "Initializing Fernet key repositories"
`keystone-manage fernet_setup --keystone-user ${DB_USER} --keystone-group "${keystone_group}"`
`keystone-manage credential_setup --keystone-user ${DB_USER} --keystone-group "${keystone_group}"`

echo "Bootstraping the Identity service"
`keystone-manage bootstrap --bootstrap-password ${USER_PASSWD} --bootstrap-admin-url http://${controller_server_name}:35357/v3/ --bootstrap-internal-url http://${controller_server_name}:35357/v3/ --bootstrap-public-url http://${controller_server_name}:5000/v3/ --bootstrap-region-id RegionOne`

echo "Updating Apache2 conf file"
echo "ServerName ${controller_server_name}" >> /etc/apache2/apache2.conf

#echo "Restarting Apache server"
/etc/init.d/apache2 restart

