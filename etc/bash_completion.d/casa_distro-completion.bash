#/usr/bin/env bash

function _complete_casa_distro_option_()
{
    local word=${COMP_WORDS[COMP_CWORD]}
    local opt_n=$(( COMP_CWORD - 2 ))
    if [ "$word" = "=" ]; then
        local word=""
        local opt_n=$(( opt_n + 1 ))
    fi
    local opt=${COMP_WORDS[opt_n]}

    # get repository location
    if [ "${COMP_WORDS[1]}" = "-r" ] \
        || [  "${COMP_WORDS[1]}" = "--repository" ]; then
        local CASA_DEFAULT_REPOSITORY="${COMP_WORDS[2]}"
        local cmd="${COMP_WORDS[3]}"
    else
        local cmd="${COMP_WORDS[1]}"
    fi
    # TODO: catch cmd option build_workflows_repository
    if [ -z "$CASA_DEFAULT_REPOSITORY" ]; then
        local CASA_DEFAULT_REPOSITORY="$HOME/casa_distro"
    fi

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
        local images=$CASA_DEFAULT_REPOSITORY/*.simg
        COMPREPLY=($(compgen -W "$images" -- "${word}"))
        ;;
    image_names)
        if [ "$cmd" = "publish_singularity" ] || [ "$cmd" = "clean_images" ]; then
            # take existing singularity images
            local images=$CASA_DEFAULT_REPOSITORY/*.simg
        fi
        if [ "$cmd" = "create_docker" ]; then
            # use prefedined image names
            local nimages="cati/casa-test: cati/casa-dev: cati/cati_platform:"
        fi
        for f in $images
        do
            local b=$(basename "$f")
            # rebuild docker-like replacing 1st _ with /
            local b="${b/_//}"
            # then replace last _ with :
            # local b="${b/_/:}"
            local b=${b%_*}:${b##*_}
            local nimages="$nimages ${b:0:-5}"
        done
        if [ "$cmd" = "publish_docker" ] || [ "$cmd" = "create_singularity" ];
        then
            # complete using existing docker images
            local docker=$(which docker)
            if [ "$?" -eq 0 ]; then
                local dimages=$(docker images --format "{{.Repository}}:{{.Tag}}")
                local nimages="$nimages $dimages"
            fi
        fi
        COMPREPLY=($(compgen -W "$nimages" -- "${word}"))
        ;;
    verbose)
        COMPREPLY=($(compgen -W "True False 1 0" -- "${word}"))
        ;;
    build_workflows_repository)
        COMPREPLY=($(compgen -d -- "${word}"))
        ;;
    command)
        COMPREPLY=($(compgen -c -W "host workflow" -- "${word}"))
        ;;
    esac
}


function _complete_casa_distro_image_names_tag_()
{
    local word=${COMP_WORDS[COMP_CWORD]}
    local image=${COMP_WORDS[$(( COMP_CWORD - 2 ))]}
    if [ "$word" = ":" ]; then
        local image=${COMP_WORDS[$(( COMP_CWORD - 1 ))]}
    fi

    if [ "$word" = ":" ]; then
        local word=""
    fi

    # get repository location
    if [ "${COMP_WORDS[1]}" = "-r" ] \
        || [  "${COMP_WORDS[1]}" = "--repository" ]; then
        local CASA_DEFAULT_REPOSITORY="${COMP_WORDS[2]}"
        local cmd="${COMP_WORDS[3]}"
    else
        local cmd="${COMP_WORDS[1]}"
    fi
    if [ -z "$CASA_DEFAULT_REPOSITORY" ]; then
        local CASA_DEFAULT_REPOSITORY="$HOME/casa_distro"
    fi

    if [ "$cmd" = "publish_singularity" ]; then
        local images=$CASA_DEFAULT_REPOSITORY/*.simg
    fi
    local nimages=""
    for f in $images
    do
        local b=$(basename "$f")
        # rebuild docker-like replacing 1st _ with /
        local b="${b/_//}"
        # then replace last _ with :
        # local b="${b/_/:}"
        local b=${b%_*}:${b##*_}
        local nimages="$nimages ${b:0:-5}"
    done
    if [ "$cmd" = "create_singularity" ] || [ "$cmd" = "publish_docker" ]; then
        # complete using existing docker images
        local docker=$(which docker)
        if [ "$?" -eq 0 ]; then
            local dimages=$(docker images --format "{{.Repository}}:{{.Tag}}")
            local nimages="$nimages ${dimages}"
        fi
    fi
    if [ "$cmd" = "create_docker" ]; then
        local nimages="${image}:ubuntu-12.04 ${image}:ubuntu-14.04 ${image}:ubuntu-16.04 ${image}:ubuntu-18.04 ${image}:centos-7.4 ${image}:windows-7-32 ${image}:windows-7-64"
    fi

    local matching=($(compgen -W "$nimages" -- "${image}:${word}"))
    local m
    for m in ${matching[@]}; do
        COMPREPLY+=(${m/$image:/})
    done
}


function _complete_casa_distro_()
{
    local word=${COMP_WORDS[COMP_CWORD]}
    local line=${COMP_LINE}
    local cmd_list="help create list update update_image shell run mrun bv_maker create_writable_image root_shell delete clean_images"
    local opt_list="-r --repository -h --help -v --verbose --version"
    local cmd_wd_num=1

    # find if 1st option is -r
    if (( COMP_CWORD > 1 )) \
        && { [ "${COMP_WORDS[1]}" = "-r" ] \
             || [  "${COMP_WORDS[1]}" = "--repository" ]; }; then
        case "$COMP_CWORD" in
        2)
            # completing dir
            COMPREPLY=($(compgen -d -- "$word"))
            return
            ;;
        *)
            # -r arg is already passed, cmd is arg 3
            local cmd_wd_num=3
        esac
    fi

    case $(( COMP_CWORD - cmd_wd_num )) in
    0)
        COMPREPLY=($(compgen -W "$cmd_list $opt_list" -- "${word}"))
        if [ -n "$COMPREPLY" ]; then
            COMPREPLY="$COMPREPLY "
        fi
        ;;
    *)
        local cmd=${COMP_WORDS[cmd_wd_num]}

        if [ "$word" = "=" ] \
             || [ "${COMP_WORDS[$(( COMP_CWORD - 1 ))]}" = "=" ]; then
            # after = sign: complete an option value
            _complete_casa_distro_option_
            return
        fi

        if { [ "$word" = ":" ] \
             && [ "${COMP_WORDS[$(( COMP_CWORD - 3 ))]}" = "image_names" ]; } \
             || { [ "${COMP_WORDS[$(( COMP_CWORD - 1 ))]}" = ":" ] \
                  && [ "${COMP_WORDS[$(( COMP_CWORD - 4 ))]}" = "image_names" ];}; then
            # in image_names option, after : sign
            _complete_casa_distro_image_names_tag_
            return
        fi

        case "$cmd" in
        help)
            COMPREPLY=($(compgen -W "$cmd_list" -- "${word}"))
            ;;
        bv_maker)
            # delegate to bv_maker completion
            COMP_WORDS=("${COMP_WORDS[@]:1}")
            COMP_CWORD=$(( COMP_CWORD - 1 ))
            _complete_bv_maker_
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
            COMPREPLY=($(compgen -W "distro= branch= system= build_workflows_repository= gui= interactive= tmp_container= container_image= cwd= env= container_options= verbose= conf=" -- "${word}"))
            ;;
        root_shell)
            COMPREPLY=($(compgen -W "singularity_image= distro= branch= system= build_workflows_repository= verbose=" -- "${word}"))
            ;;
        run)
            COMPREPLY=($(compgen -W "distro= branch= system= build_workflows_repository= gui= interactive= tmp_container= container_image= cwd= env= container_options= verbose= conf=" -- "${word}"))
            ;;
        shell)
            COMPREPLY=($(compgen -W "distro= branch= system= build_workflows_repository= gui= interactive= tmp_container= container_image= cwd= env= container_options= verbose= conf=" -- "${word}"))
            ;;
        update)
            COMPREPLY=($(compgen -W "distro= branch= system= build_workflows_repository= verbose= command=" -- "${word}"))
            ;;
        update_image)
            COMPREPLY=($(compgen -W "distro= branch= system= build_workflows_repository= verbose=" -- "${word}"))
            ;;
        delete)
            COMPREPLY=($(compgen -W "distro= branch= system= build_workflows_repository= interactive=" -- "${word}"))
            ;;
        clean_images)
            COMPREPLY=($(compgen -W "build_workflows_repository= image_names= verbose= interactive=" -- "${word}"))
            ;;
        esac
        ;;
    esac

}


function _complete_casa_distro_admin_()
{
    local word=${COMP_WORDS[COMP_CWORD]}
    local line=${COMP_LINE}
    local cmd_list="help package_casa_distro publish_casa_distro create_release_plan update_release_plan html_release_plan create_latest_release create_docker update_docker publish_docker create_singularity publish_singularity publish_build_workflows"
    local opt_list="-r --repository -h --help -v --verbose --version"
    local cmd_wd_num=1

    # find if 1st option is -r
    if (( COMP_CWORD > 1 )) \
        && { [ "${COMP_WORDS[1]}" = "-r" ] \
             || [  "${COMP_WORDS[1]}" = "--repository" ]; }; then
        case "$COMP_CWORD" in
        2)
            # completing dir
            COMPREPLY=($(compgen -d -- "$word"))
            return
            ;;
        *)
            # -r arg is already passed, cmd is arg 3
            local cmd_wd_num=3
        esac
    fi

    case $(( COMP_CWORD - cmd_wd_num )) in
    0)
        COMPREPLY=($(compgen -W "$cmd_list $opt_list" -- "${word}"))
        if [ -n "$COMPREPLY" ]; then
            COMPREPLY="$COMPREPLY "
        fi
        ;;
    *)
        local cmd=${COMP_WORDS[cmd_wd_num]}

        if [ "$word" = "=" ] \
             || [ "${COMP_WORDS[$(( COMP_CWORD - 1 ))]}" = "=" ]; then
            # after = sign: complete an option value
            _complete_casa_distro_option_
            return
        fi

        if { [ "$word" = ":" ] \
             && [ "${COMP_WORDS[$(( COMP_CWORD - 3 ))]}" = "image_names" ]; } \
             || { [ "${COMP_WORDS[$(( COMP_CWORD - 1 ))]}" = ":" ] \
                  && [ "${COMP_WORDS[$(( COMP_CWORD - 4 ))]}" = "image_names" ];}; then
            # in image_names option, after : sign
            _complete_casa_distro_image_names_tag_
            return
        fi

        case "$cmd" in
        help)
            COMPREPLY=($(compgen -W "$cmd_list" -- "${word}"))
            ;;
        package_casa_distro)
            COMPREPLY=($(compgen -W "build_workflows_repository=" -- "${word}"))
            ;;
        publish_casa_distro)
            COMPREPLY=($(compgen -W "build_workflows_repository= repository_server= repository_server_directory= login= verbose=" -- "${word}"))
            ;;
        create_release_plan|update_release_plan)
            COMPREPLY=($(compgen -W "components= build_workflows_repository= verbose=" -- "${word}"))
            ;;
        html_release_plan)
            COMPREPLY=($(compgen -W "login= password= build_workflows_repository= verbose=" -- "${word}"))
            ;;
        create_latest_release)
            COMPREPLY=($(compgen -W "build_workflows_repository= dry= ignore_warning= verbose=" -- "${word}"))
            ;;
        create_docker)
            COMPREPLY=($(compgen -W "image_names= verbose=" -- "${word}"))
            ;;
        update_docker|publish_docker)
            COMPREPLY=($(compgen -W "image_names= verbose=" -- "${word}"))
            ;;
        create_singularity)
            COMPREPLY=($(compgen -W "image_names= build_workflows_repository= verbose=" -- "${word}"))
            ;;
        publish_singularity)
            COMPREPLY=($(compgen -W "image_names= build_workflows_repository= repository_server= repository_server_directory= login= verbose=" -- "${word}"))
            ;;
        publish_build_workflows)
            COMPREPLY=($(compgen -W "distro= branch= system= build_workflows_repository= repository_server= repository_server_directory= login= verbose=" -- "${word}"))
            ;;
        esac
        ;;
    esac

}



# complete -W "help create list update update_image shell run mrun bv_maker create_writable_image root_shell" casa_distro
# complete -W "help package_casa_distro publish_casa_distro create_release_plan update_release_plan html_release_plan create_latest_release create_docker update_docker publish_docker create_singularity publish_singularity publish_build_workflows" casa_distro_admin

complete -F _complete_casa_distro_ -o nospace -o default casa_distro
complete -F _complete_casa_distro_admin_ -o nospace -o default casa_distro_admin
