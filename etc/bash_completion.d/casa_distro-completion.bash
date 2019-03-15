#/usr/bin/env bash

function _complete_casa_distro_option_()
{
#     if [ -z "$COMPREPLY" ]; then
        local word=${COMP_WORDS[COMP_CWORD]}
        local opt_n=$(( COMP_CWORD - 2 ))
        local opt=${COMP_WORDS[opt_n]}
    #     echo "opt: $opt / $opt_n / $COMP_CWORD"
    #     echo "word: $word"
        case "$opt" in
        distro|distro_name|distro_source)
            COMPREPLY=($(compgen -W "brainvisa opensource" -- "${word}"))
            ;;
        branch)
            COMPREPLY=($(compgen -W "bug_fix trunk" -- "${word}"))
            ;;
        system)
            COMPREPLY=($(compgen -W "ubuntu-16.04 ubuntu-18.04 ubuntu-14.04 ubuntu-12.04 centos-7.4 windows-7-32 windows-7-64" -- "${word}"))
            ;;
        container_type)
            COMPREPLY=($(compgen -W "singularity docker virtualbox" -- "${word}"))
            ;;
        container_image|container_test_image)
            if [ -z "$CASA_DEFAULT_REPOSITORY" ]; then
                local CASA_DEFAULT_REPOSITORY="$HOME/casa_distro"
            fi
            local images=$CASA_DEFAULT_REPOSITORY/*.simg
            COMPREPLY=($(compgen -W "$images" -- "${word}"))
            ;;
        image_name)
            if [ -z "$CASA_DEFAULT_REPOSITORY" ]; then
                local CASA_DEFAULT_REPOSITORY="$HOME/casa_distro"
            fi
            local images=$CASA_DEFAULT_REPOSITORY/*.simg
            local nimages=""
            for f in $images
            do
                local b=$(basename "$f")
                # TODO: rebuild docker-like replacing _ with /
                nimages="$nimages ${b:0:-5}"
            done
            COMPREPLY=($(compgen -W "$nimages" -- "${word}"))
            ;;
        verbose)
            COMPREPLY=($(compgen -W "0 1 True False" -- "${word}"))
            ;;
        esac
#     fi
}


function _complete_casa_distro_()
{
    local word=${COMP_WORDS[COMP_CWORD]}
    local line=${COMP_LINE}
    local cmd_list="help create list update update_image shell run mrun bv_maker create_writable_image root_shell"
    local opt_list="-r -h -v --version"

    case "$COMP_CWORD" in
    1)
        COMPREPLY=($(compgen -W "$cmd_list $opt_list" -- "${word}"))
        if [ -n "$COMPREPLY" ]; then
            COMPREPLY="$COMPREPLY "
        fi
        ;;
    *)
        local cmd=${COMP_WORDS[1]}

        case "$cmd" in
        help)
            COMPREPLY=($(compgen -W "$cmd_list" -- "${word}"))
            ;;
        bv_maker)
            COMP_WORDS=("${COMP_WORDS[@]:1}")
            COMP_CWORD=$(( COMP_CWORD - 1 ))
            _complete_bv_maker_
#             COMPREPLY=($(compgen -W "distro= branch= system= build_workflows_repository= gui= interactive= tmp_container= container_image= cwd= env= container_options= args_list= verbose= conf=" -- "${word}"))
            ;;
        create)
            COMPREPLY=($(compgen -W "distro_source= distro_name= container_type= container_image= container_test_image= branch= system= not_override= build_workflows_repository= verbose=" -- "${word}"))
            _complete_casa_distro_option_
            ;;
        create_writable_image)
            COMPREPLY=($(compgen -W "singularity_image= distro= branch= system= build_workflows_repository= verbose=" -- "${word}"))
            _complete_casa_distro_option_
            ;;
        list)
            COMPREPLY=($(compgen -W "distro= branch= system= build_workflows_repository= verbose=" -- "${word}"))
#             echo "reply: $COMPREPLY"
            _complete_casa_distro_option_
            ;;
        mrun)
            COMPREPLY=($(compgen -W "distro= branch= system= build_workflows_repository= gui= interactive= tmp_container= container_image= cwd= env= container_options= args_list= verbose= conf=" -- "${word}"))
            _complete_casa_distro_option_
            ;;
        root_shell)
            COMPREPLY=($(compgen -W "singularity_image= distro= branch= system= build_workflows_repository= verbose=" -- "${word}"))
            _complete_casa_distro_option_
            ;;
        run)
            COMPREPLY=($(compgen -W "distro= branch= system= build_workflows_repository= gui= interactive= tmp_container= container_image= cwd= env= container_options= args_list= verbose= conf=" -- "${word}"))
            _complete_casa_distro_option_
            ;;
        shell)
            COMPREPLY=($(compgen -W "distro= branch= system= build_workflows_repository= gui= interactive= tmp_container= container_image= cwd= env= container_options= args_list= verbose= conf=" -- "${word}"))
            _complete_casa_distro_option_
            ;;
        update)
            COMPREPLY=($(compgen -W "distro= branch= system= build_workflows_repository= verbose=" -- "${word}"))
            _complete_casa_distro_option_
            ;;
        update_image)
            COMPREPLY=($(compgen -W "distro= branch= system= build_workflows_repository= verbose=" -- "${word}"))
            _complete_casa_distro_option_
            ;;
        esac
        ;;
    esac

#     if [ -z "$COMPREPLY" ]; then
#         COMPREPLY=($(compgen -f -- "${word}"))
#     fi
}

# complete -W "help create list update update_image shell run mrun bv_maker create_writable_image root_shell" casa_distro
complete -W "help package_casa_distro publish_casa_distro create_release_plan update_release_plan html_release_plan create_latest_release create_docker update_docker publish_docker create_singularity publish_singularity publish_build_workflows" casa_distro_admin

complete -F _complete_casa_distro_ -o nospace -o default casa_distro
