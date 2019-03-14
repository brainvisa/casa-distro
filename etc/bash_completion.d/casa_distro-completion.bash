#/usr/bin/env bash
complete -W "help create list update update_image shell run mrun bv_maker create_writable_image root_shell" casa_distro
complete -W "help package_casa_distro publish_casa_distro create_release_plan update_release_plan html_release_plan create_latest_release create_docker update_docker publish_docker create_singularity publish_singularity publish_build_workflows" casa_distro_admin
