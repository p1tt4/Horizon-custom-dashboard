# !/bin/bash
#
#
dash_name=$1
panel_name=${2:-'first_panel'}

if [ -z "$dash_name" ]; then
	echo "Error: please provide a dashboard name"
	exit 1
fi

if [ -z $(which tox) ]; then
	echo "Tox executable is not installed"
	pip install tox
fi	
root_dir=$(pwd)
branch='stable/pike'

cd "$root_dir"/horizon
# create an empty dashboard directory
mkdir -p openstack_dashboard/dashboards/"${dash_name}"
# populate the new dashboad directory
tox -evenv -- startdash "${dash_name}" --target openstack_dashboard/dashboards/"$dash_name"

#tox -e venv -- startdash "$dash_name" --target openstack_dashboard/dashboards/"$dash_name"
# create a new panel's directory
mkdir -p openstack_dashboard/dashboards/"${dash_name}"/"${panel_name}"
# populate the new panel directory
tox -evenv -- startpanel "${panel_name}" --dashboard=openstack_dashboard.dashboards."${dash_name}" --target=openstack_dashboard/dashboards/"${dash_name}"/"${panel_name}"


