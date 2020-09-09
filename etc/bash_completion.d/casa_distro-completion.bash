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

    local SHARE=$(realpath $(realpath $(dirname $(realpath $(which casa_distro))))/../share)
    if [ -d "$SHARE"/casa-distro-* ]; then
        SHARE="$SHARE"/casa-distro-*
    fi
    local SHARE_DIRS="${SHARE} ${CASA_DEFAULT_REPOSITORY}/share ${HOME}/.config/casa-distro ${HOME}/.casa-distro"

    case "$opt" in
    distro)
        local distro
        if [ ! -d "$SHARE" ]; then
            # no share dir (zip distrib): use builtin list
            distro="brainvisa opensource cati_platform web cea"
        fi
        for d in ${SHARE_DIRS}; do
            if [ -d "$d/distro" ]; then
                for d2 in $d/distro/*/; do
                    distro="$distro $(basename $d2)"
                done
            fi
        done
        COMPREPLY=($(compgen -W "$distro" -- "${word}"))
        ;;
    branch)
        COMPREPLY=($(compgen -W "master integration latest_releasse release_candidate" -- "${word}"))
        ;;
    system)
        local sys
        if [ ! -d "$SHARE" ]; then
            # no share dir (zip distrib): use builtin list
            sys="centos-7.4 ubuntu-12.04 ubuntu-14.04 ubuntu-16.04 ubuntu-18.04 windows-7-32 windows-7-64"
        else
            for system in "$SHARE/docker/casa-dev"/*/; do
                sys="$sys $(basename $system)"
            done
        fi
        COMPREPLY=($(compgen -W "$sys" -- "${word}"))
        ;;
    container_type)
        COMPREPLY=($(compgen -W "singularity docker virtualbox" -- "${word}"))
        ;;
    name)
        local names=`casa_distro list base_directory=$CASA_DEFAULT_REPOSITORY | grep -E -v '^(  [a-z])'`
        COMPREPLY=($(compgen -W "$names" -- "${word}"))
        ;;
    container_image|container_test_image)
        local images=$CASA_DEFAULT_REPOSITORY/*.simg
        COMPREPLY=($(compgen -W "$images" -- "${word}"))
        ;;
    image)
        # take existing singularity images
        local images=$CASA_DEFAULT_REPOSITORY/*.sif
#         for f in $images
#         do
#             local b=$(basename "$f")
#             local nimages="$nimages ${b:0:-4}"
#         done
        COMPREPLY=($(compgen -W "$images" -- "${word}"))
        ;;
    image_names)
        if [ "$cmd" = "publish_singularity" ] || [ "$cmd" = "clean_images" ]; then
            # take existing singularity images
            local images=$CASA_DEFAULT_REPOSITORY/*.simg
        fi
        if [ "$cmd" = "create_docker" ]; then
            local nimages
            if [ ! -d "$SHARE" ]; then
                # no share dir (zip distrib): use builtin list
                nimages="cati/casa-test: cati/casa-dev: cati/cati_platform:"
            fi
            for d in ${SHARE_DIRS}; do
                if [ -d "$d/docker" ]; then
                    for d2 in $d/docker/*/; do
                        nimages="${nimages} cati/$(basename $d2):"
                    done
                fi
            done
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
    base_directory)
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
        local SHARE=$(realpath $(realpath $(dirname $(realpath $(which casa_distro))))/../share)
        if [ -d "$SHARE"/casa-distro-* ]; then
            SHARE="$SHARE"/casa-distro-*
        fi
        local SHARE_DIRS="${SHARE} ${CASA_DEFAULT_REPOSITORY}/share ${HOME}/.config/casa-distro ${HOME}/.casa-distro"

        local nimages
        local image_dir=$(basename ${image})
        for d in ${SHARE_DIRS}; do
            if [ -d "$d/docker/${image_dir}" ]; then
                for d2 in ${d}/docker/${image_dir}/*/; do
                    nimages="${nimages} ${image}:$(basename $d2)"
                done
            fi
        done
        if [ -z "${nimages}" ]; then
            local sys
            if [ ! -d "$SHARE" ]; then
                # no share dir (zip distrib): use builtin list
                sys="centos-7.4 ubuntu-12.04 ubuntu-14.04 ubuntu-16.04 ubuntu-18.04 windows-7-32 windows-7-64"
            else
                for system in "$SHARE/docker/casa-dev"/*/; do
                    sys="$sys $(basename $system)"
                done
            fi
            local nimages
            for system in $sys; do
              nimages="${nimages} ${image}:${system}"
            done
        fi
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
    local cmd_list="help distro list setup setup_dev shell update update_image run mrun bv_maker delete clean_images"
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

        if { [ "$word" = ":" ] \
             && [ "${COMP_WORDS[$(( COMP_CWORD - 3 ))]}" = "image" ]; } \
             || { [ "${COMP_WORDS[$(( COMP_CWORD - 1 ))]}" = ":" ] \
                  && [ "${COMP_WORDS[$(( COMP_CWORD - 4 ))]}" = "image" ];}; then
            # in image option, after : sign
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
#         distro)
#             ;;
        setup)
            COMPREPLY=($(compgen -W "distro= version= name= container_type= image= writable= system= base_directory= url= output= verbose=" -- "${word}"))
            ;;
        setup_dev)
            COMPREPLY=($(compgen -W "distro= name= container_type= image= writable= branch= system= base_directory= url= output= verbose=" -- "${word}"))
            ;;
        list)
            COMPREPLY=($(compgen -W "type= distro= branch= system= name= base_directory= verbose=" -- "${word}"))
            ;;
        mrun)
            COMPREPLY=($(compgen -W "type= distro= branch= system= name= base_directory= gui= root= image= cwd= env= container_options= verbose=" -- "${word}"))
            ;;
        run)
            COMPREPLY=($(compgen -W "type= distro= branch= system= name= base_directory= gui= root= image= cwd= env= container_options= verbose=" -- "${word}"))
            ;;
        shell)
            COMPREPLY=($(compgen -W "type= distro= branch= system= name= base_directory= gui= root= image= cwd= env= container_options= verbose=" -- "${word}"))
            ;;
        update)
            COMPREPLY=($(compgen -W "type= distro= branch= system= name= base_directory= writable= verbose=" -- "${word}"))
            ;;
        update_image)
            COMPREPLY=($(compgen -W "type= distro= branch= system= name= base_directory= writable= verbose=" -- "${word}"))
            ;;
        delete)
            COMPREPLY=($(compgen -W "type= distro= branch= system= name= base_directory= interactive=" -- "${word}"))
            ;;
        clean_images)
            COMPREPLY=($(compgen -W "base_directory= image_names= verbose= interactive=" -- "${word}"))
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
