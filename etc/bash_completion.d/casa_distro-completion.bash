#/usr/bin/env bash

function _complete_casa_distro_()
{
    local word=${COMP_WORDS[COMP_CWORD]}
    local line=${COMP_LINE}
    local cmd_list="help create list update update_image shell run mrun bv_maker create_writable_image root_shell"
    local opt_list="-r -h -v --version"

    case "$COMP_CWORD" in
    1)
        COMPREPLY=($(compgen -W "$cmd_list $opt_list" -- "${word}"))
        ;;
    *)
        local cmd=${COMP_WORDS[1]}

        case "$cmd" in
        help)
            COMPREPLY=($(compgen -W "$cmd_list" -- "${word}"))
            ;;
        bv_maker)
            COMPREPLY=($(compgen -W "distro= branch= system= build_workflows_repository= gui= interactive= tmp_container= container_image= cwd= env= container_options= args_list= verbose= conf=" -- "${word}"))
            ;;
        create)
            COMPREPLY=($(compgen -W "distro_source= distro_name= container_type= container_image= container_test_image= branch= system= not_override= build_workflows_repository= verbose=" -- "${word}"))
            ;;
        create_writable_image)
            COMPREPLY=($(compgen -W "singularity_image= distro= branch= system= build_workflows_repository= verbose=" -- "${word}"))
            ;;
        list)
            COMPREPLY=($(compgen -W "distro= branch= system= build_workflows_repository= verbose=" -- "${word}"))
            ;;
        mrun)
            COMPREPLY=($(compgen -W "distro= branch= system= build_workflows_repository= gui= interactive= tmp_container= container_image= cwd= env= container_options= args_list= verbose= conf=" -- "${word}"))
            ;;
        root_shell)
            COMPREPLY=($(compgen -W "singularity_image= distro= branch= system= build_workflows_repository= verbose=" -- "${word}"))
            ;;
        run)
            COMPREPLY=($(compgen -W "distro= branch= system= build_workflows_repository= gui= interactive= tmp_container= container_image= cwd= env= container_options= args_list= verbose= conf=" -- "${word}"))
            ;;
        shell)
            COMPREPLY=($(compgen -W "distro= branch= system= build_workflows_repository= gui= interactive= tmp_container= container_image= cwd= env= container_options= args_list= verbose= conf=" -- "${word}"))
            ;;
        update)
            COMPREPLY=($(compgen -W "distro= branch= system= build_workflows_repository= verbose=" -- "${word}"))
            ;;
        update_image)
            COMPREPLY=($(compgen -W "distro= branch= system= build_workflows_repository= verbose=" -- "${word}"))
            ;;
        esac
        ;;
    esac

    if [ -z "$COMPREPLY" ]; then
        COMPREPLY=($(compgen -f -- "${word}"))
    fi
}

# complete -W "help create list update update_image shell run mrun bv_maker create_writable_image root_shell" casa_distro
complete -W "help package_casa_distro publish_casa_distro create_release_plan update_release_plan html_release_plan create_latest_release create_docker update_docker publish_docker create_singularity publish_singularity publish_build_workflows" casa_distro_admin

complete -F _complete_casa_distro_ casa_distro
