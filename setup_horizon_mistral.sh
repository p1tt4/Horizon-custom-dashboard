# !/bin/bash
#
# These are the steps that I followed to setup a local environment to
# develop a new Horizon dashboard, based on Mistral
#
# Run this script with `source` command ==> source setup_horizon_mistral.sh
#


base=$(pwd)
virtual_env='pyenv'
horizon_dir="${base}/horizon"
mistral_dir="${base}/mistral-dashboard"
horizon_git='https://github.com/openstack/horizon.git'
mistral_git='https://github.com/openstack/mistral-dashboard.git'
branch='stable/pike'
manage_py='tox -evenv python manage.py'
enabled_file='_50_custom_backup.py'


err() {
    echo "[$(date +'%Y-%m-%dT%H:%M:%S%z')]: $@" >&2
}

log() {
    echo "[$(date +'%Y-%m-%dT%H:%M:%S%z')]: $@" >&1
}

install_venv() {
    if [[ ! -d "${virtual_env}" ]]; then
		log "Installing Python virtual environment"
		virtualenv "${virtual_env}"
    fi
}

enable_custom_dashboard() {
    log "Enabling dashboard"
    echo "# The name of the dashboard to be added to HORIZON['dashboards']
DASHBOARD = 'custom_backup'
# If set to True, this dashboard will not be added to the settings
DISABLED = False
" > "${horizon_dir}/openstack_dashboard/enabled/${enabled_file}"
}

enable_mistral_dashboard() {
    log "Enabling Mistral"
    cp -b "${mistral_dir}/mistraldashboard/enabled/_50_mistral.py" "${horizon_dir}/openstack_dashboard/local/enabled/_50_mistral.py"
    cp -b "${mistral_dir}/mistraldashboard/enabled/_50_mistral.py" "${horizon_dir}/openstack_dashboard/enabled/_50_mistral.py"
}

install_tox() {
	pip install tox
}

update_requirements() {
    log "Updating requirements file"
    echo "
python-memcached==1.58
mysqlclient==1.4.2
-e ../mistral-dashboard/
" >> requirements.txt
}

main() {
    log "Bootstraping..."

    install_venv
    . "${virtual_env}/bin/activate"

    # TODO temporary IF test. To be removed 
    [[ ! -d "${horizon_dir}" ]] && git clone "${horizon_git}" -b "${branch}"
    [[ ! -d "${mistral_dir}" ]] && git clone "${mistral_git}" -b "${branch}"

    cp -r local_settings.py "${horizon_dir}/openstack_dashboard/local/"
    cp -r custom_backup "${horizon_dir}/openstack_dashboard/dashboards"

    cd "${horizon_dir}"
    update_requirements
	install_tox
    enable_custom_dashboard
    enable_mistral_dashboard

    tox -evenv python manage.py migrate
    tox -evenv python manage.py runserver

}


main "$@"



