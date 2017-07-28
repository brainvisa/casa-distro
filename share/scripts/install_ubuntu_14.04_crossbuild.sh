#!/usr/bin/env bash
#
# To uninstall python use:
# wine64 msiexec /x /tmp/python-2.7.11.amd64.msi /qn TARGETDIR=d:\\usr\\local\\python-2.7.11 ALLUSERS=1
#

# ------------------------------------------------------------------------------
# Functions
# ------------------------------------------------------------------------------
function set_toolchain() {
    export CFLAGS="-I${CROSSBUILD_INSTALL_PREFIX}/include"
    export CPPFLAGS="-I${CROSSBUILD_INSTALL_PREFIX}/include"
    export CXXFLAGS=$CPPFLAGS
    export LDFLAGS="-L${CROSSBUILD_INSTALL_PREFIX}/lib"
    export XDG_DATA_DIRS="${CROSSBUILD_INSTALL_PREFIX}/share"
    export CC=${__toolchain}-gcc
    export CXX=${__toolchain}-g++
    export LD=${__toolchain}-ld
    export RANLIB=${__toolchain}-ranlib
    export AR=${__toolchain}-ar
    export AS=${__toolchain}-as
    export STRIP=${__toolchain}-strip
}

function unset_toolchain() {
    export CFLAGS=
    export CPPFLAGS=
    export CXXFLAGS=
    export LDFLAGS=
    export XDG_DATA_DIRS=
    export CC=
    export CXX=
    export LD=
    export RANLIB=
    export AR=
    export AS=
    export STRIP=
}

function get_c_flags() {
    __result=
    __split_flags=0

    if [ "$1" = "--split" ]; then
        __split_flags=1;shift;
    fi

    for l in $@; do
        #echo "===== DEBUG ==== l: $l" >&2
        __pkg_config_result="$(pkg-config --cflags $l 2>/dev/null)"
        __pkg_config_error=$?
        #echo "===== DEBUG ==== __pkg_config_error: ${__pkg_config_error}" >&2
        if [ ${__pkg_config_error} -eq 0 ]; then
            __flags="${__pkg_config_result}"
        else
            __flags="-I${CROSSBUILD_INSTALL_PREFIX}/$l/include"
        fi 

        if [ -z "${__result}" ]; then
            __result="${__flags}"
        else
            __result="${__result} ${__flags}"
        fi
        
    done

    if [ "${__split_flags}" = "1" ]; then
        echo "${__result}" | sed 's/-I/-I /g' | sed 's/-D/-D /g' | sed -r 's/\(\s\)+/ /g'
    else
        echo "${__result}"
    fi

    __split_flags=
    __result=
    __flags=
    __pkg_config_result=
    __pkg_config_error=
}

function get_link_flags() {
    __result=
    __split_flags=0

    if [ "$1" = "--split" ]; then
        __split_flags=1;shift;
    fi

    for l in $@; do
        __pkg_config_result="$(pkg-config --libs-only-L $l 2>/dev/null)"
        __pkg_config_error=$?
        if [ ${__pkg_config_error} -eq 0 ]; then
            __flags="${__pkg_config_result}"
        else
            __flags="-L${CROSSBUILD_INSTALL_PREFIX}/$l/lib"
        fi 

        if [ -z "${__result}" ]; then
            __result="${__flags}"
        else
            __result="${__result} ${__flags}"
        fi
        
    done


    if [ "${__split_flags}" = "1" ]; then
        echo "${__result}" | sed 's/-L/-L /g' | sed -r 's/\(\s\)+/ /g'
    else
        echo "${__result}"        
    fi

    __split_flags=
    __result=
    __flags=
    __pkg_config_result=
    __pkg_config_error=
}

function download() {
    
    # check if download type was specified as first argument
    __download_type="sources"
    for __d in "sources" "i686" "x86_64"; do 
        if [ "$1" == "${__d}" ]; then
            __download_type="pkg/$1"
            shift;
            break;
        fi
    done

    __file_name="$(basename $1)"

    # if mirror url is set, we use it 
    if [ -z "${__mirror_url}" ]; then
        __url="$1"
    else
        __url="${__mirror_url}/${__download_type}/${__file_name}"
    fi

    # if a second parameter is given to the function
    # we use it as the output file name
    if [ -z "$2" ]; then
        __out_file_name="${__file_name}"
    else
        __out_file_name="$2"
    fi

    # Download is done when:
    # 1) Output file does not exists
    # 2) Size of output file is 0
    # 3) Download is forced using FORCE_DOWNLOAD variable
    if [ ! -f "${__download_dir}/${__out_file_name}" ] \
        || [ "$(du -b ${__download_dir}/${__out_file_name} | cut -f 1)" == "0" ] \
        || [ "${CROSSBUILD_FORCE_DOWNLOAD}" == "1" ]; then
        if [ "${CROSSBUILD_VERBOSE}" == "1" ]; then
            echo "download ${__url} => ${__download_dir}/${__out_file_name}"
        fi
        wget --no-check-certificate \
             --user-agent "Mozilla" \
             "${__url}" \
             -O ${__download_dir}/${__out_file_name}
    fi
    __d=
    __download_type=
    __file_name=
    __url=
    __out_file_name=
}

function remove() {
    __directory="$1"
    if [ -z "${__directory}" ]; then
        if [ "${CROSSBUILD_VERBOSE}" == "1" ]; then
            echo "unable to remove install directory: no directory given."
        fi
    else
        if [ -d "${__directory}" ]; then
            if [ "${CROSSBUILD_VERBOSE}" == "1" ]; then
                echo "removing ${__directory}"
            fi
            rm -rf "${__directory}"
        fi
    fi

    unset __directory
}

function fix_python_script() {
    __executable="$1"
    if [ -f "${__executable}" ]; then
        if [ "${CROSSBUILD_VERBOSE}" == "1" ]; then
            echo "fixing python script ${__executable}"
        fi
        sed -i -e 's/#!.*python.exe/#!python.exe/g' ${__executable}
    fi
}

# ------------------------------------------------------------------------------
# Global variables
# ------------------------------------------------------------------------------
if [ -z "${CROSSBUILD_DOWNLOAD}" ]; then
    # Defaultly download components
    __download="1"
else
    __download="${CROSSBUILD_DOWNLOAD}"
fi

if [ -z "${CROSSBUILD_INSTALL}" ]; then
    # Defaultly install components
    __install="1"
else
    __install="${CROSSBUILD_INSTALL}"
fi

if [ "${CROSSBUILD_DOWNLOAD_ONLY}" == "1" ]; then
    __install="0"
fi

if [ -z "${CROSSBUILD_REMOVE_BEFORE_INSTALL}" ]; then
    if [ "${__install}" == "1" ]; then
        # Defaultly remove installed components
        __remove_before_install="1"
    else
        __remove_before_install="0"
    fi
else
    __remove_before_install="${CROSSBUILD_REMOVE_BEFORE_INSTALL}"
fi

if [ -z "${CROSSBUILD_USE_CEA_MIRROR}" ]; then
    # Defaultly use CEA mirror
    __use_cea_mirror="1"
else
    __use_cea_mirror="${CROSSBUILD_USE_CEA_MIRROR}"
fi

if [ "${__use_cea_mirror}" == "1" ]; then
    if [ -z "${CROSSBUILD_CEA_MIRROR_VERSION}" ]; then
        __cea_mirror_version="1.0.0"
    else
        __cea_mirror_version="${CROSSBUILD_CEA_MIRROR_VERSION}"
    fi
    __mirror_url="ftp://ftp.cea.fr/pub/dsv/anatomist/3rdparty/${__cea_mirror_version}"
else
    if [ -n "${CROSSBUILD_MIRROR_URL}" ]; then
        __mirror_url="${CROSSBUILD_MIRROR_URL}"
    fi
fi

if [ -z "${CROSSBUILD_UPDATE_REGISTRY_PATH}" ]; then
    # Defaultly update registry path
    __update_registry_path="1"
else
    __update_registry_path="${CROSSBUILD_UPDATE_REGISTRY_PATH}"
fi

if [ -z "${CROSSBUILD_FIX_PYTHON_SCRIPTS}" ]; then
    # Defaultly fixes python scripts
    __fix_python_scripts=1
else
    __fix_python_scripts=${CROSSBUILD_FIX_PYTHON_SCRIPTS}
fi

# ------------------------------------------------------------------------------
# Build variables
# ------------------------------------------------------------------------------
if [ -z "${CROSSBUILD_ARCH}" ]; then
    __arch="i686"
else
    __arch="${CROSSBUILD_ARCH}"
fi

if [ -z "${CROSSBUILD_TOOLCHAIN}" ]; then
    #TOOLCHAIN=i586-mingw32msvc
    __toolchain=${__arch}-w64-mingw32
else
    __toolchain="${CROSSBUILD_TOOLCHAIN}"
fi

if [ -z "${CROSSBUILD_BUILDTYPE}" ]; then
    __buildtype=x86_64-linux-gnu
else
    __buildtype="${CROSSBUILD_BUILDTYPE}"
fi

if [ -z "${CROSSBUILD_PROC_NUM}" ]; then
    __build_proc_num=$(($(lscpu -p | grep -v '#' | wc -l) - 1))
else
    __build_proc_num="${CROSSBUILD_PROC_NUM}"
fi

if [ -z "${CROSSBUILD_TMP_DIR}" ]; then
    # Create temporary build directory
    __tmp_dir="$(mktemp -d)"
else
    __tmp_dir="${CROSSBUILD_TMP_DIR}"
fi

if [ -z "${CROSSBUILD_BUILD_DIR}" ]; then
    __build_dir="${__tmp_dir}"
else
    __build_dir="${CROSSBUILD_BUILD_DIR}"
fi
if [ ! -d "${__build_dir}" ]; then
    mkdir -p "${__build_dir}"
fi

if [ -z "${CROSSBUILD_DOWNLOAD_DIR}" ]; then
    __download_dir="${__tmp_dir}"
else
    __download_dir="${CROSSBUILD_DOWNLOAD_DIR}"
fi
if [ ! -d "${__download_dir}" ]; then
    mkdir -p "${__download_dir}"
fi

pushd "${__build_dir}" 2>&1>/dev/null

# ------------------------------------------------------------------------------
# Package variables
# ------------------------------------------------------------------------------
__sys_packages=(autoconf automake autopoint bash bison bzip2 cmake flex gettext
                git g++ gperf intltool libffi-dev libglib2.0-dev libtool
                libltdl-dev libssl-dev libxml-parser-perl make openssl patch
                perl pkg-config python python-virtualenv ruby scons sed unzip
                wget xvfb xz-utils dos2unix texinfo)

__build_packages=(wine mingw64 python)

__build_libs=(libiconv zlib libxml2 expat hdf5 gettext sqlite libsigcpp freetype
              libregex boost blitz libffi libjpeg libtiff libpng fontconfig glib 
              openjpeg jpegxr gdkpixbuf pixman cairo openslide dcmtk netcdf minc
              libsvm qt qwt5 yaml qtifw)

__build_python_mods=(python_wheel python_pip python_sip python_pyqt python_six 
                     python_numpy python_scipy python_traits python_dateutil 
                     python_pytz python_pyparsing python_cycler
                     python_singledispatch python_tornado python_certifi
                     python_backports_abc python_nose python_cairo
                     python_configobj python_matplotlib python_crypto
                     python_paramiko python_pyro python_pil python_dicom
                     python_yaml python_xmltodict python_markupsafe 
                     python_jinja2 python_pygments python_docutils 
                     python_sphinx)

if [ -z "${CROSSBUILD_INSTALL_PREFIX}" ]; then
    CROSSBUILD_INSTALL_PREFIX="${HOME}/${__toolchain}/usr/local"
fi

# Create install directories
mkdir -p ${CROSSBUILD_INSTALL_PREFIX}/bin ${CROSSBUILD_INSTALL_PREFIX}/lib/pkgconfig ${CROSSBUILD_INSTALL_PREFIX}/include

# Set package variables
__packages=
if [ "${CROSSBUILD_ALL}" == "1" ]; then
    __packages=(system
               ${__build_packages[@]}
               ${__build_libs[@]}
               ${__build_python_mods[@]})
else
    if [ "${CROSSBUILD_LIBS}" == "1" ]; then
        __packages=(${__build_libs[@]})
    fi

    if [ "${CROSSBUILD_PYTHON_MODULES}" == "1" ]; then
        __packages=(${__packages[@]} ${__build_python_mods[@]})
    fi
fi

# Declare upper case variables for each components
for p in ${__packages[@]}; do
    __var_name="${p^^}"
    declare "${__var_name}"="1"
    echo "${__var_name}=${!__var_name}"
done

# ------------------------------------------------------------------------------
# Toolchain files generation
# ------------------------------------------------------------------------------
# Generate cmake toolchain file
cat << EOF > toolchain-${__toolchain}.cmake
# the name of the target operating system
SET(CMAKE_SYSTEM_NAME Windows)

if (NOT COMPILER_PREFIX)
    set(COMPILER_PREFIX "${__toolchain}")
endif()

# which compilers to use for C and C++
find_program(CMAKE_RC_COMPILER NAMES \${COMPILER_PREFIX}-windres)
find_program(CMAKE_C_COMPILER NAMES \${COMPILER_PREFIX}-gcc)
find_program(CMAKE_CXX_COMPILER NAMES \${COMPILER_PREFIX}-g++)
find_program(CMAKE_Fortran_COMPILER NAMES \${COMPILER_PREFIX}-gfortran)

# here is the target environment located
set(CMAKE_FIND_ROOT_PATH /usr/\${COMPILER_PREFIX} \${CMAKE_FIND_ROOT_PATH})

# adjust the default behaviour of the FIND_XXX() commands:
# search headers and libraries in the target environment, search 
# programs in the host environment
set(CMAKE_FIND_ROOT_PATH_MODE_PROGRAM NEVER)
set(CMAKE_FIND_ROOT_PATH_MODE_LIBRARY ONLY)
set(CMAKE_FIND_ROOT_PATH_MODE_INCLUDE ONLY)

EOF

cat << EOF > /dev/null #toolchain-${__toolchain}.sh
PATH=${CROSSBUILD_INSTALL_PREFIX}/bin:${PATH}
PKG_CONFIG=$(which pkg-config)
PKG_CONFIG_PATH="${CROSSBUILD_INSTALL_PREFIX}/lib/pkgconfig"
CFLAGS="-I${CROSSBUILD_INSTALL_PREFIX}/include"
CPPFLAGS="-I${CROSSBUILD_INSTALL_PREFIX}/include"
LDFLAGS="-L${CROSSBUILD_INSTALL_PREFIX}/lib"
XDG_DATA_DIRS="${CROSSBUILD_INSTALL_PREFIX}/share"

CC=${__toolchain}-gcc
CXX=${__toolchain}-g++
LD=${__toolchain}-ld
RANLIB=${__toolchain}-ranlib
AR=${__toolchain}-ar
AS=${__toolchain}-as
STRIP=${__toolchain}-strip

EOF

# ------------------------------------------------------------------------------
# Update registry script
# ------------------------------------------------------------------------------
cat << EOF > update_registry_path
#!/usr/bin/env python
from __future__                 import print_function
import os

try:
    from configparser               import RawConfigParser, NoOptionError
except:
    from ConfigParser               import RawConfigParser, NoOptionError
    
def get_section(line):
   e = line.index(']')
   
   return (line[line.index('[')+1:e], line[e+1:])

class RegistryFileReader(object):
    def __init__(self, fp):
        self.fp = fp
        self.head = None
        self.comments = dict()
        self.tags = dict()
        self.__initialized_section = False
        self.__cur_section = 'global'
    
    def __start_section(self, line):
        k, t = get_section(line)
        #print('__start_section, k', k, 't', t)
        self.__cur_section = k
        self.tags[k] = t
    
    def __add_comment(self, line):
        #print('__add_comment', line, 'for section', self.__cur_section)
        self.comments.setdefault(self.__cur_section, []).append(line)
        
    def readline(self):
        
        if not self.__initialized_section:
            self.__initialized_section = True
            return '[%s]\\n' % self.__cur_section
        
        line = self.fp.readline()
        if not self.head:
            self.head = line
            return ';;'
            
        l = line.strip()
        
        if l.startswith('['):
            self.__start_section(line)
        
        elif l.startswith('#') or l.startswith(';;'):
            self.__add_comment(line)
            
        else:
            line.replace(':', ':')
        
        return line

class RegistryFileWriter(object):
    def __init__(self, fp, head, tags = dict(), comments = dict()):
        self.fp = fp
        self.head = head
        self.tags = tags
        self.comments = comments
        
    def write(self, line):
        l = line.strip()
        
        if l.startswith('['):
            k, t = get_section(line)
            
            if len(t.strip()) == 0:
                t = self.tags.get(k)
                
            if k == 'global':
                line = self.head + '\\n'
            else:
                if len(t.strip()) > 0:
                    line = line[:-1] + t + line[-1]
            self.fp.write(line[:-1])
                
            # Write comment lines for section
            for c in self.comments.get(k, []):
                self.fp.write(c)
        else:
            line = line.replace(" = ", "=", 1)
            if line.strip().endswith("="):
                line = line[:-1] + "\\"\\"" + line[-1]
                
            self.fp.write(line)

class RegistryFileParser(RawConfigParser):
    import re
    
    OPTCRE = re.compile(
    r'(?P<option>[^=\\s][^=]*)'              # very permissive!
    r'\\s*(?P<vi>[:=])\\s*'                   # any number of space/tab,
                                            # followed by separator
                                            # (either : or =), followed
                                            # by any # space/tab
    r'(?P<value>.*)$'                       # everything up to eol
    )
    OPTCRE_NV = re.compile(
        r'(?P<option>[^=\\s][^=]*)'            # very permissive!
        r'\\s*(?:'                             # any number of space/tab,
        r'(?P<vi>[:=])\\s*'                    # optionally followed by
                                              # separator (either : or
                                              # =), followed by any #
                                              # space/tab
        r'(?P<value>.*))?$'                   # everything up to eol
        )
    
    def __init__(self):
        RawConfigParser.__init__(self)
        self.optionxform = str
        self.__head = None
        self.__comments = dict()
        self.__tags = dict()
    
    def read(self, f):
        registry_reader = RegistryFileReader(open(f))
        self.readfp(registry_reader)
        self.__head = registry_reader.head
        self.__comments = registry_reader.comments
        self.__tags = registry_reader.tags
  
    def write(self, f):
        RawConfigParser.write(self, RegistryFileWriter(f,
                                                       self.__head,
                                                       self.__tags, 
                                                       self.__comments))
        
    def get_value_list(self, section, value):
        v = self.get(section, value)
        # Find starting and ending double quotes
        s = v.find('"')
        e = v.find('"', s + 1)
        
        if s == -1:
            s = v.find(':')
            t, v = (v[:s - 1], v[s + 1:])
        
        elif s == 0:
            t = None
            
        else:
            t, v = (v[:s - 1], v[s:])
            
        if t == 'str(2)' or t is None:
            return eval(v).split(';')
        
        else:
            raise RuntimeError('Registry value with type %s [section: %s, value: %s] is '
                               'not supported yet' % (t, section, value))
        
    def set_value_list(self, key, value, data):
        
        d = '"' + string.join(data, ';') + '"'
        return self.set(key, value, d)

def split_value_path(value_path, parse_root = True):
    l = value_path.split('\\\\')
    
    offset = 0 if parse_root else 1
    registry_root = l[0] if parse_root else None
    section = l[1 - offset:-1] if len(l) > (2 - offset) else ''
    
    # Remove leading and trailing \\
    if len(section) > 0 and section[0] == '':
      section = section[1:]
    if section[-1] == '':
      section = section[:-1]
    value = l[-1] if len(l) > (1 - offset) else None
    
    return (registry_root, '\\\\'.join(section), value)

def get_registry_file(registry_root):
    if registry_root in ('HKLM', 'HKEY_LOCAL_MACHINE', 
                         'HKCR', 'HKEY_CLASSES_ROOT'):
        return 'system.reg'
    elif registry_root in ('HKCU', 'HKEY_CURRENT_USER',
                           'HKU', 'HKEY_USERS'):
        return 'user.reg'
    elif registry_root in ('HKCC', 'HKEY_CURRENT_CONFIG'):
        raise RuntimeError('HKEY_CURRENT_CONFIG is only stored in memory' \\
                           'no file is associated')
    else:
        raise RuntimeError('%s registry root is unknown' % registry_root)

def add_to_list(lst, value, prepend = True, unique = True):
    if prepend:
        lst = [value] + lst
    else:
        lst = lst + [value]
        
    unique_values = set()
    result = []
    
    for v in lst:
        if not unique or v not in unique_values:
            unique_values.add(v)
            result.append(v)
            
    return result

def registry_normalize(value):
    return value.replace('\\\\', r'\\\\')
    
#---------------------------------------------------------------------------
# Default values
#---------------------------------------------------------------------------
wine_prefix = os.environ.get('WINEPREFIX')
casa_deps = os.environ.get('CASA_DEPS')
crossbuild_install_prefix = os.environ.get('CROSSBUILD_INSTALL_PREFIX')
wine_dir = wine_prefix if wine_prefix \\
           else os.path.join(os.environ.get('HOME'), '.wine')               
prefix_default = casa_deps if casa_deps else crossbuild_install_prefix
registry_file_default = None
registry_action_default = 'set'
value_path_default = None
value_default = ''

#---------------------------------------------------------------------------
# Main
#---------------------------------------------------------------------------
if __name__ == '__main__':
    import string
    from argparse                   import ArgumentParser                             
    
    #---------------------------------------------------------------------------
    # Argument parser initialization
    #---------------------------------------------------------------------------
    description = '''
    Update registry with missing pathes.
    '''
    
    parser = ArgumentParser( description = description )

    parser.add_argument(
        '-f', '--registry-file',
        dest = 'registry_file',
        help = 'Wine registry file to update\\n'
            '[default: %s].' % registry_file_default,
        metavar = 'REGISTRY_FILE',
        default = registry_file_default
    )
    
    parser.add_argument(
        '-p', '--prefix',
        dest = 'prefix',
        help = 'Install prefix to use\\n'
            '[default: %s].' % prefix_default,
        metavar = 'PREFIX',
        default = prefix_default
    )
    
    parser.add_argument(
        '-r', '--registry-action',
        dest = 'registry_action',
        help = 'action to do in registry\\n'
            '[default: %s].' % registry_action_default,
        metavar = 'REGISTRY_ACTION',
        default = registry_action_default
    )
    
    parser.add_argument(
        '--value-path',
        dest = 'value_path',
        help = 'path of the value to set in registry\\n'
            '[default: %s].' % value_path_default,
        metavar = 'VALUE_PATH',
        default = value_path_default
    )
        
    parser.add_argument(
        '--value',
        dest = 'value',
        help = 'the value to set in registry\\n'
            '[default: %s].' % value_default,
        metavar = 'VALUE',
        default = value_default
    )
    
    args = parser.parse_args()
    
    if args.registry_action not in ('set', 'append', 'prepend'):
        raise RuntimeError('Registry action %s is not supported. Only set, ' \\
                           'append and prepend are currently available ' \\
                           'actions' % args.registry_action)
    
    if not args.value_path or not len(args.value_path.strip()) > 0:
        raise RuntimeError('Value path to edit must be given')        
    
    registry_root, section, value = split_value_path(args.value_path.strip())
    #print('==== info from ', args.value_path.strip(), 
    #      'root', registry_root, 'section', section, 'value', value)
    section = registry_normalize(section)
    if not args.registry_file:
        registry_file = get_registry_file(registry_root)
        registry_file = os.path.join(wine_dir, registry_file)
    else:
        registry_file = args.registry_file
    
    
    parser = RegistryFileParser()
    parser.read(registry_file)
    
    if args.registry_action == 'set':
        try:
            registry_value = parser.get(section, '"%s"' % value)
        except NoOptionError:
            registry_value = '**not defined**'
            
        #print('==== read value', registry_value, 'from', args.value_path, 'in', 
        #      registry_file)
        parser.set(section, 
                   '"' + value + '"',
                   '"' + registry_normalize(args.value) + '"')
        print('Wine registry updated,', value, 'set to', args.value)
              
    elif args.registry_action in ('prepend', 'append'):
        try:
            registry_list = parser.get_value_list(section, '"%s"' % value)
        except NoOptionError:
            registry_list = '**not defined**'
            
        new_registry_list = add_to_list(registry_list, 
                                        args.value,
                                        prepend = (args.registry_action 
                                                   == 'prepend'))
        #print('==== setting value', new_registry_list, 'to',
        #      args.value_path, 'in', registry_file)
        parser.set(section, 
                   '"' + value + '"',
                   '"' + registry_normalize(';'.join(new_registry_list)) + '"')
        print('Wine registry updated,', value, 'set to', 
              ';'.join(new_registry_list))
    parser.write(open(registry_file, 'wb'))
    
EOF
chmod +x update_registry_path

# ------------------------------------------------------------------------------
# Install system packages
# ------------------------------------------------------------------------------
if [ "${__install}" == "1" ] && [ "${SYSTEM}" == "1" ]; then
    echo "=========================== SYSTEM ==============================="
    sudo apt-get -q -y install ${__sys_packages[@]}
fi

# ------------------------------------------------------------------------------
# Create virtual python environment
# to get an up-to-date setuptools pip and wheel packages
# ------------------------------------------------------------------------------
PYTHON_HOST_VIRTUAL_DIR=${__tmp_dir}/python2-virtualenv
PYTHON_HOST_COMMAND=python2
virtualenv -p python2 --system-site-packages "${PYTHON_HOST_VIRTUAL_DIR}"
export PATH="${PYTHON_HOST_VIRTUAL_DIR}/bin:${PATH}"
${PYTHON_HOST_COMMAND} -m pip install --upgrade pip setuptools wheel
${PYTHON_HOST_COMMAND} -m pip install --upgrade distutilscross

# ------------------------------------------------------------------------------
# Wine 1.8
# ------------------------------------------------------------------------------
if [ -n "${WINECMD}" ]; then
    __wine_cmd="${WINECMD}"
else
    if [ "${__arch}" == "x86_64" ]; then
        __wine_cmd=wine64
    else
        __wine_cmd=wine
    fi
fi

if [ -n "${WINEPREFIX}" ]; then
    __wine_prefix=${WINEPREFIX}
else
    __wine_prefix=${HOME}/.wine
fi

if [ "${__install}" == "1" ] && [ "${WINE}" == "1" ]; then
    echo "============================ WINE ================================"
    cat << EOF > "${__build_dir}/apt-wine.sh"
#!/usr/bin/env sh
dpkg --add-architecture i386
add-apt-repository -y ppa:ubuntu-wine/ppa
apt-get -q -y update
apt-get -q -y -f install
apt-get -q -y autoremove

# Explicit calls are used to ensure i386 installation,
# otherwise it may fails
apt-get -q -y install libp11-kit-gnome-keyring:i386
apt-get -q -y install libglu1-mesa:i386
apt-get -q -y install libglu1:i386
apt-get -q -y install libgl1-mesa-glx:i386
apt-get -q -y install libudev1:i386
apt-get -q -y install libcgmanager0:i386
apt-get -q -y install wine1.8-i386
apt-get -q -y install wine1.8 wine-gecko2.34 wine-mono4.5.4 winetricks
EOF
    chmod +x "${__build_dir}/apt-wine.sh"
    sudo "${__build_dir}/apt-wine.sh"
fi

if [ -z "$(which winepath)" ]; then
    (>&2 echo "Unable to use winepath which is necessary to cross build. Please install wine first.")
    exit 1
fi

CROSSBUILD_INSTALL_PREFIX_WINE="$(winepath -w "$(readlink -f ${CROSSBUILD_INSTALL_PREFIX})")"
WINDOWS_INSTALL_PREFIX="$(readlink -f "$(winepath -u c:\\windows)")"

if [ "${__update_registry_path}" = "1" ]; then
    # Update registry path to append install prefix, this will be necessary for
    # Windows programs to run (for example PyQt configuration is read using an 
    # executable linked with the Qt dlls. It is necessary to kill wineserver
    # before doing changes in registry file because wineserver can save the
    # registry at any time.
    wineserver -k -w
    
    # Add binary prefix to the registry
    ${__build_dir}/update_registry_path \
        --registry-action 'prepend' \
        --value-path "HKLM\\System\\CurrentControlSet\\Control\\Session Manager\\Environment\\PATH" \
        --value "${CROSSBUILD_INSTALL_PREFIX_WINE}\\bin"
fi

# Define variables
# Use pkg-config instead of ${__toolchain}-pkg-config, 
# because on Ubuntu 14.04, it does not allow to use 
# PKG_CONFIG_PATH variable
export PATH=${CROSSBUILD_INSTALL_PREFIX}/bin:${PATH}
export PKG_CONFIG=$(which pkg-config)
export PKG_CONFIG_PATH="${CROSSBUILD_INSTALL_PREFIX}/lib/pkgconfig"
#export PKG_CONFIG_SYSROOT="${CROSSBUILD_INSTALL_PREFIX}/lib/pkgconfig"
#export PKG_CONFIG_SYSROOT_DIR="${CROSSBUILD_INSTALL_PREFIX}/lib/pkgconfig"
#export PATH="${CROSSBUILD_INSTALL_PREFIX}/bin:${PATH}"

set_toolchain

# ------------------------------------------------------------------------------
# Summary
# ------------------------------------------------------------------------------
echo "============================== SUMMARY ==============================="
if [ "${__download}" == "1" ]; then
    echo "* Download in directory ${__download_dir}"
fi
if [ "${__remove_before_install}" == "1" ]; then
    echo "* Existing install directories will be deleted"
fi
if [ "${__update_registry_path}" == "1" ]; then
    echo "* Wine registry PATH variable will be updated"
fi
if [ "${__fix_python_scripts}" == "1" ]; then
    echo "* Installed python scripts will be fixed"
fi
if [ "${__install}" == "1" ]; then
    echo "* Build in directory ${__build_dir}"
    echo "* Build using ${__build_proc_num} procs"
    echo "* Build using toolchain ${__toolchain}"
    echo "* Install in"
    echo "*   => windows directory ${CROSSBUILD_INSTALL_PREFIX_WINE}"
    echo "*   => linux directory ${CROSSBUILD_INSTALL_PREFIX}"
fi
if [ "${SYSTEM}" == "1" ]; then
    __displayed_header=0
    for p in ${__sys_packages[@]}; do
        if [ ${__displayed_header} -eq 0 ]; then
            echo "* System packages"
            __displayed_header=1
        fi
        echo "*   ${p}"
    done
fi
__displayed_header=0
for p in ${__build_packages[@]}; do
    __var_name="${p^^}"
    if [ "${!__var_name}" == "1" ]; then
        if [ ${__displayed_header} -eq 0 ]; then
            echo "* Cross build packages"
            __displayed_header=1
        fi
        echo "*   ${p}"
    fi
done
__displayed_header=0
for p in ${__build_libs[@]}; do
    __var_name="${p^^}"
    if [ "${!__var_name}" == "1" ]; then
        if [ ${__displayed_header} -eq 0 ]; then
            echo "* Cross build libraries"
            __displayed_header=1
        fi
        echo "*   ${p}"
    fi
done
__displayed_header=0
for p in ${__build_python_mods[@]}; do
    __var_name="${p^^}"
    if [ "${!__var_name}" == "1" ]; then
        if [ ${__displayed_header} -eq 0 ]; then
            echo "* Cross build python modules"
            __displayed_header=1
        fi
        echo "*   ${p}"
    fi
done

# ------------------------------------------------------------------------------
# Mingw64
# ------------------------------------------------------------------------------
if [ "${__install}" == "1" ] && [ "${MINGW64}"  == "1" ]; then
    echo "=========================== MINGW64 =============================="
    sudo apt-get -q -y install binutils-mingw-w64 \
                               binutils-mingw-w64-i686 \
                               binutils-mingw-w64-x86-64 \
                               g++-mingw-w64 \
                               g++-mingw-w64-i686 \
                               g++-mingw-w64-x86-64 \
                               gcc-mingw-w64 \
                               gcc-mingw-w64-base \
                               gcc-mingw-w64-i686 \
                               gcc-mingw-w64-x86-64 \
                               gdb-mingw-w64 \
                               gdb-mingw-w64-target \
                               gfortran-mingw-w64 \
                               gfortran-mingw-w64-i686 \
                               gfortran-mingw-w64-x86-64 \
                               gnat-mingw-w64 \
                               gnat-mingw-w64-base \
                               gnat-mingw-w64-i686 \
                               gnat-mingw-w64-x86-64 \
                               mingw-w64 \
                               mingw-w64-common \
                               mingw-w64-i686-dev \
                               mingw-w64-tools \
                               mingw-w64-x86-64-dev \
                               mingw32 \
                               mingw32-binutils \
                               mingw32-runtime
fi

# get version once mingw64 has been installed
MINGW64_VERSION=$(${__toolchain}-gcc -v 2>&1 | grep 'gcc version' | sed -r 's/gcc version\s(([0-9]+[.]){0,2}[0-9]+).*/\1/')
MINGW64_LIB_PREFIX=/usr/lib/gcc/${__toolchain}/${MINGW64_VERSION%.*}
MINGW64_GCC_LIB_PREFIX=/usr/${__toolchain}/lib

if [ "${__install}" == "1" ] && [ "${MINGW64}" == "1" ]; then
    # Must copy libgcc libgfortran libquadmath libstdc++
    # to binaries directory
    pushd ${CROSSBUILD_INSTALL_PREFIX}
    mkdir -p mingw64-${MINGW64_VERSION}/bin
    mkdir -p mingw64-${MINGW64_VERSION}/lib

    ln -fs mingw64-${MINGW64_VERSION} mingw64
    pushd mingw64
    pushd bin
    cp -f ${MINGW64_LIB_PREFIX}/libgcc*.dll \
          ${MINGW64_LIB_PREFIX}/libgfortran*.dll \
          ${MINGW64_LIB_PREFIX}/libquadmath*.dll \
          ${MINGW64_LIB_PREFIX}/libstdc++*.dll \
          ${MINGW64_GCC_LIB_PREFIX}/libwinpthread*.dll \
          ./
    popd
    pushd lib
    cp -f ${MINGW64_LIB_PREFIX}/libgcc*.dll.a \
          ${MINGW64_LIB_PREFIX}/libgfortran*.dll.a \
          ${MINGW64_LIB_PREFIX}/libquadmath*.dll.a \
          ${MINGW64_LIB_PREFIX}/libstdc++*.dll.a \
          ${MINGW64_GCC_LIB_PREFIX}/libwinpthread*.dll.a \
          ./
    popd
    popd
    pushd bin;ln -fs ../mingw64/bin/*.* ./;popd
    pushd lib;ln -fs ../mingw64/lib/*.* ./;popd
    popd
fi

# ------------------------------------------------------------------------------
# Python 2
# ------------------------------------------------------------------------------
PYTHON_VERSION=2.7.11
PYTHON_VERSION_MINOR=${PYTHON_VERSION%.*}
PYTHON_VERSION_HEX=$(${PYTHON_HOST_COMMAND} -c "version='${PYTHON_VERSION}';version_arr=version.split('.');version_arr=[(int(version_arr[i]) << ((abs(i) - 1)  * 8)) for i in xrange(-1, -len(version_arr) - 1, -1)];print hex(sum(version_arr))")
PYTHON_INSTALL_PREFIX=${CROSSBUILD_INSTALL_PREFIX}/python-${PYTHON_VERSION}
PYTHON_INSTALL_PREFIX_WINE=${CROSSBUILD_INSTALL_PREFIX_WINE}\\python-${PYTHON_VERSION}

if [ "${__arch}" == "x86_64" ]; then
    PYTHON_ARCH_SUFFIX=.amd64
    PYTHON_WIN_ARCH_SUFFIX=win_amd64
    PYTHON_CFLAGS="-DMS_WIN64 -I${PYTHON_INSTALL_PREFIX}/include"
    PYTHON_CPPFLAGS="-DMS_WIN64 -I${PYTHON_INSTALL_PREFIX}/include"
    PYTHON_LDFLAGS="${PYTHON_INSTALL_PREFIX}/DLLs/python${PYTHON_VERSION_MINOR//./}.dll"
else
    PYTHON_WIN_ARCH_SUFFIX=win32
    PYTHON_CFLAGS="-I${PYTHON_INSTALL_PREFIX}/include"
    PYTHON_CPPFLAGS="-I${PYTHON_INSTALL_PREFIX}/include"
    PYTHON_LDFLAGS="${PYTHON_INSTALL_PREFIX}/DLLs/python${PYTHON_VERSION_MINOR//./}.dll"
fi

PYTHON_SOURCE_URL=https://www.python.org/ftp/python/${PYTHON_VERSION}/python-${PYTHON_VERSION}${PYTHON_ARCH_SUFFIX}.msi

if [ "${PYTHON}"  == "1" ]; then
    echo "=============================== PYTHON ==============================="
    if [ "${__download}" == "1" ]; then
        download "${__arch}" ${PYTHON_SOURCE_URL}
    fi

    if [ "${__remove_before_install}" == "1"  ]; then
        remove ${PYTHON_INSTALL_PREFIX}
    fi

    if [ "${__install}" == "1" ]; then
        # echo "wine cmd: ${__wine_cmd}"
        # echo "download file: ${__download_dir}/python-${PYTHON_VERSION}${PYTHON_ARCH_SUFFIX}.msi"
        # echo "log file: python-${PYTHON_VERSION}-install.log"
        # echo "target dir: ${PYTHON_INSTALL_PREFIX_WINE}"
        ${__wine_cmd} msiexec \
        /i ${__download_dir}/python-${PYTHON_VERSION}${PYTHON_ARCH_SUFFIX}.msi \
        /L*v python-${PYTHON_VERSION}-install.log \
        /qn TARGETDIR=${PYTHON_INSTALL_PREFIX_WINE} ALLUSERS=1 \
        || exit 1
        
        if [ -d "${WINDOWS_INSTALL_PREFIX}" ]; then
            # I do not understand why, but under ubuntu 14.04 64-bits, python installer 64-bits installs 
            # python dll in ${WINDOWS_INSTALL_PREFIX}/system32 whereas python installer 32-bits installs 
            # python dll in ${WINDOWS_INSTALL_PREFIX}/syswow64
            if [ "${__arch}" == "x86_64" ]; then
                PYTHON_WIN_SYS_DIR=${WINDOWS_INSTALL_PREFIX}/system32
            else
                PYTHON_WIN_SYS_DIR=${WINDOWS_INSTALL_PREFIX}/syswow64
            fi
            cp -f "${PYTHON_WIN_SYS_DIR}/python${PYTHON_VERSION_MINOR//./}.dll" ${PYTHON_INSTALL_PREFIX}/DLLs
        fi
        pushd ${CROSSBUILD_INSTALL_PREFIX}

        ln -fs python-${PYTHON_VERSION} python
        pushd bin;ln -fs ../python/*.exe ./;
                  ln -fs ../python/DLLs/*.dll ./;
                  ln -fs ../python/Scripts/easy_install.exe \
                         ../python/Scripts/easy_install-2.7.exe \
                         ./;
        popd
        pushd lib;ln -fs ../python/libs/*.* ./;popd
        pushd include;ln -fs ../python/include ./python${PYTHON_VERSION_MINOR};popd


        # Add links to python scripts
        popd
    fi
    
    if [ "${__update_registry_path}" = "1" ]; then
        # Update registry path to append install prefix, this will be necessary for
        # Windows programs to run (for example PyQt configuration is read using an 
        # executable linked with the Qt dlls. It is necessary to kill wineserver
        # before doing changes in registry file because wineserver can save the
        # registry at any time.
        wineserver -k -w
        
        # Add binary prefix to the registry
        ${__build_dir}/update_registry_path \
            --value-path "HKLM\\System\\CurrentControlSet\\Control\\Session Manager\\Environment\\PYTHONHOME" \
            --value "${PYTHON_INSTALL_PREFIX_WINE}"
    fi
    
    if [ "${__fix_python_scripts}" == "1" ]; then
        for __script in easy_install.exe easy_install-2.7.exe; do
            fix_python_script ${PYTHON_INSTALL_PREFIX}/Scripts/${__script}
        done
    fi

fi

# ------------------------------------------------------------------------------
# libiconv
# ------------------------------------------------------------------------------
LIBICONV_VERSION=1.14
LIBICONV_INSTALL_PREFIX=${CROSSBUILD_INSTALL_PREFIX}/libiconv-${LIBICONV_VERSION}
LIBICONV_SOURCE_URL=https://ftp.gnu.org/pub/gnu/libiconv/libiconv-${LIBICONV_VERSION}.tar.gz
if [ "${LIBICONV}"  == "1" ]; then
    echo "============================== LIBICONV =============================="
    if [ "${__download}" == "1" ]; then
        download ${LIBICONV_SOURCE_URL}
    fi

    if [ "${__remove_before_install}" == "1"  ]; then
        remove ${LIBICONV_INSTALL_PREFIX}
    fi

    if [ "${__install}" == "1" ]; then
        tar xvf ${__download_dir}/libiconv-${LIBICONV_VERSION}.tar.gz
        pushd ${__build_dir}/libiconv-${LIBICONV_VERSION}
        ./configure \
                --build=${__buildtype} \
                --host=${__toolchain} \
                --prefix=${LIBICONV_INSTALL_PREFIX} \
        || exit 1
        make -j${__build_proc_num} install || exit 1

        pushd ${CROSSBUILD_INSTALL_PREFIX}
        ln -fs libiconv-${LIBICONV_VERSION} libiconv
        pushd bin;ln -fs ../libiconv/bin/*.* ./;popd
        pushd lib;ln -fs ../libiconv/lib/*.* ./;popd
        pushd include;ln -fs ../libiconv/include/* ./;popd
        popd
        popd
    fi
fi

# ------------------------------------------------------------------------------
# zlib
# ------------------------------------------------------------------------------
ZLIB_VERSION=1.2.8
ZLIB_INSTALL_PREFIX=${CROSSBUILD_INSTALL_PREFIX}/zlib-${ZLIB_VERSION}
ZLIB_SOURCE_URL=http://sourceforge.mirrorservice.org/l/li/libpng/zlib/${ZLIB_VERSION}/zlib-${ZLIB_VERSION}.tar.gz
if [ "${ZLIB}" == "1" ]; then
    echo "================================ ZLIB ================================"
    if [ "${__download}" == "1" ]; then
        download ${ZLIB_SOURCE_URL}
    fi

    if [ "${__remove_before_install}" == "1"  ]; then
        remove ${ZLIB_INSTALL_PREFIX}
    fi

    if [ "${__install}" == "1" ]; then
        tar xvf ${__download_dir}/zlib-${ZLIB_VERSION}.tar.gz
        pushd ${__build_dir}/zlib-${ZLIB_VERSION}
        cmake -DCMAKE_INSTALL_PREFIX=${ZLIB_INSTALL_PREFIX} \
              -DCMAKE_TOOLCHAIN_FILE=${__build_dir}/toolchain-${__toolchain}.cmake \
              -DCMAKE_CROSSCOMPILING=ON \
        || exit 1
        make -j${__build_proc_num} install || exit 1

        pushd ${CROSSBUILD_INSTALL_PREFIX}
        rm -f zlib && ln -fs zlib-${ZLIB_VERSION} zlib
        pushd zlib-${ZLIB_VERSION}/bin;
              ln -fs libzlib.dll libz.dll;popd
        pushd zlib-${ZLIB_VERSION}/lib;
              ln -fs libzlib.dll.a libz.dll.a;
              ln -fs libzlibstatic.a libzstatic.a;popd
        pushd bin;ln -fs ../zlib/bin/*.* ./;popd
        pushd lib;ln -fs ../zlib/lib/*.* ./;popd
        pushd include;ln -fs ../zlib/include/* ./;popd
        pushd lib/pkgconfig;ln -fs ../../zlib/share/pkgconfig/* ./;popd
        popd
        popd
    fi
fi

# ------------------------------------------------------------------------------
# bzip2
# ------------------------------------------------------------------------------
BZIP2_VERSION=1.0.6
BZIP2_INSTALL_PREFIX=${CROSSBUILD_INSTALL_PREFIX}/bzip2-${BZIP2_VERSION}
BZIP2_SOURCE_URL=http://www.bzip.org/${BZIP2_VERSION}/bzip2-${BZIP2_VERSION}.tar.gz
if [ "${BZIP2}" == "1" ]; then
    echo "============================== BZIP2 ================================="
    if [ "${__download}" == "1" ]; then
        download ${BZIP2_SOURCE_URL}
    fi

    if [ "${__remove_before_install}" == "1"  ]; then
        remove ${BZIP2_INSTALL_PREFIX}
    fi

    if [ "${__install}" == "1" ]; then
        tar xvf ${__download_dir}/bzip2-${BZIP2_VERSION}.tar.gz
        pushd ${__build_dir}/bzip2-${BZIP2_VERSION}
        ./configure \
                --build=${__buildtype} \
                --host=${__toolchain} \
                --prefix=${BZIP2_INSTALL_PREFIX} \
        || exit 1

        make -j${__build_proc_num} install || exit 1

        pushd ${CROSSBUILD_INSTALL_PREFIX}
        rm -f bzip2 && ln -fs bzip2-${BZIP2_VERSION} bzip2
        pushd bin;ln -fs ../bzip2/bin/*.* ./;popd
        pushd lib;ln -fs ../bzip2/lib/*.* ./;popd
        pushd include;ln -fs ../bzip2/include/* ./;popd
        pushd lib/pkgconfig;ln -fs ../../bzip2/lib/pkgconfig/* ./;popd

        popd
        popd
    fi
fi

# ------------------------------------------------------------------------------
# libxml2
# ------------------------------------------------------------------------------
LIBXML2_VERSION=2.7.8
LIBXML2_INSTALL_PREFIX=${CROSSBUILD_INSTALL_PREFIX}/libxml2-${LIBXML2_VERSION}
LIBXML2_SOURCE_URL=ftp://xmlsoft.org/libxml2/libxml2-sources-${LIBXML2_VERSION}.tar.gz
if [ "${LIBXML2}" == "1" ]; then
    echo "=============================== LIBXML2 =============================="
    if [ "${__download}" == "1" ]; then
        download ${LIBXML2_SOURCE_URL}
    fi

    if [ "${__remove_before_install}" == "1"  ]; then
        remove ${LIBXML2_INSTALL_PREFIX}
    fi

    if [ "${__install}" == "1" ]; then
        tar xvf ${__download_dir}/libxml2-sources-${LIBXML2_VERSION}.tar.gz
        pushd ${__build_dir}/libxml2-${LIBXML2_VERSION}
        ./configure \
                --build=${__buildtype} \
                --host=${__toolchain} \
                --prefix=${LIBXML2_INSTALL_PREFIX} \
                --with-python=${PYTHON_INSTALL_PREFIX} \
        || exit 1
        make -j${__build_proc_num} install || exit 1

        pushd ${CROSSBUILD_INSTALL_PREFIX}
        rm -f libxml2 && ln -fs libxml2-${LIBXML2_VERSION} libxml2
        pushd bin;ln -fs ../libxml2/bin/*.* ./;popd
        pushd lib;ln -fs ../libxml2/lib/*.* ./;popd
        pushd include;ln -fs ../libxml2/include/* ./;popd
        pushd lib/pkgconfig;ln -fs ../../libxml2/lib/pkgconfig/* ./;popd
        popd
        popd
    fi
fi

# ------------------------------------------------------------------------------
# expat
# ------------------------------------------------------------------------------
EXPAT_VERSION=2.1.0
EXPAT_INSTALL_PREFIX=${CROSSBUILD_INSTALL_PREFIX}/expat-${EXPAT_VERSION}
EXPAT_SOURCE_URL=http://sourceforge.mirrorservice.org/e/ex/expat/expat/${EXPAT_VERSION}/expat-${EXPAT_VERSION}.tar.gz
if [ "${EXPAT}" == "1" ]; then
    echo "================================ EXPAT ==============================="
    if [ "${__download}" == "1" ]; then
        download ${EXPAT_SOURCE_URL}
    fi

    if [ "${__remove_before_install}" == "1"  ]; then
        remove ${EXPAT_INSTALL_PREFIX}
    fi

    if [ "${__install}" == "1" ]; then
        tar xvf ${__download_dir}/expat-${EXPAT_VERSION}.tar.gz
        pushd ${__build_dir}/expat-${EXPAT_VERSION}

        # Generate patch to build shared library
        cat << EOF > expat-${EXPAT_VERSION}.patch
diff -NurwB --strip-trailing-cr --suppress-common-lines Makefile.in Makefile.in
--- Makefile.in	2016-09-27 17:14:25.945876843 +0200
+++ Makefile.in	2016-09-27 17:14:28.977876607 +0200
@@ -79,7 +79,7 @@
 
 install: xmlwf/xmlwf@EXEEXT@ installlib
 	\$(mkinstalldirs) \$(DESTDIR)\$(bindir) \$(DESTDIR)\$(man1dir)
-	\$(LIBTOOL) --mode=install \$(INSTALL_PROGRAM) xmlwf/xmlwf@EXEEXT@ \$(DESTDIR)\$(bindir)/xmlwf
+	\$(LIBTOOL) --mode=install \$(INSTALL_PROGRAM) xmlwf/xmlwf@EXEEXT@ \$(DESTDIR)\$(bindir)/xmlwf@EXEEXT@
 	\$(INSTALL_DATA) \$(MANFILE) \$(DESTDIR)\$(man1dir)
 
 installlib: \$(LIBRARY) \$(APIHEADER) expat.pc
EOF
        patch -f -N -i expat-${EXPAT_VERSION}.patch -p0
        ./configure \
                --build=${__buildtype} \
                --host=${__toolchain} \
                --prefix=${EXPAT_INSTALL_PREFIX} \
        || exit 1
        make -j${__build_proc_num} install || exit 1

        pushd ${CROSSBUILD_INSTALL_PREFIX}
        rm -f expat && ln -fs expat-${EXPAT_VERSION} expat
        pushd bin;ln -fs ../expat/bin/*.* ./;popd
        pushd lib;ln -fs ../expat/lib/*.* ./;popd
        pushd include;ln -fs ../expat/include/* ./;popd
        pushd lib/pkgconfig;ln -fs ../../expat/lib/pkgconfig/* ./;popd
        popd
        popd
    fi
fi

# ------------------------------------------------------------------------------
# hdf5
# ------------------------------------------------------------------------------
HDF5_VERSION=1.8.11
HDF5_INSTALL_PREFIX=${CROSSBUILD_INSTALL_PREFIX}/hdf5-${HDF5_VERSION}
HDF5_SOURCE_URL=https://support.hdfgroup.org/ftp/HDF5/prev-releases/hdf5-${HDF5_VERSION}/src/hdf5-${HDF5_VERSION}.tar.gz
if [ "${HDF5}" == "1" ]; then
    echo "================================ HDF5 ==============================="
    if [ "${__download}" == "1" ]; then
        download ${HDF5_SOURCE_URL}
    fi

    if [ "${__remove_before_install}" == "1"  ]; then
        remove ${HDF5_INSTALL_PREFIX}
    fi

    if [ "${__install}" == "1" ]; then
        tar xvf ${__download_dir}/hdf5-${HDF5_VERSION}.tar.gz
        pushd ${__build_dir}/hdf5-${HDF5_VERSION}

        # Generate cache to be able to configure for cross compilation
        # The problem is that TRY_RUN is used and executable can not be run
        # on build platform, so we need to set test values manually
        cat << EOF > ${__build_dir}/hdf5-${HDF5_VERSION}-cache.cmake
SET( HAVE_IOEO_EXITCODE 
     "1"
     CACHE STRING "Result from TRY_RUN" FORCE)

SET( HDF5_PRINTF_LL_TEST_RUN 
     "0"
     CACHE STRING "Result from TRY_RUN" FORCE)

SET( HDF5_PRINTF_LL_TEST_RUN__TRYRUN_OUTPUT 
     "PRINTF_LL_WIDTH=[ll]"
     CACHE STRING "Output from TRY_RUN" FORCE)

SET( H5_LDOUBLE_TO_INTEGER_WORKS_RUN 
     "0"
     CACHE STRING "Result from TRY_RUN" FORCE)

SET( H5_LDOUBLE_TO_INTEGER_WORKS_RUN__TRYRUN_OUTPUT 
     ""
     CACHE STRING "Output from TRY_RUN" FORCE)

SET( H5_ULONG_TO_FLOAT_ACCURATE_RUN 
     "0"
     CACHE STRING "Result from TRY_RUN" FORCE)

SET( H5_ULONG_TO_FLOAT_ACCURATE_RUN__TRYRUN_OUTPUT 
     ""
     CACHE STRING "Output from TRY_RUN" FORCE)

SET( H5_ULONG_TO_FP_BOTTOM_BIT_ACCURATE_RUN 
     "1"
     CACHE STRING "Result from TRY_RUN" FORCE)

SET( H5_ULONG_TO_FP_BOTTOM_BIT_ACCURATE_RUN__TRYRUN_OUTPUT 
     ""
     CACHE STRING "Output from TRY_RUN" FORCE)

SET( H5_FP_TO_ULLONG_ACCURATE_RUN 
     "0"
     CACHE STRING "Result from TRY_RUN" FORCE)

SET( H5_FP_TO_ULLONG_ACCURATE_RUN__TRYRUN_OUTPUT 
     ""
     CACHE STRING "Output from TRY_RUN" FORCE)

SET( H5_LDOUBLE_TO_UINT_ACCURATE_RUN 
     "0"
     CACHE STRING "Result from TRY_RUN" FORCE)

SET( H5_LDOUBLE_TO_UINT_ACCURATE_RUN__TRYRUN_OUTPUT 
     ""
     CACHE STRING "Output from TRY_RUN" FORCE)

SET( H5_ULLONG_TO_LDOUBLE_PRECISION_RUN 
     "0"
     CACHE STRING "Result from TRY_RUN" FORCE)

SET( H5_ULLONG_TO_LDOUBLE_PRECISION_RUN__TRYRUN_OUTPUT 
     ""
     CACHE STRING "Output from TRY_RUN" FORCE)

SET( H5_FP_TO_INTEGER_OVERFLOW_WORKS_RUN 
     "0"
     CACHE STRING "Result from TRY_RUN" FORCE)

SET( H5_FP_TO_INTEGER_OVERFLOW_WORKS_RUN__TRYRUN_OUTPUT 
     ""
     CACHE STRING "Output from TRY_RUN" FORCE)

SET( H5_LDOUBLE_TO_LLONG_ACCURATE_RUN 
     "0"
     CACHE STRING "Result from TRY_RUN" FORCE)

SET( H5_LDOUBLE_TO_LLONG_ACCURATE_RUN__TRYRUN_OUTPUT 
     ""
     CACHE STRING "Output from TRY_RUN" FORCE)

SET( H5_LLONG_TO_LDOUBLE_CORRECT_RUN 
     "0"
     CACHE STRING "Result from TRY_RUN" FORCE)

SET( H5_LLONG_TO_LDOUBLE_CORRECT_RUN__TRYRUN_OUTPUT 
     ""
     CACHE STRING "Output from TRY_RUN" FORCE)

SET( H5_NO_ALIGNMENT_RESTRICTIONS_RUN 
     "0"
     CACHE STRING "Result from TRY_RUN" FORCE)

SET( H5_NO_ALIGNMENT_RESTRICTIONS_RUN__TRYRUN_OUTPUT 
     ""
     CACHE STRING "Output from TRY_RUN" FORCE)

EOF
        # Generate patch to build shared library
        cat << EOF > hdf5-${HDF5_VERSION}.patch
diff -NurwB --strip-trailing-cr --suppress-common-lines config/cmake/HDFMacros.cmake config/cmake/HDFMacros.cmake
--- config/cmake/HDFMacros.cmake    2016-09-30 17:17:01.747939198 +0200
+++ config/cmake/HDFMacros.cmake    2016-09-30 17:23:11.019851626 +0200
@@ -109,14 +109,14 @@
   )
   
   #----- Use MSVC Naming conventions for Shared Libraries
-  IF (MINGW AND \${libtype} MATCHES "SHARED")
+  IF (MINGW AND (\${libtype} MATCHES "SHARED") AND (NOT CMAKE_CROSSCOMPILING))
     SET_TARGET_PROPERTIES (\${libtarget}
         PROPERTIES
         IMPORT_SUFFIX ".lib"
         IMPORT_PREFIX ""
         PREFIX ""
     )
-  ENDIF (MINGW AND \${libtype} MATCHES "SHARED")
+  ENDIF (MINGW AND (\${libtype} MATCHES "SHARED") AND (NOT CMAKE_CROSSCOMPILING))
 
 ENDMACRO (HDF_SET_LIB_OPTIONS)

diff -NurB --strip-trailing-cr --suppress-common-lines src/CMakeLists.txt src/CMakeLists.txt
--- src/CMakeLists.txt  2017-07-18 17:29:58.631026771 +0200
+++ src/CMakeLists.txt  2017-07-18 17:35:48.654774168 +0200
@@ -621,8 +621,7 @@
 SET (CMD \$<TARGET_FILE:H5detect>)
 ADD_CUSTOM_COMMAND (
     OUTPUT \${HDF5_BINARY_DIR}/H5Tinit.c
-    COMMAND \${CMD}
-    ARGS > \${HDF5_BINARY_DIR}/H5Tinit.c
+    COMMAND \${CMAKE_CROSSCOMPILING_RUN_COMMAND} \${CMD} > \${HDF5_BINARY_DIR}/H5Tinit.c
     DEPENDS H5detect
 )
 
@@ -634,8 +633,7 @@
 SET (CMD \$<TARGET_FILE:H5make_libsettings>)
 ADD_CUSTOM_COMMAND (
     OUTPUT \${HDF5_BINARY_DIR}/H5lib_settings.c
-    COMMAND \${CMD}
-    ARGS > \${HDF5_BINARY_DIR}/H5lib_settings.c
+    COMMAND \${CMAKE_CROSSCOMPILING_RUN_COMMAND} \${CMD} > \${HDF5_BINARY_DIR}/H5lib_settings.c
     DEPENDS H5make_libsettings
     WORKING_DIRECTORY \${HDF5_BINARY_DIR}
 )
 
EOF
        patch -f -N -i hdf5-${HDF5_VERSION}.patch -p0

        cmake -C ${__build_dir}/hdf5-${HDF5_VERSION}-cache.cmake \
              -DCMAKE_INSTALL_PREFIX=${HDF5_INSTALL_PREFIX} \
              -DCMAKE_TOOLCHAIN_FILE=${__build_dir}/toolchain-${__toolchain}.cmake \
              -DCMAKE_CROSSCOMPILING=ON \
              -DCMAKE_CROSSCOMPILING_RUN_COMMAND=${__wine_cmd} \
              -DBUILD_SHARED_LIBS=ON \
              -DHDF5_BUILD_TOOLS=ON \
              -DHDF5_BUILD_HL_LIB=ON \
              -DHDF5_BUILD_CPP_LIB=ON \
              -DHDF5_ENABLE_THREADSAFE=ON \
              -DHDF5_BUILD_EXAMPLES=ON \
              -DH5_HAVE_PTHREAD_H=ON \
              -DHDF_LEGACY_NAMING=ON \
              -DCMAKE_C_STANDARD_LIBRARIES="-lws2_32 -lnetapi32 -lwsock32" \
              -DCMAKE_CXX_STANDARD_LIBRARIES="-lws2_32 -lnetapi32 -lwsock32" \
              . \
        || exit 1
        make -j${__build_proc_num} install || exit 1

        pushd ${CROSSBUILD_INSTALL_PREFIX}
        rm -f hdf5 && ln -fs hdf5-${HDF5_VERSION} hdf5
        pushd bin;ln -fs ../hdf5/bin/*.* ./;popd
        pushd lib;ln -fs ../hdf5/lib/*.* ./;popd
        pushd include;ln -fs ../hdf5/include/* ./;popd
#        pushd lib/pkgconfig;ln -fs ../../hdf5/lib/pkgconfig/* ./;popd
        popd
        popd
    fi
fi

# ------------------------------------------------------------------------------
# gettext
# ------------------------------------------------------------------------------
GETTEXT_VERSION=0.18.3.2
#GETTEXT_VERSION=0.19.8.1
GETTEXT_INSTALL_PREFIX=${CROSSBUILD_INSTALL_PREFIX}/gettext-${GETTEXT_VERSION}
GETTEXT_SOURCE_URL=https://ftp.gnu.org/pub/gnu/gettext/gettext-${GETTEXT_VERSION}.tar.gz
if [ "${GETTEXT}" == "1" ]; then
    echo "============================== GETTEXT ==============================="
    if [ "${__download}" == "1" ]; then
        download ${GETTEXT_SOURCE_URL}
    fi

    if [ "${__remove_before_install}" == "1"  ]; then
        remove ${GETTEXT_INSTALL_PREFIX}
    fi

    if [ "${__install}" == "1" ]; then
        tar xvf ${__download_dir}/gettext-${GETTEXT_VERSION}.tar.gz
        pushd ${__build_dir}/gettext-${GETTEXT_VERSION}
        
        # Generate patch to build shared library
        cat << EOF > gettext-${GETTEXT_VERSION}.patch
diff -NurwB --strip-trailing-cr --suppress-common-lines gettext-runtime/intl/printf.c gettext-runtime/intl/printf.c
--- gettext-runtime/intl/printf.c    2016-07-20 17:30:08.733584387 +0200
+++ gettext-runtime/intl/printf.c    2016-07-21 10:49:25.331397770 +0200
@@ -308,7 +308,7 @@
 #include "asnprintf.c"
 #endif
 
-# if HAVE_DECL__SNWPRINTF
+# if HAVE_DECL__SNWPRINTF || WIN32
    /* Windows.  The function vswprintf() has a different signature than
       on Unix; we use the function _vsnwprintf() instead.  */
 #  define system_vswprintf _vsnwprintf
EOF
        patch -f -N -i gettext-${GETTEXT_VERSION}.patch -p0

        # Due to a bug in the library, it is necessary to build with -O2
        CFLAGS="-O2 ${CFLAGS}" \
        CXXFLAGS="-O2 ${CXXFLAGS}" \
        ./configure \
                --build=${__buildtype} \
                --host=${__toolchain} \
                --prefix=${GETTEXT_INSTALL_PREFIX} \
        || exit 1
        make -j${__build_proc_num} install || exit 1

        pushd ${CROSSBUILD_INSTALL_PREFIX}
        rm -f getext && ln -fs gettext-${GETTEXT_VERSION} gettext
        pushd bin;ln -fs ../gettext/bin/*.* ./;popd
        pushd lib;ln -fs ../gettext/lib/*.* ./;popd
        pushd include;ln -fs ../gettext/include/* ./;popd
        popd
        popd
    fi
fi

# ------------------------------------------------------------------------------
# sqlite3
# ------------------------------------------------------------------------------
SQLITE_VERSION=3.8.2
SQLITE_VERSION_STD=$(${PYTHON_HOST_COMMAND} -c "import string; print '{0:0<7s}'.format(string.replace('${SQLITE_VERSION}', '.', '0'))")
SQLITE_INSTALL_PREFIX=${CROSSBUILD_INSTALL_PREFIX}/sqlite3-${SQLITE_VERSION}
SQLITE_SOURCE_URL=http://www.sqlite.org/2013/sqlite-autoconf-${SQLITE_VERSION_STD}.tar.gz
if [ "${SQLITE}" == "1" ]; then
    echo "=============================== SQLITE ==============================="
    if [ "${__download}" == "1" ]; then
        download ${SQLITE_SOURCE_URL}
    fi

    if [ "${__remove_before_install}" == "1"  ]; then
        remove ${SQLITE_INSTALL_PREFIX}
    fi

    if [ "${__install}" == "1" ]; then
        tar xvf ${__download_dir}/sqlite-autoconf-${SQLITE_VERSION_STD}.tar.gz
        pushd ${__build_dir}/sqlite-autoconf-${SQLITE_VERSION_STD}
        ./configure \
                --build=${__buildtype} \
                --host=${__toolchain} \
                --prefix=${SQLITE_INSTALL_PREFIX} \
                --with-python=${PYTHON_INSTALL_PREFIX} \
                --enable-shared \
        || exit 1
        make -j${__build_proc_num} install || exit 1

        pushd ${CROSSBUILD_INSTALL_PREFIX}
        rm -f sqlite3 && ln -fs sqlite3-${SQLITE_VERSION} sqlite3
        pushd bin;ln -fs ../sqlite3/bin/*.* ./;popd
        pushd lib;ln -fs ../sqlite3/lib/*.* ./;popd
        pushd include;ln -fs ../sqlite3/include/* ./;popd
        pushd lib/pkgconfig;ln -fs ../../sqlite3/lib/pkgconfig/* ./;popd
        popd
        popd
    fi
fi

# ------------------------------------------------------------------------------
# libsigc++
# ------------------------------------------------------------------------------
LIBSIGCPP_VERSION=2.1.1
LIBSIGCPP_INSTALL_PREFIX=${CROSSBUILD_INSTALL_PREFIX}/libsigc++-${LIBSIGCPP_VERSION}
LIBSIGCPP_SOURCE_URL=http://ftp.gnome.org/pub/GNOME/sources/libsigc++/2.1/libsigc++-${LIBSIGCPP_VERSION}.tar.gz
if [ "${LIBSIGCPP}" == "1" ]; then
    echo "============================== LIBSIGC++ ============================="
    if [ "${__download}" == "1" ]; then
        download ${LIBSIGCPP_SOURCE_URL}
    fi

    if [ "${__remove_before_install}" == "1"  ]; then
        remove ${LIBSIGCPP_INSTALL_PREFIX}
    fi

    if [ "${__install}" == "1" ]; then
        tar xvf ${__download_dir}/libsigc++-${LIBSIGCPP_VERSION}.tar.gz
        pushd ${__build_dir}/libsigc++-${LIBSIGCPP_VERSION}
        cat << EOF > libsigc++-${LIBSIGCPP_VERSION}.patch
diff -NurwB --strip-trailing-cr --suppress-common-lines sigc++/signal_base.h sigc++/signal_base.h
--- sigc++/signal_base.h    2016-07-21 23:19:43.112258845 +0200
+++ sigc++/signal_base.h    2016-07-21 23:18:54.816309160 +0200
@@ -21,6 +21,9 @@
 #ifndef _SIGC_SIGNAL_BASE_H_
 #define _SIGC_SIGNAL_BASE_H_
 
+#include <cstddef>
+#include <cstdlib>
+#include <cstring>
 #include <list>
 #include <sigc++config.h>
 #include <sigc++/type_traits.h>
EOF
        patch -f -N -i libsigc++-${LIBSIGCPP_VERSION}.patch -p0

        ./configure \
                --build=${__buildtype} \
                --host=${__toolchain} \
                --prefix=${LIBSIGCPP_INSTALL_PREFIX} \
        || exit 1
        make -j${__build_proc_num} install || exit 1

        pushd ${CROSSBUILD_INSTALL_PREFIX}
        rm -f libsigc++ && ln -fs libsigc++-${LIBSIGCPP_VERSION} libsigc++
        pushd bin;ln -fs ../libsigc++/bin/*.* ./;popd
        pushd lib;ln -fs ../libsigc++/lib/*.* ./;popd
        pushd include;ln -fs ../libsigc++/include/* ./;popd
        pushd lib/pkgconfig;ln -fs ../../libsigc++/lib/pkgconfig/* ./;popd
        popd
        popd
    fi
fi

# ------------------------------------------------------------------------------
# freetype
# ------------------------------------------------------------------------------
FREETYPE_VERSION=2.4.3
FREETYPE_INSTALL_PREFIX=${CROSSBUILD_INSTALL_PREFIX}/freetype-${FREETYPE_VERSION}
FREETYPE_SOURCE_URL=http://ftp.igh.cnrs.fr/pub/nongnu/freetype/freetype-${FREETYPE_VERSION}.tar.gz
if [ "${FREETYPE}" == "1" ]; then
    echo "============================== FREETYPE =============================="
    if [ "${__download}" == "1" ]; then
        download ${FREETYPE_SOURCE_URL}
    fi

    if [ "${__remove_before_install}" == "1"  ]; then
        remove ${FREETYPE_INSTALL_PREFIX}
    fi

    if [ "${__install}" == "1" ]; then
        tar xvf ${__download_dir}/freetype-${FREETYPE_VERSION}.tar.gz
        pushd ${__build_dir}/freetype-${FREETYPE_VERSION}
        ./configure \
                --build=${__buildtype} \
                --host=${__toolchain} \
                --prefix=${FREETYPE_INSTALL_PREFIX} \
        || exit 1
        make -j${__build_proc_num} install || exit 1
        
        pushd ${CROSSBUILD_INSTALL_PREFIX}
        rm -f freetype && ln -fs freetype-${FREETYPE_VERSION} freetype
        pushd bin;ln -fs ../freetype/bin/*.* ./;popd
        pushd lib;ln -fs ../freetype/lib/*.* ./;popd
        pushd include;ln -fs ../freetype/include/* ./;popd
        pushd lib/pkgconfig;ln -fs ../../freetype/lib/pkgconfig/* ./;popd
        popd
        popd
    fi
fi

# ------------------------------------------------------------------------------
# libregex
# ------------------------------------------------------------------------------
LIBREGEX_VERSION=2.5.1
LIBREGEX_INSTALL_PREFIX=${CROSSBUILD_INSTALL_PREFIX}/libregex-${LIBREGEX_VERSION}
LIBREGEX_SOURCE_URL=http://sourceforge.mirrorservice.org/m/mi/mingw/Other/UserContributed/regex/mingw-regex-${LIBREGEX_VERSION}/mingw-libgnurx-${LIBREGEX_VERSION}-src.tar.gz
if [ "${LIBREGEX}" == "1" ]; then
    echo "============================== LIBREGEX =============================="
    if [ "${__download}" == "1" ]; then
        download ${LIBREGEX_SOURCE_URL}
    fi

    if [ "${__remove_before_install}" == "1"  ]; then
        remove ${LIBREGEX_INSTALL_PREFIX}
    fi

    if [ "${__install}" == "1" ]; then
        tar xvf ${__download_dir}/mingw-libgnurx-${LIBREGEX_VERSION}-src.tar.gz
        pushd ${__build_dir}/mingw-libgnurx-${LIBREGEX_VERSION}
        ./configure \
                --build=${__buildtype} \
                --host=${__toolchain} \
                --prefix=${LIBREGEX_INSTALL_PREFIX} \
        || exit 1
        make -j${__build_proc_num}
        make -j${__build_proc_num} install || exit 1

        pushd ${CROSSBUILD_INSTALL_PREFIX}
        rm -f libregex && ln -fs libregex-${LIBREGEX_VERSION} libregex
        pushd ${LIBREGEX_INSTALL_PREFIX}/lib;ln -fs libgnurx.dll.a libregex.dll.a;popd
        pushd bin;ln -fs ../libregex/bin/*.* ./;popd
        pushd lib;ln -fs ../libregex/lib/*.* ./;popd
        pushd include;ln -fs ../libregex/include/* ./;popd
        popd
        popd
    fi
fi

# ------------------------------------------------------------------------------
# boost
# ------------------------------------------------------------------------------
BOOST_VERSION=1.54.0
BOOST_INSTALL_PREFIX=${CROSSBUILD_INSTALL_PREFIX}/boost-${BOOST_VERSION}
BOOST_SOURCE_URL=http://sourceforge.mirrorservice.org/b/bo/boost/boost/${BOOST_VERSION}/boost_${BOOST_VERSION//./_}.tar.gz
if [ "${BOOST}" == "1" ]; then
    echo "=============================== BOOST ================================"
    if [ "${__download}" == "1" ]; then
        download ${BOOST_SOURCE_URL}
    fi

    if [ "${__remove_before_install}" == "1"  ]; then
        remove ${BOOST_INSTALL_PREFIX}
    fi

    if [ "${__install}" == "1" ]; then
        tar xvf ${__download_dir}/boost_${BOOST_VERSION//./_}.tar.gz
        pushd ${__build_dir}/boost_${BOOST_VERSION//./_}
        ./bootstrap.sh
        cat << EOF > user-config.jam
using gcc : 4.8 : ${__toolchain}-g++ ;
EOF
        #./bjam toolset=gcc target-os=windows variant=debug --with-program_options
        ./b2 toolset=gcc target-os=windows variant=release threading=multi threadapi=win32\
        link=shared runtime-link=shared --prefix=${BOOST_INSTALL_PREFIX} --user-config=user-config.jam -j ${__build_proc_num}\
        --without-mpi --without-python -sNO_BZIP2=1 install
        # -sNO_ZLIB=1 --layout=tagged
        mkdir -p ${BOOST_INSTALL_PREFIX}/bin
        mv -f ${BOOST_INSTALL_PREFIX}/lib/*.dll ${BOOST_INSTALL_PREFIX}/bin

        pushd ${CROSSBUILD_INSTALL_PREFIX}
        rm -f boost && ln -fs boost-${BOOST_VERSION} boost
        pushd bin;ln -fs ../boost/bin/*.* ./;popd
        pushd lib;ln -fs ../boost/lib/*.* ./;popd
        pushd include;ln -fs ../boost/include/* ./;popd
        popd
        popd
    fi
fi

# ------------------------------------------------------------------------------
# blitz
# ------------------------------------------------------------------------------
BLITZ_VERSION=0.10
BLITZ_INSTALL_PREFIX=${CROSSBUILD_INSTALL_PREFIX}/blitz-${BLITZ_VERSION}
BLITZ_SOURCE_URL=http://sourceforge.mirrorservice.org/b/bl/blitz/blitz/Blitz%2B%2B%20${BLITZ_VERSION}/blitz-${BLITZ_VERSION}.tar.gz
if [ "${BLITZ}" == "1" ]; then
    echo "=============================== BLITZ ================================"
    if [ "${__download}" == "1" ]; then
        download ${BLITZ_SOURCE_URL}
    fi

    if [ "${__remove_before_install}" == "1"  ]; then
        remove ${BLITZ_INSTALL_PREFIX}
    fi

    if [ "${__install}" == "1" ]; then
        tar xvf ${__download_dir}/blitz-${BLITZ_VERSION}.tar.gz
        pushd ${__build_dir}/blitz-${BLITZ_VERSION}
        
        # Generate patch to build shared library
        cat << EOF > blitz-${BLITZ_VERSION}.patch
--- lib/Makefile.am     2016-07-12 12:03:20.838004325 +0200
+++ lib/Makefile.am     2016-07-12 12:01:02.501982180 +0200
@@ -5,6 +5,7 @@
 EXTRA_DIST = readme.txt
 
 AM_CPPFLAGS = -I\$(top_srcdir) -I\$(top_builddir) \$(BOOST_CPPFLAGS)
+AM_LDFLAGS = -no-undefined
 
 lib_LTLIBRARIES = libblitz.la
 libblitz_la_SOURCES = \$(top_srcdir)/src/globals.cpp
EOF

        patch -f -N -i blitz-${BLITZ_VERSION}.patch -p0
        libtoolize --force \
        && aclocal \
        && autoheader \
        && automake --force-missing --add-missing \
        && autoconf \
        && ./configure \
                --build=${__buildtype} \
                --host=${__toolchain} \
                --prefix=${BLITZ_INSTALL_PREFIX} \
                --enable-shared \
        || exit 1
        make -j${__build_proc_num} install || exit 1

        pushd ${CROSSBUILD_INSTALL_PREFIX}
        rm -f blitz && ln -fs blitz-${BLITZ_VERSION} blitz
        pushd bin;ln -fs ../blitz/bin/*.* ./;popd
        pushd lib;ln -fs ../blitz/lib/*.* ./;popd
        pushd include;ln -fs ../blitz/include/* ./;popd
        pushd lib/pkgconfig;ln -fs ../../blitz/lib/pkgconfig/* ./;popd
        popd
        popd
    fi
fi

# ------------------------------------------------------------------------------
# libffi
# ------------------------------------------------------------------------------
LIBFFI_VERSION=3.0.13
LIBFFI_INSTALL_PREFIX=${CROSSBUILD_INSTALL_PREFIX}/libffi-${LIBFFI_VERSION}
LIBFFI_SOURCE_URL=ftp://sourceware.org/pub/libffi/libffi-${LIBFFI_VERSION}.tar.gz
if [ "${LIBFFI}" == "1" ]; then
    echo "=========================== LIBFFI ==============================="
    if [ "${__download}" == "1" ]; then
        download ${LIBFFI_SOURCE_URL}
    fi

    if [ "${__remove_before_install}" == "1"  ]; then
        remove ${LIBFFI_INSTALL_PREFIX}
    fi

    if [ "${__install}" == "1" ]; then
        tar xvf ${__download_dir}/libffi-${LIBFFI_VERSION}.tar.gz
        pushd ${__build_dir}/libffi-${LIBFFI_VERSION}
        
        # Generate patch to build shared library
        libtoolize --force \
        && aclocal \
        && autoheader \
        && automake --force-missing --add-missing \
        && autoconf \
        && ./configure \
                --build=${__buildtype} \
                --host=${__toolchain} \
                --prefix=${LIBFFI_INSTALL_PREFIX} \
                --enable-shared \
        || exit 1
        make -j${__build_proc_num} install || exit 1

        pushd ${CROSSBUILD_INSTALL_PREFIX}
        rm -f libffi && ln -fs libffi-${LIBFFI_VERSION} libffi
        pushd bin;ln -fs ../libffi/bin/*.* ./;popd
        pushd lib;ln -fs ../libffi/lib/*.* ./;popd
        pushd include;ln -fs ../libffi/include/* ./;popd
        pushd lib/pkgconfig;ln -fs ../../libffi/lib/pkgconfig/* ./;popd
        popd
        popd
    fi
fi

# ------------------------------------------------------------------------------
# libjpeg
# ------------------------------------------------------------------------------
LIBJPEG_VERSION=6b
LIBJPEG_INSTALL_PREFIX=${CROSSBUILD_INSTALL_PREFIX}/libjpeg-${LIBJPEG_VERSION}
LIBJPEG_SOURCE_URL=http://sourceforge.mirrorservice.org/l/li/libjpeg/libjpeg/${LIBJPEG_VERSION}/jpegsrc.v${LIBJPEG_VERSION}.tar.gz
if [ "${LIBJPEG}" == "1" ]; then
    echo "============================== LIBJPEG ==============================="
    if [ "${__download}" == "1" ]; then
        download ${LIBJPEG_SOURCE_URL}
    fi

    if [ "${__remove_before_install}" == "1"  ]; then
        remove ${LIBJPEG_INSTALL_PREFIX}
    fi

    if [ "${__install}" == "1" ]; then
        tar xvf ${__download_dir}/jpegsrc.v${LIBJPEG_VERSION}.tar.gz
        pushd ${__build_dir}/jpeg-${LIBJPEG_VERSION}
        
        mkdir -p ${LIBJPEG_INSTALL_PREFIX}/bin \
                 ${LIBJPEG_INSTALL_PREFIX}/lib \
                 ${LIBJPEG_INSTALL_PREFIX}/include \
                 ${LIBJPEG_INSTALL_PREFIX}/man/man1

        # Generate patch to build shared library
        cat << EOF > jpeg-${LIBJPEG_VERSION}.patch
diff -NurB --strip-trailing-cr --suppress-common-lines makefile.cfg makefile.cfg
--- makefile.cfg	2017-06-23 23:39:38.184968656 +0200
+++ makefile.cfg	2017-06-24 01:03:59.201122913 +0200
@@ -15,6 +15,7 @@
 libdir = \$(exec_prefix)/lib
 includedir = \$(prefix)/include
 binprefix =
+libprefix =
 manprefix =
 manext = 1
 mandir = \$(prefix)/man/man\$(manext)
@@ -40,7 +41,9 @@
 # \$(O) expands to "lo" if using libtool, plain "o" if not.
 # Similarly, \$(A) expands to "la" or "a".
 O = @O@
-A = @A@
+A = dll
+IMP = dll.a
+EXE = .exe
 
 # Library version ID; libtool uses this for the shared library version number.
 # Note: we suggest this match the macro of the same name in jpeglib.h.
@@ -54,7 +57,7 @@
 # miscellaneous OS-dependent stuff
 SHELL= /bin/sh
 # linker
-LN= @LN@
+LN= ${__toolchain}-gcc
 # file deletion command
 RM= rm -f
 # directory creation command
@@ -133,7 +136,7 @@
 TROBJECTS= jpegtran.\$(O) rdswitch.\$(O) cdjpeg.\$(O) transupp.\$(O)
 
 
-all: @A2K_DEPS@ libjpeg.\$(A) cjpeg djpeg jpegtran rdjpgcom wrjpgcom
+all: @A2K_DEPS@ \$(libprefix)jpeg\$(JPEG_LIB_VERSION).\$(A) cjpeg\$(EXE) djpeg\$(EXE) jpegtran\$(EXE) rdjpgcom\$(EXE) wrjpgcom\$(EXE)
 
 # Special compilation rules to support ansi2knr and libtool.
 .SUFFIXES: .lo .la
@@ -161,6 +164,11 @@
 # the library:
 
 # without libtool:
+jpeg\$(JPEG_LIB_VERSION).dll: @A2K_DEPS@ \$(LIBOBJECTS)
+	\$(RM) jpeg\$(JPEG_LIB_VERSION).dll libjpeg.dll.a
+	\$(LN) -shared -o jpeg\$(JPEG_LIB_VERSION).dll \$(LDFLAGS) \$(LIBOBJECTS) -Wl,--out-implib,libjpeg.dll.a
+	
+# without libtool:
 libjpeg.a: @A2K_DEPS@ \$(LIBOBJECTS)
 	\$(RM) libjpeg.a
 	\$(AR) libjpeg.a  \$(LIBOBJECTS)
@@ -173,37 +181,38 @@
 
 # sample programs:
 
-cjpeg: \$(COBJECTS) libjpeg.\$(A)
-	\$(LN) \$(LDFLAGS) -o cjpeg \$(COBJECTS) libjpeg.\$(A) \$(LDLIBS)
+cjpeg\$(EXE): \$(COBJECTS) \$(libprefix)jpeg\$(JPEG_LIB_VERSION).\$(A)
+	\$(LN) \$(LDFLAGS) -o cjpeg\$(EXE) \$(COBJECTS) \$(libprefix)jpeg\$(JPEG_LIB_VERSION).\$(A) \$(LDLIBS)
 
-djpeg: \$(DOBJECTS) libjpeg.\$(A)
-	\$(LN) \$(LDFLAGS) -o djpeg \$(DOBJECTS) libjpeg.\$(A) \$(LDLIBS)
+djpeg\$(EXE): \$(DOBJECTS) \$(libprefix)jpeg\$(JPEG_LIB_VERSION).\$(A)
+	\$(LN) \$(LDFLAGS) -o djpeg\$(EXE) \$(DOBJECTS) \$(libprefix)jpeg\$(JPEG_LIB_VERSION).\$(A) \$(LDLIBS)
 
-jpegtran: \$(TROBJECTS) libjpeg.\$(A)
-	\$(LN) \$(LDFLAGS) -o jpegtran \$(TROBJECTS) libjpeg.\$(A) \$(LDLIBS)
+jpegtran\$(EXE): \$(TROBJECTS) \$(libprefix)jpeg\$(JPEG_LIB_VERSION).\$(A)
+	\$(LN) \$(LDFLAGS) -o jpegtran\$(EXE) \$(TROBJECTS) \$(libprefix)jpeg\$(JPEG_LIB_VERSION).\$(A) \$(LDLIBS)
 
-rdjpgcom: rdjpgcom.\$(O)
-	\$(LN) \$(LDFLAGS) -o rdjpgcom rdjpgcom.\$(O) \$(LDLIBS)
+rdjpgcom\$(EXE): rdjpgcom.\$(O)
+	\$(LN) \$(LDFLAGS) -o rdjpgcom\$(EXE) rdjpgcom.\$(O) \$(LDLIBS)
 
-wrjpgcom: wrjpgcom.\$(O)
-	\$(LN) \$(LDFLAGS) -o wrjpgcom wrjpgcom.\$(O) \$(LDLIBS)
+wrjpgcom\$(EXE): wrjpgcom.\$(O)
+	\$(LN) \$(LDFLAGS) -o wrjpgcom\$(EXE) wrjpgcom.\$(O) \$(LDLIBS)
 
 # Installation rules:
 
-install: cjpeg djpeg jpegtran rdjpgcom wrjpgcom @FORCE_INSTALL_LIB@
-	\$(INSTALL_PROGRAM) cjpeg \$(bindir)/\$(binprefix)cjpeg
-	\$(INSTALL_PROGRAM) djpeg \$(bindir)/\$(binprefix)djpeg
-	\$(INSTALL_PROGRAM) jpegtran \$(bindir)/\$(binprefix)jpegtran
-	\$(INSTALL_PROGRAM) rdjpgcom \$(bindir)/\$(binprefix)rdjpgcom
-	\$(INSTALL_PROGRAM) wrjpgcom \$(bindir)/\$(binprefix)wrjpgcom
+install: cjpeg\$(EXE) djpeg\$(EXE) jpegtran\$(EXE) rdjpgcom\$(EXE) wrjpgcom\$(EXE) install-lib
+	\$(INSTALL_PROGRAM) cjpeg\$(EXE) \$(bindir)/\$(binprefix)cjpeg\$(EXE)
+	\$(INSTALL_PROGRAM) djpeg\$(EXE) \$(bindir)/\$(binprefix)djpeg\$(EXE)
+	\$(INSTALL_PROGRAM) jpegtran\$(EXE) \$(bindir)/\$(binprefix)jpegtran\$(EXE)
+	\$(INSTALL_PROGRAM) rdjpgcom\$(EXE) \$(bindir)/\$(binprefix)rdjpgcom\$(EXE)
+	\$(INSTALL_PROGRAM) wrjpgcom\$(EXE) \$(bindir)/\$(binprefix)wrjpgcom\$(EXE)
 	\$(INSTALL_DATA) \$(srcdir)/cjpeg.1 \$(mandir)/\$(manprefix)cjpeg.\$(manext)
 	\$(INSTALL_DATA) \$(srcdir)/djpeg.1 \$(mandir)/\$(manprefix)djpeg.\$(manext)
 	\$(INSTALL_DATA) \$(srcdir)/jpegtran.1 \$(mandir)/\$(manprefix)jpegtran.\$(manext)
 	\$(INSTALL_DATA) \$(srcdir)/rdjpgcom.1 \$(mandir)/\$(manprefix)rdjpgcom.\$(manext)
 	\$(INSTALL_DATA) \$(srcdir)/wrjpgcom.1 \$(mandir)/\$(manprefix)wrjpgcom.\$(manext)
 
-install-lib: libjpeg.\$(A) install-headers
-	\$(INSTALL_LIB) libjpeg.\$(A) \$(libdir)/\$(binprefix)libjpeg.\$(A)
+install-lib: \$(libprefix)jpeg\$(JPEG_LIB_VERSION).\$(A) install-headers
+	\$(INSTALL_LIB) \$(libprefix)jpeg\$(JPEG_LIB_VERSION).\$(A) \$(bindir)/\$(libprefix)jpeg\$(JPEG_LIB_VERSION).\$(A)
+	\$(INSTALL_LIB) libjpeg.\$(IMP) \$(libdir)/libjpeg.\$(IMP)
 
 install-headers: jconfig.h
 	\$(INSTALL_DATA) jconfig.h \$(includedir)/jconfig.h
@@ -212,22 +221,22 @@
 	\$(INSTALL_DATA) \$(srcdir)/jerror.h \$(includedir)/jerror.h
 
 clean:
-	\$(RM) *.o *.lo libjpeg.a libjpeg.la
-	\$(RM) cjpeg djpeg jpegtran rdjpgcom wrjpgcom
+	\$(RM) *.o *.lo libjpeg.*a libjpeg.la
+	\$(RM) cjpeg\$(EXE) djpeg\$(EXE) jpegtran\$(EXE) rdjpgcom\$(EXE) wrjpgcom\$(EXE)
 	\$(RM) ansi2knr core testout* config.log config.status
 	\$(RM) -r knr .libs _libs
 
 distclean: clean
 	\$(RM) Makefile jconfig.h libtool config.cache
 
-test: cjpeg djpeg jpegtran
+test: cjpeg\$(EXE) djpeg\$(EXE) jpegtran\$(EXE)
 	\$(RM) testout*
-	./djpeg -dct int -ppm -outfile testout.ppm  \$(srcdir)/testorig.jpg
-	./djpeg -dct int -bmp -colors 256 -outfile testout.bmp  \$(srcdir)/testorig.jpg
-	./cjpeg -dct int -outfile testout.jpg  \$(srcdir)/testimg.ppm
-	./djpeg -dct int -ppm -outfile testoutp.ppm \$(srcdir)/testprog.jpg
-	./cjpeg -dct int -progressive -opt -outfile testoutp.jpg \$(srcdir)/testimg.ppm
-	./jpegtran -outfile testoutt.jpg \$(srcdir)/testprog.jpg
+	./djpeg\$(EXE) -dct int -ppm -outfile testout.ppm  \$(srcdir)/testorig.jpg
+	./djpeg\$(EXE) -dct int -bmp -colors 256 -outfile testout.bmp  \$(srcdir)/testorig.jpg
+	./cjpeg\$(EXE) -dct int -outfile testout.jpg  \$(srcdir)/testimg.ppm
+	./djpeg\$(EXE) -dct int -ppm -outfile testoutp.ppm \$(srcdir)/testprog.jpg
+	./cjpeg\$(EXE) -dct int -progressive -opt -outfile testoutp.jpg \$(srcdir)/testimg.ppm
+	./jpegtran\$(EXE) -outfile testoutt.jpg \$(srcdir)/testprog.jpg
 	cmp \$(srcdir)/testimg.ppm testout.ppm
 	cmp \$(srcdir)/testimg.bmp testout.bmp
 	cmp \$(srcdir)/testimg.jpg testout.jpg

EOF
        patch -f -N -i jpeg-${LIBJPEG_VERSION}.patch -p0

        #CFLAGS="-O2 -DBUILD" \
        ./configure \
                --build=${__buildtype} \
                --host=${__toolchain} \
                --prefix=${LIBJPEG_INSTALL_PREFIX} \
        || exit 1
        make -j${__build_proc_num} install || exit 1

        pushd ${CROSSBUILD_INSTALL_PREFIX}
        rm -f libjpeg && ln -fs libjpeg-${LIBJPEG_VERSION} libjpeg
        pushd bin;ln -fs ../libjpeg/bin/*.* ./;popd
        pushd lib;ln -fs ../libjpeg/lib/*.* ./;popd
        pushd include;ln -fs ../libjpeg/include/* ./;popd

        popd
        popd
    fi
fi

# ------------------------------------------------------------------------------
# libtiff
# ------------------------------------------------------------------------------
LIBTIFF_VERSION=4.0.3
LIBTIFF_INSTALL_PREFIX=${CROSSBUILD_INSTALL_PREFIX}/libtiff-${LIBTIFF_VERSION}
#LIBTIFF_SOURCE_URL=ftp://ftp.remotesensing.org/libtiff/tiff-${LIBTIFF_VERSION}.tar.gz
LIBTIFF_SOURCE_URL=http://download.osgeo.org/libtiff/tiff-${LIBTIFF_VERSION}.tar.gz
if [ "${LIBTIFF}" == "1" ]; then
    echo "============================== LIBTIFF ==============================="
    if [ "${__download}" == "1" ]; then
        download ${LIBTIFF_SOURCE_URL}
    fi

    if [ "${__remove_before_install}" == "1"  ]; then
        remove ${LIBTIFF_INSTALL_PREFIX}
    fi

    if [ "${__install}" == "1" ]; then
        tar xvf ${__download_dir}/tiff-${LIBTIFF_VERSION}.tar.gz
        pushd ${__build_dir}/tiff-${LIBTIFF_VERSION}
        libtoolize --force \
        && aclocal \
        && autoheader \
        && automake --force-missing --add-missing \
        && autoconf \
        && ./configure \
                --build=${__buildtype} \
                --host=${__toolchain} \
                --prefix=${LIBTIFF_INSTALL_PREFIX} \
                --enable-shared \
        || exit 1
        make -j${__build_proc_num} install || exit 1

        pushd ${CROSSBUILD_INSTALL_PREFIX}
        rm -f libtiff && ln -fs libtiff-${LIBTIFF_VERSION} libtiff
        pushd bin;ln -fs ../libtiff/bin/*.* ./;popd
        pushd lib;ln -fs ../libtiff/lib/*.* ./;popd
        pushd include;ln -fs ../libtiff/include/* ./;popd
        pushd lib/pkgconfig;ln -fs ../../libtiff/lib/pkgconfig/* ./;popd

        popd
        popd
    fi
fi

# ------------------------------------------------------------------------------
# libpng
# ------------------------------------------------------------------------------
LIBPNG_VERSION=1.2.50
LIBPNG_INSTALL_PREFIX=${CROSSBUILD_INSTALL_PREFIX}/libpng-${LIBPNG_VERSION}
LIBPNG_SOURCE_URL=http://sourceforge.mirrorservice.org/l/li/libpng/libpng12/older-releases/${LIBPNG_VERSION}/libpng-${LIBPNG_VERSION}.tar.xz
if [ "${LIBPNG}" == "1" ]; then
    echo "=========================== LIBPNG ==============================="
    if [ "${__download}" == "1" ]; then
        download ${LIBPNG_SOURCE_URL}
    fi

    if [ "${__remove_before_install}" == "1"  ]; then
        remove ${LIBPNG_INSTALL_PREFIX}
    fi

    if [ "${__install}" == "1" ]; then
        tar xvf ${__download_dir}/libpng-${LIBPNG_VERSION}.tar.xz
        pushd ${__build_dir}/libpng-${LIBPNG_VERSION}
        cat << EOF > libpng-${LIBPNG_VERSION}.patch
diff -NurwB --strip-trailing-cr --suppress-common-lines scripts/libpng.pc.in scripts/libpng.pc.in
--- scripts/libpng.pc.in    2016-07-22 16:09:07.471696487 +0200
+++ scripts/libpng.pc.in    2016-07-22 16:09:32.227689364 +0200
@@ -7,4 +7,4 @@
 Description: Loads and saves PNG files
 Version: 1.2.50
 Libs: -L\${libdir} -lpng12
-Cflags: -I\${includedir}
+Cflags: @definitions@ -I\${includedir}
diff -NurwB --strip-trailing-cr --suppress-common-lines CMakeLists.txt CMakeLists.txt
--- CMakeLists.txt  2016-07-22 16:06:28.871745018 +0200
+++ CMakeLists.txt  2016-07-22 16:08:21.591710325 +0200
@@ -202,6 +202,10 @@
 set(exec_prefix \${CMAKE_INSTALL_PREFIX})
 set(libdir      \${CMAKE_INSTALL_PREFIX}/lib)
 set(includedir  \${CMAKE_INSTALL_PREFIX}/include)
+get_directory_property(DIR_DEFS DIRECTORY \${CMAKE_CURRENT_SOURCE_DIR} COMPILE_DEFINITIONS)
+foreach(d \${DIR_DEFS})
+    set(definitions "\${definitions} -D\${d}")
+endforeach()
 
 configure_file(\${CMAKE_CURRENT_SOURCE_DIR}/scripts/libpng.pc.in
   \${CMAKE_CURRENT_BINARY_DIR}/libpng.pc)
EOF
        patch -f -N -i libpng-${LIBPNG_VERSION}.patch -p0

        cmake -DCMAKE_INSTALL_PREFIX=${LIBPNG_INSTALL_PREFIX} \
              -DCMAKE_FIND_ROOT_PATH=${CROSSBUILD_INSTALL_PREFIX} \
              -DCMAKE_TOOLCHAIN_FILE=${__build_dir}/toolchain-${__toolchain}.cmake \
              -DCMAKE_CROSSCOMPILING=ON \
              -DPNG_NO_STDIO=NO \
              -DPNG_NO_CONSOLE_IO=NO \
        || exit 1

        make -j${__build_proc_num} install || exit 1

        pushd ${CROSSBUILD_INSTALL_PREFIX}
        rm -f libpng && ln -fs libpng-${LIBPNG_VERSION} libpng
        pushd ${LIBPNG_INSTALL_PREFIX}/lib;ln -fs libpng12.dll.a libpng.dll.a;popd
        pushd bin;ln -fs ../libpng/bin/*.* ./;popd
        pushd lib;ln -fs ../libpng/lib/*.* ./;popd
        pushd include;ln -fs ../libpng/include/* ./;popd
        pushd lib/pkgconfig;ln -fs ../../libpng/lib/pkgconfig/* ./;popd
        popd
        popd
    fi
fi

# ------------------------------------------------------------------------------
# libmng
# ------------------------------------------------------------------------------
LIBMNG_VERSION=2.0.2
LIBMNG_INSTALL_PREFIX=${CROSSBUILD_INSTALL_PREFIX}/libmng-${LIBMNG_VERSION}
LIBMNG_SOURCE_URL=http://sourceforge.mirrorservice.org/l/li/libmng/libmng-devel/${LIBMNG_VERSION}/libmng-${LIBMNG_VERSION}.tar.gz
if [ "${LIBMNG}" == "1" ]; then
    echo "=========================== LIBMNG ==============================="
    if [ "${__download}" == "1" ]; then
        download ${LIBMNG_SOURCE_URL}
    fi

    if [ "${__remove_before_install}" == "1"  ]; then
        remove ${LIBMNG_INSTALL_PREFIX}
    fi

    if [ "${__install}" == "1" ]; then
        tar xvf ${__download_dir}/libmng-${LIBMNG_VERSION}.tar.gz
        pushd ${__build_dir}/libmng-${LIBMNG_VERSION}
        cat << EOF > libmng-${LIBMNG_VERSION}.patch
diff -NurwB --strip-trailing-cr --suppress-common-lines CMakeLists.txt CMakeLists.txt
--- CMakeLists.txt  2016-10-27 19:36:41.352663554 +0200
+++ CMakeLists.txt  2016-10-27 19:37:24.308664844 +0200
@@ -434,7 +434,7 @@
 #
 ENDIF(BUILD_SHARED_LIBS)
 #------------ libmng.pc ---------------
-IF(UNIX)
+IF(UNIX OR CMAKE_CROSSCOMPILING)
  SET(MNG_LIBS_PRIVATE "")
  IF(JPEG_FOUND)
   SET(MNG_LIBS_PRIVATE "\${MNG_LIBS_PRIVATE} -ljpeg")
@@ -456,7 +456,7 @@
  INSTALL(FILES  \${CMAKE_CURRENT_BINARY_DIR}/libmng.pc DESTINATION
     \${MNG_INSTALL_PKGCONFIG_DIR} )
 
-ENDIF(UNIX)
+ENDIF(UNIX OR CMAKE_CROSSCOMPILING)
 #
 INSTALL(EXPORT MNG_TARGETS DESTINATION \${MNG_INSTALL_PACKAGE_DIR})
 #

diff -NurwB --strip-trailing-cr --suppress-common-lines libmng_types.h libmng_types.h
--- libmng_types.h  2016-09-27 14:35:56.384271583 +0200
+++ libmng_types.h  2016-09-27 14:36:09.684245001 +0200
@@ -204,6 +204,7 @@
 #define HAVE_BOOLEAN
 typedef int boolean;
 #endif
+#include <stdio.h>
 #include <jpeglib.h>
 #endif /* MNG_INCLUDE_IJG6B */
 
EOF
        patch -f -N -i libmng-${LIBMNG_VERSION}.patch -p0

        cmake -DCMAKE_INSTALL_PREFIX=${LIBMNG_INSTALL_PREFIX} \
              -DCMAKE_FIND_ROOT_PATH=${CROSSBUILD_INSTALL_PREFIX} \
              -DCMAKE_TOOLCHAIN_FILE=${__build_dir}/toolchain-${__toolchain}.cmake \
              -DCMAKE_CROSSCOMPILING=ON \
        || exit 1

        make -j${__build_proc_num} install || exit 1

        pushd ${CROSSBUILD_INSTALL_PREFIX}
        rm -f libmng && ln -fs libmng-${LIBMNG_VERSION} libmng
        pushd bin;ln -fs ../libmng/bin/*.* ./;popd
        pushd lib;ln -fs ../libmng/lib/*.* ./;popd
        pushd include;ln -fs ../libmng/include/* ./;popd
        pushd lib/pkgconfig;ln -fs ../../libmng/lib/pkgconfig/* ./;popd

        popd
        popd
    fi
fi

# ------------------------------------------------------------------------------
# fontconfig
# ------------------------------------------------------------------------------
FONTCONFIG_VERSION=2.8.0
FONTCONFIG_INSTALL_PREFIX=${CROSSBUILD_INSTALL_PREFIX}/fontconfig-${FONTCONFIG_VERSION}
FONTCONFIG_SOURCE_URL=http://www.freedesktop.org/software/fontconfig/release/fontconfig-${FONTCONFIG_VERSION}.tar.gz
if [ "${FONTCONFIG}" == "1" ]; then
    echo "============================= FONTCONFIG ============================="
    if [ "${__download}" == "1" ]; then
        download ${FONTCONFIG_SOURCE_URL}
    fi

    if [ "${__remove_before_install}" == "1"  ]; then
        remove ${FONTCONFIG_INSTALL_PREFIX}
    fi

    if [ "${__install}" == "1" ]; then
        tar xvf ${__download_dir}/fontconfig-${FONTCONFIG_VERSION}.tar.gz
        pushd ${__build_dir}/fontconfig-${FONTCONFIG_VERSION}
        libtoolize --force \
        && aclocal \
        && autoheader \
        && automake --force-missing --add-missing \
        && autoconf \
        && ./configure \
                --with-arch=i386 \
                --build=${__buildtype} \
                --host=${__toolchain} \
                --prefix=${FONTCONFIG_INSTALL_PREFIX} \
                --with-freetype-config=${FREETYPE_INSTALL_PREFIX}/bin/freetype-config \
        || exit 1
        # Fontconfig fails to install using multi processors
        make -j${__build_proc_num} || exit 1
        make install || exit 1

        pushd ${CROSSBUILD_INSTALL_PREFIX}
        rm -f fontconfig && ln -fs fontconfig-${FONTCONFIG_VERSION} fontconfig
        pushd bin;ln -fs ../fontconfig/bin/*.* ./;popd
        pushd lib;ln -fs ../fontconfig/lib/*.* ./;popd
        pushd include;ln -fs ../fontconfig/include/* ./;popd
        pushd lib/pkgconfig;ln -fs ../../fontconfig/lib/pkgconfig/* ./;popd

        popd
        popd
    fi
fi

# ------------------------------------------------------------------------------
# glib
# ------------------------------------------------------------------------------
GLIB_VERSION=2.40.2
GLIB_INSTALL_PREFIX=${CROSSBUILD_INSTALL_PREFIX}/glib-${GLIB_VERSION}
GLIB_SOURCE_URL=http://ftp.gnome.org/pub/GNOME/sources/glib/${GLIB_VERSION%.*}/glib-${GLIB_VERSION}.tar.xz
if [ "${GLIB}" == "1" ]; then
    echo "================================ GLIB ================================"
    if [ "${__download}" == "1" ]; then
        download ${GLIB_SOURCE_URL}
    fi

    if [ "${__remove_before_install}" == "1"  ]; then
        remove ${GLIB_INSTALL_PREFIX}
    fi

    if [ "${__install}" == "1" ]; then
        tar xvf ${__download_dir}/glib-${GLIB_VERSION}.tar.xz
        pushd ${__build_dir}/glib-${GLIB_VERSION}

        if [ "${__toolchain}" == "i586-mingw32msvc" ]; then
            cat << EOF > glib-${GLIB_VERSION}.patch
diff -NurwB --strip-trailing-cr --suppress-common-lines configure.ac configure.ac
--- configure.ac    2016-07-21 17:13:57.994060819 +0200
+++ configure.ac    2016-07-21 17:14:05.090061193 +0200
@@ -3531,7 +3531,7 @@
 AS_IF([test "x$enable_compile_warnings" = xyes], [
   CC_CHECK_FLAGS_APPEND([GLIB_WARN_CFLAGS], [CFLAGS], [\\
    -Wall -Wstrict-prototypes -Werror=declaration-after-statement \\
-   -Werror=missing-prototypes -Werror=implicit-function-declaration \\
+   -Werror=implicit-function-declaration \\
    -Werror=pointer-arith -Werror=init-self -Werror=format-security \\
    -Werror=format=2 -Werror=missing-include-dirs])
 ])
diff -NurwB --strip-trailing-cr --suppress-common-lines glib/gatomic.c glib/gatomic.c
--- glib/gatomic.c  2016-07-21 17:31:35.494137558 +0200
+++ glib/gatomic.c  2016-07-21 17:39:38.230173769 +0200
@@ -519,6 +519,16 @@
 #define InterlockedXor(a,b) _gInterlockedXor(a,b)
 #endif
 
+/* mingw32 does not have MemoryBarrier.
+ * MemoryBarrier may be defined as a macro or a function.
+ * Just make a failsafe version for ourselves. */
+#ifndef MemoryBarrier
+static inline void MemoryBarrier (void) {
+  long dummy = 0;
+  InterlockedExchange (&dummy, 1);
+}
+#endif
+
 /*
  * http://msdn.microsoft.com/en-us/library/ms684122(v=vs.85).aspx
  */
EOF

        else
            cat << EOF > glib-${GLIB_VERSION}.patch
diff -NurwB --strip-trailing-cr --suppress-common-lines glib/tests/fileutils.c glib/tests/fileutils.c
--- glib/tests/fileutils.c  2016-07-22 01:34:19.051977900 +0200
+++ glib/tests/fileutils.c  2016-07-22 01:35:13.615975394 +0200
@@ -32,13 +32,11 @@
 #define G_STDIO_NO_WRAP_ON_UNIX
 #include <glib/gstdio.h>
 
-#ifdef G_OS_UNIX
 #include <unistd.h>
 #include <sys/types.h>
 #include <sys/stat.h>
 #include <fcntl.h>
 #include <utime.h>
-#endif
 #ifdef G_OS_WIN32
 #include <windows.h>
 #endif
EOF
        fi

        patch -f -N -i glib-${GLIB_VERSION}.patch -p0

        libtoolize --force \
        && aclocal \
        && autoheader \
        && automake --force-missing --add-missing \
        && autoconf \
        && ./configure \
                --build=${__buildtype} \
                --host=${__toolchain} \
                --prefix=${GLIB_INSTALL_PREFIX} \
                --with-python=${PYTHON_HOST_COMMAND} \
                --enable-shared \
        || exit 1
        make -j${__build_proc_num} install || exit 1

        pushd ${CROSSBUILD_INSTALL_PREFIX}
        rm -f glib && ln -fs glib-${GLIB_VERSION} glib
        pushd bin;ln -fs ../glib/bin/*.* ./;popd
        pushd lib;ln -fs ../glib/lib/*.* ./;popd
        pushd include;ln -fs ../glib/include/* ./;popd
        pushd lib/pkgconfig;ln -fs ../../glib/lib/pkgconfig/* ./;popd
        popd
        popd
    fi
fi

# ------------------------------------------------------------------------------
# openjpeg
# ------------------------------------------------------------------------------
OPENJPEG_VERSION=2.1
OPENJPEG_INSTALL_PREFIX=${CROSSBUILD_INSTALL_PREFIX}/openjpeg-${OPENJPEG_VERSION}
OPENJPEG_SOURCE_URL=https://github.com/uclouvain/openjpeg/archive/version.${OPENJPEG_VERSION}.tar.gz

if [ "${OPENJPEG}" == "1" ]; then
    echo "============================== OPENJPEG =============================="
    if [ "${__download}" == "1" ]; then
        if [ "$__use_cea_mirror" = "1" ]; then
            # It was necessary to rename the original file because its name did
            # not contain anything to know that it provides openjpeg. It is
            # necessary to have particular case where cea mirror file name 
            # is not the same as original file name.
            download "${__mirror_url}/sources/openjpeg-${OPENJPEG_VERSION}.tar.gz"
        else
            download ${OPENJPEG_SOURCE_URL} openjpeg-${OPENJPEG_VERSION}.tar.gz
        fi
    fi

    if [ "${__remove_before_install}" == "1"  ]; then
        remove ${OPENJPEG_INSTALL_PREFIX}
    fi

    if [ "${__install}" == "1" ]; then
        tar xvf ${__download_dir}/openjpeg-${OPENJPEG_VERSION}.tar.gz
        pushd ${__build_dir}/openjpeg-version.${OPENJPEG_VERSION}
        cmake \
            -DCMAKE_INSTALL_PREFIX=${OPENJPEG_INSTALL_PREFIX} \
            -DCMAKE_TOOLCHAIN_FILE=${__build_dir}/toolchain-${__toolchain}.cmake \
            -DCMAKE_CROSSCOMPILING=ON \
            -DBUILD_PKGCONFIG_FILES=ON \
        || exit 1
        make -j${__build_proc_num} install || exit 1

        pushd ${CROSSBUILD_INSTALL_PREFIX}
        rm -f openjpeg && ln -fs openjpeg-${OPENJPEG_VERSION} openjpeg
        pushd bin;ln -fs ../openjpeg/bin/*.* ./;popd
        pushd lib;ln -fs ../openjpeg/lib/*.* ./;popd
        pushd include;ln -fs ../openjpeg/include/* ./;popd
        pushd lib/pkgconfig;ln -fs ../../openjpeg/lib/pkgconfig/* ./;popd
        popd
        popd
    fi
fi

# ------------------------------------------------------------------------------
# jxrlib
# ------------------------------------------------------------------------------
JPEGXR_VERSION=1.1
JPEGXR_INSTALL_PREFIX=${CROSSBUILD_INSTALL_PREFIX}/jxrlib-${JPEGXR_VERSION}
JPEGXR_LATEST_REV=$(basename $(wget --no-check-certificate -O ${__tmp_dir}/jpegxr.rss "http://jxrlib.codeplex.com/project/feeds/rss?ProjectRSSFeed=codeplex%3a%2f%2fsourcecontrol%2fjxrlib" 2>/dev/null && xmllint ${__tmp_dir}/jpegxr.rss --xpath '/rss/channel/item[1]/link/text()'))
JPEGXR_SOURCE_URL="http://download-codeplex.sec.s-msft.com/Download/SourceControlFileDownload.ashx?ProjectName=jxrlib&changeSetId=${JPEGXR_LATEST_REV}"

if [ "${JPEGXR}" == "1" ]; then
    echo "=============================== JPEGXR ==============================="
    if [ "${__download}" == "1" ]; then
        if [ "$__use_cea_mirror" = "1" ]; then
            # It was necessary to rename the original file because its name did
            # not contain anything to know that it provides jxrlib. It is
            # necessary to have particular case where cea mirror file name 
            # is not the same as original file name.
            download "${__mirror_url}/sources/jxrlib-${JPEGXR_VERSION}.zip"
        else
            download ${JPEGXR_SOURCE_URL} jxrlib-${JPEGXR_VERSION}.zip
        fi
    fi

    if [ "${__remove_before_install}" == "1"  ]; then
        remove ${JPEGXR_INSTALL_PREFIX}
    fi

    if [ "${__install}" == "1" ]; then
        mkdir ${__build_dir}/jxrlib-${JPEGXR_VERSION}
        pushd ${__build_dir}/jxrlib-${JPEGXR_VERSION}
        unzip ${__download_dir}/jxrlib-${JPEGXR_VERSION}.zip

        # Generate patch to build cross build shared library
        cat << EOF > jxrlib-${JPEGXR_VERSION}.patch
diff -NurwB --strip-trailing-cr --suppress-common-lines libjxr.pc.in libjxr.pc.in
--- libjxr.pc.in    2016-07-25 18:07:36.231581830 +0200
+++ libjxr.pc.in    2016-07-25 18:08:34.811563699 +0200
@@ -9,4 +9,4 @@
 Version: %(JXR_VERSION)s
 Libs: -L\${libdir} -ljpegxr -ljxrglue
 Libs.private: -lm 
-Cflags: -I\${includedir}/libjxr/common -I\${includedir}/libjxr/image/x86 -I\${includedir}/libjxr/image -I\${includedir}/libjxr/glue -I\${includedir}/libjxr/test -D__ANSI__ -DDISABLE_PERF_MEASUREMENT %(JXR_ENDIAN)s
+Cflags: -I\${includedir}/libjxr/common -I\${includedir}/libjxr/image/x86 -I\${includedir}/libjxr/image -I\${includedir}/libjxr/glue -I\${includedir}/libjxr/test -D__ANSI__ -DDISABLE_PERF_MEASUREMENT %(JXR_ENDIAN)s %(JXR_ARCH)s %(JXR_CROSS_COMPILING)s

diff -NurwB --strip-trailing-cr --suppress-common-lines jxrgluelib/JXRMeta.h jxrgluelib/JXRMeta.h
--- jxrgluelib/JXRMeta.h    2016-07-20 11:25:00.803288188 +0200
+++ jxrgluelib/JXRMeta.h    2016-07-19 17:56:50.859941174 +0200
@@ -111,6 +110,12 @@
 #define __out_win   __out
 #endif
 
+#ifdef CROSS_COMPILING
+#define __in_ecount(size)
+#define __out_ecount(size)
+#define __in
+#define __out
+#endif
 
 //================================================================
 
diff -NurwB --strip-trailing-cr --suppress-common-lines Makefile Makefile
--- Makefile	2016-11-02 12:08:23.574742441 +0100
+++ Makefile	2016-11-02 12:25:53.790174830 +0100
@@ -29,7 +29,9 @@
 ##
 build: all
 
+ifndef CC
 CC=cc
+endif
 
 JXR_VERSION=1.1
 
@@ -49,6 +51,14 @@
 PICFLAG=
 endif

+ifeq (\$(ARCH), x86_64)
+ARCH_FLAG=-D__LP64__
+endif
+ 
+ifneq (\$(CROSS_COMPILING),)
+CROSS_COMPILING_FLAG=-DCROSS_COMPILING
+endif
+
 ifneq (\$(BIG_ENDIAN),)
 ENDIANFLAG=-D_BIG__ENDIAN_
 else
@@ -65,10 +71,18 @@
 
 CD=cd
 MK_DIR=mkdir -p
-CFLAGS=-I. -Icommon/include -I\$(DIR_SYS) \$(ENDIANFLAG) -D__ANSI__ -DDISABLE_PERF_MEASUREMENT -w \$(PICFLAG) -O
+CFLAGS=-I. -Icommon/include -I\$(DIR_SYS) \$(ENDIANFLAG) \$(ARCH_FLAG) \$(CROSS_COMPILING_FLAG) -D__ANSI__ -DDISABLE_PERF_MEASUREMENT -w \$(PICFLAG) -O
+
+ifndef STATIC_LIB_EXT
+STATIC_LIB_EXT=.a
+endif
+
+ifndef SHARED_LIB_EXT
+SHARED_LIB_EXT=.so
+endif
 
-STATIC_LIBRARIES=\$(DIR_BUILD)/libjxrglue.a \$(DIR_BUILD)/libjpegxr.a
-SHARED_LIBRARIES=\$(DIR_BUILD)/libjxrglue.so \$(DIR_BUILD)/libjpegxr.so
+STATIC_LIBRARIES=\$(DIR_BUILD)/libjxrglue\$(STATIC_LIB_EXT) \$(DIR_BUILD)/libjpegxr\$(STATIC_LIB_EXT)
+SHARED_LIBRARIES=\$(DIR_BUILD)/libjxrglue\$(SHARED_LIB_EXT) \$(DIR_BUILD)/libjpegxr\$(SHARED_LIB_EXT)
 
 ifneq (\$(SHARED),)
 LIBRARIES=\$(SHARED_LIBRARIES)
@@ -76,7 +90,7 @@
 LIBRARIES=\$(STATIC_LIBRARIES)
 endif
 
-LIBS=-L\$(DIR_BUILD) \$(shell echo \$(LIBRARIES) | sed -e 's%\$(DIR_BUILD)/lib\\([^ ]*\\)\\.\\(a\\|so\\)%-l\\1%g') -lm
+LIBS=-L\$(DIR_BUILD) \$(shell echo \$(LIBRARIES) | sed -e 's%\$(DIR_BUILD)/lib\\([^ ]*\\)\\(\$(STATIC_LIB_EXT)\\|\$(SHARED_LIB_EXT)\\)%-l\\1%g') -lm
 
 ##--------------------------------
 ##
@@ -118,14 +132,14 @@
 ## JPEG XR library
 ##
 
-\$(DIR_BUILD)/libjpegxr.a: \$(OBJ_ENC) \$(OBJ_DEC) \$(OBJ_SYS)
+\$(DIR_BUILD)/libjpegxr\$(STATIC_LIB_EXT): \$(OBJ_ENC) \$(OBJ_DEC) \$(OBJ_SYS)
 	\$(MK_DIR) \$(@D)
 	ar rvu \$@ \$(OBJ_ENC) \$(OBJ_DEC) \$(OBJ_SYS)
 	ranlib \$@
 
-\$(DIR_BUILD)/libjpegxr.so: \$(OBJ_ENC) \$(OBJ_DEC) \$(OBJ_SYS)
+\$(DIR_BUILD)/libjpegxr\$(SHARED_LIB_EXT): \$(OBJ_ENC) \$(OBJ_DEC) \$(OBJ_SYS)
 	\$(MK_DIR) \$(@D)
-	\$(CC) -shared \$? -o \$@
+	\$(CC) -shared \$? -Wl,--no-undefined -o \$@
 
 ##--------------------------------
 ##
@@ -156,14 +170,14 @@
 ## JPEG XR Glue library
 ##
 
-\$(DIR_BUILD)/libjxrglue.a: \$(OBJ_GLUE) \$(OBJ_TEST)
+\$(DIR_BUILD)/libjxrglue\$(STATIC_LIB_EXT): \$(OBJ_GLUE) \$(OBJ_TEST)
 	\$(MK_DIR) \$(@D)
 	ar rvu \$@ \$(OBJ_GLUE) \$(OBJ_TEST)
 	ranlib \$@
 
-\$(DIR_BUILD)/libjxrglue.so: \$(OBJ_GLUE) \$(OBJ_TEST)
+\$(DIR_BUILD)/libjxrglue\$(SHARED_LIB_EXT): \$(OBJ_GLUE) \$(OBJ_TEST) \$(DIR_BUILD)/libjpegxr\$(SHARED_LIB_EXT)
 	\$(MK_DIR) \$(@D)
-	\$(CC) -shared \$? -o \$@
+	\$(CC) -shared \$? -Wl,--no-undefined -o \$@
 
 ##--------------------------------
 ##
@@ -171,7 +185,7 @@
 ##
 ENCAPP=JxrEncApp
 
-\$(DIR_BUILD)/\$(ENCAPP): \$(DIR_SRC)/\$(DIR_EXEC)/\$(ENCAPP).c \$(LIBRARIES)
+\$(DIR_BUILD)/\$(ENCAPP)\${EXE_EXT}: \$(DIR_SRC)/\$(DIR_EXEC)/\$(ENCAPP).c \$(LIBRARIES)
 	\$(MK_DIR) \$(@D)
 	\$(CC) \$< -o \$@ \$(CFLAGS) -I\$(DIR_GLUE) -I\$(DIR_TEST) \$(LIBS)
 
@@ -182,7 +196,7 @@
 
 DECAPP=JxrDecApp
 
-\$(DIR_BUILD)/\$(DECAPP): \$(DIR_SRC)/\$(DIR_EXEC)/\$(DECAPP).c \$(LIBRARIES)
+\$(DIR_BUILD)/\$(DECAPP)\${EXE_EXT}: \$(DIR_SRC)/\$(DIR_EXEC)/\$(DECAPP).c \$(LIBRARIES)
 	\$(MK_DIR) \$(@D)
 	\$(CC) \$< -o \$@ \$(CFLAGS) -I\$(DIR_GLUE) -I\$(DIR_TEST) \$(LIBS)
 
@@ -190,19 +204,19 @@
 ##
 ## JPEG XR library
 ##
-all: \$(DIR_BUILD)/\$(ENCAPP) \$(DIR_BUILD)/\$(DECAPP) \$(LIBRARIES)
+all: \$(DIR_BUILD)/\$(ENCAPP)\${EXE_EXT} \$(DIR_BUILD)/\$(DECAPP)\${EXE_EXT} \$(LIBRARIES)
 
 clean:
-	rm -rf \$(DIR_BUILD)/*App \$(DIR_BUILD)/*.o \$(DIR_BUILD)/libj*.a \$(DIR_BUILD)/libj*.so \$(DIR_BUILD)/libjxr.pc
+	rm -rf \$(DIR_BUILD)/*App \$(DIR_BUILD)/*.o \$(DIR_BUILD)/libj*\$(STATIC_LIB_EXT) \$(DIR_BUILD)/libj*\$(SHARED_LIB_EXT) \$(DIR_BUILD)/libjxr.pc
 
 \$(DIR_BUILD)/libjxr.pc: \$(DIR_SRC)/libjxr.pc.in
-	@python -c 'import os; d = { "DIR_INSTALL": "\$(DIR_INSTALL)", "JXR_VERSION": "\$(JXR_VERSION)", "JXR_ENDIAN": "\$(ENDIANFLAG)" }; fin = open("\$<", "r"); fout = open("\$@", "w+"); fout.writelines( [ l % d for l in fin.readlines()])'
+	@python -c 'import os; d = { "DIR_INSTALL": "\$(DIR_INSTALL)", "JXR_VERSION": "\$(JXR_VERSION)", "JXR_ENDIAN": "\$(ENDIANFLAG)", "JXR_ARCH": "\$(ARCH_FLAG)", "JXR_CROSS_COMPILING": "\$(CROSS_COMPILING_FLAG)" }; fin = open("\$<", "r"); fout = open("\$@", "w+"); fout.writelines( [ l % d for l in fin.readlines()])'
 
 install: all \$(DIR_BUILD)/libjxr.pc
 	install -d \$(DIR_INSTALL)/lib/pkgconfig \$(DIR_INSTALL)/bin \$(DIR_INSTALL)/include/libjxr/common  \$(DIR_INSTALL)/include/libjxr/image/x86 \$(DIR_INSTALL)/include/libjxr/glue \$(DIR_INSTALL)/include/libjxr/test \$(DIR_INSTALL)/share/doc/jxr-\$(JXR_VERSION)
 	install \$(LIBRARIES) \$(DIR_INSTALL)/lib
 	install -m 644 \$(DIR_BUILD)/libjxr.pc \$(DIR_INSTALL)/lib/pkgconfig
-	install \$(DIR_BUILD)/\$(ENCAPP) \$(DIR_BUILD)/\$(DECAPP) \$(DIR_INSTALL)/bin
+	install \$(DIR_BUILD)/\$(ENCAPP)\${EXE_EXT} \$(DIR_BUILD)/\$(DECAPP)\${EXE_EXT} \$(DIR_INSTALL)/bin
 	install -m 644 \$(DIR_SRC)/common/include/*.h \$(DIR_INSTALL)/include/libjxr/common
 	install -m 644 \$(DIR_SRC)/image/x86/*.h \$(DIR_INSTALL)/include/libjxr/image/x86
 	install -m 644 \$(DIR_SRC)/\$(DIR_SYS)/*.h \$(DIR_INSTALL)/include/libjxr/image


diff -NurwB --strip-trailing-cr --suppress-common-lines image/sys/strcodec.c image/sys/strcodec.c
--- image/sys/strcodec.c    2016-07-20 11:23:39.307231385 +0200
+++ image/sys/strcodec.c    2016-07-20 11:16:17.898933942 +0200
@@ -281,7 +281,7 @@
     pWS->SetPos = SetPosWS_File;
     pWS->GetPos = GetPosWS_File;
 
-#ifdef WIN32
+#if (defined(WIN32) && !defined(CROSS_COMPILING))
     FailIf(0 != fopen_s(&pWS->state.file.pFile, szFilename, szMode), WMP_errFileIO);
 #else
     pWS->state.file.pFile = fopen(szFilename, szMode);

diff -NurwB --strip-trailing-cr --suppress-common-lines image/sys/strcodec.h image/sys/strcodec.h
--- image/sys/strcodec.h    2016-07-20 11:23:46.531236337 +0200
+++ image/sys/strcodec.h    2016-07-20 11:08:09.466383242 +0200
@@ -57,7 +57,7 @@
 
 //================================================================
 //#ifdef WIN32
-#if defined(WIN32) && !defined(UNDER_CE)   // WIN32 seems to be defined always in VS2005 for ARM platform
+#if defined(WIN32) && !defined(UNDER_CE) && !defined(CROSS_COMPILING)  // WIN32 seems to be defined always in VS2005 for ARM platform
 #define PLATFORM_X86
 #include "..\\x86\\x86.h"
 #endif
@@ -450,6 +450,10 @@
 
     struct WMPStream ** ppWStream;
 
+#ifdef CROSS_COMPILING
+#define TCHAR char
+#endif
+
 #ifdef WIN32
     TCHAR **ppTempFile;
 #else
EOF
        cat << EOF >> /dev/null
diff -NurwB --strip-trailing-cr --suppress-common-lines image/sys/strcodec.c image/sys/strcodec.c
--- image/sys/strcodec.c    2016-07-20 11:23:39.307231385 +0200
+++ image/sys/strcodec.c    2016-07-20 11:16:17.898933942 +0200
@@ -664,7 +664,7 @@
 //================================================================
 // Memory access functions
 //================================================================
-#if (defined(WIN32) && !defined(UNDER_CE)) || (defined(UNDER_CE) && defined(_ARM_))
+#if (defined(WIN32) && !defined(UNDER_CE) && !defined(CROSS_COMPILING) ) || (defined(UNDER_CE) && defined(_ARM_))
 // WinCE ARM and Desktop x86
 #else
 // other platform

EOF
        # It is necessary to convert carriage return because the package content 
        # is in windows conventions (i.e.: carriage return is \r\n, not only \n)
        dos2unix image/sys/ansi.h \
                 image/sys/strcodec.h \
                 image/sys/strcodec.c \
                 jxrgluelib/JXRMeta.h \
                 Makefile \
                 libjxr.pc.in
        
        patch -f -N -i jxrlib-${JPEGXR_VERSION}.patch -p0

        DIR_INSTALL=${JPEGXR_INSTALL_PREFIX} \
        SHARED=1 \
        SHARED_LIB_EXT=.dll \
        EXE_EXT=.exe \
        ARCH=${__arch} \
        CROSS_COMPILING=1 \
        make -j${__build_proc_num} install || exit 1

        pushd ${CROSSBUILD_INSTALL_PREFIX}
        rm -f jxrlib && ln -fs jxrlib-${JPEGXR_VERSION} jxrlib
        pushd ${JPEGXR_INSTALL_PREFIX}/bin;ln -fs ../lib/*.dll ./; popd
        pushd bin;ln -fs ../jxrlib/bin/*.* ./;popd
        pushd include;ln -fs ../jxrlib/include/* ./;popd
        pushd lib/pkgconfig;ln -fs ../../jxrlib/lib/pkgconfig/* ./;popd

        popd
        popd
    fi
fi

# ------------------------------------------------------------------------------
# jasper
# ------------------------------------------------------------------------------
JASPER_VERSION=1.900.1
JASPER_INSTALL_PREFIX=${CROSSBUILD_INSTALL_PREFIX}/jasper-${JASPER_VERSION}
JASPER_SOURCE_URL=https://github.com/mdadams/jasper/archive/version-${JASPER_VERSION}.tar.gz
if [ "${JASPER}" == "1" ]; then
    echo "========================= JASPER =============================="
    if [ "${__download}" == "1" ]; then
        if [ "$__use_cea_mirror" = "1" ]; then
            # It was necessary to rename the original file because its name did
            # not contain anything to know that it provides jasper. It is
            # necessary to have particular case where cea mirror file name 
            # is not the same as original file name.
            download "${__mirror_url}/sources/jasper-${JASPER_VERSION}.tar.gz"
        else
            download ${JASPER_SOURCE_URL} jasper-${JASPER_VERSION}.tar.gz
        fi
    fi

    if [ "${__remove_before_install}" == "1"  ]; then
        remove ${JASPER_INSTALL_PREFIX}
    fi

    if [ "${__install}" == "1" ]; then
        tar xvf ${__download_dir}/jasper-${JASPER_VERSION}.tar.gz
        pushd ${__build_dir}/jasper-version-${JASPER_VERSION}

        libtoolize --force \
        && aclocal \
        && autoheader \
        && automake --force-missing --add-missing \
        && autoconf \
        && ./configure \
                --build=${__buildtype} \
                --host=${__toolchain} \
                --prefix=${JASPER_INSTALL_PREFIX} \
                --enable-shared \
        || exit 1
        make -j${__build_proc_num} install || exit 1

        pushd ${CROSSBUILD_INSTALL_PREFIX}
        rm -f jasper && ln -fs jasper-${JASPER_VERSION} jasper
        pushd bin;ln -fs ../jasper/bin/*.* ./;popd
        pushd lib;ln -fs ../jasper/lib/*.* ./;popd
        pushd include;ln -fs ../jasper/include/* ./;popd
        pushd lib/pkgconfig;ln -fs ../../jasper/lib/pkgconfig/* ./;popd
        popd
        popd
    fi
fi

# ------------------------------------------------------------------------------
# gdk-pixbuf
# ------------------------------------------------------------------------------
GDKPIXBUF_VERSION=2.30.7
GDKPIXBUF_INSTALL_PREFIX=${CROSSBUILD_INSTALL_PREFIX}/gdk-pixbuf-${GDKPIXBUF_VERSION}
GDKPIXBUF_SOURCE_URL=http://ftp.gnome.org/pub/GNOME/sources/gdk-pixbuf/${GDKPIXBUF_VERSION%.*}/gdk-pixbuf-${GDKPIXBUF_VERSION}.tar.xz
if [ "${GDKPIXBUF}" == "1" ]; then
    echo "============================= GDKPIXBUF =============================="
    if [ "${__download}" == "1" ]; then
        download ${GDKPIXBUF_SOURCE_URL}
    fi

    if [ "${__remove_before_install}" == "1"  ]; then
        remove ${GDKPIXBUF_INSTALL_PREFIX}
    fi

    if [ "${__install}" == "1" ]; then
        tar xvf ${__download_dir}/gdk-pixbuf-${GDKPIXBUF_VERSION}.tar.xz
        pushd ${__build_dir}/gdk-pixbuf-${GDKPIXBUF_VERSION}
        
        # Generate patch to build shared library
        cat << EOF > gdk-pixbuf-${GDKPIXBUF_VERSION}.patch
diff -NurwB --strip-trailing-cr --suppress-common-lines gdk-pixbuf/io-png.c gdk-pixbuf/io-png.c
--- gdk-pixbuf/io-png.c	2016-07-22 15:37:48.943968875 +0200
+++ gdk-pixbuf/io-png.c	2016-07-22 15:37:37.983969631 +0200
@@ -295,8 +295,9 @@
 		png_destroy_read_struct (&png_ptr, &info_ptr, NULL);
 		return NULL;
 	}
-
+#ifdef PNG_STDIO_SUPPORTED
 	png_init_io (png_ptr, f);
+#endif
 	png_read_info (png_ptr, info_ptr);
 
         if (!setup_png_transformations(png_ptr, info_ptr, error, &w, &h, &ctype)) {
@@ -1001,7 +1002,9 @@
                                  png_save_to_callback_write_func,
                                  png_save_to_callback_flush_func);
        } else {
+#ifdef PNG_STDIO_SUPPORTED
                png_init_io (png_ptr, f);
+#endif
        }
 
        if (compression >= 0)

EOF

        patch -f -N -i gdk-pixbuf-${GDKPIXBUF_VERSION}.patch -p0
        libtoolize --force \
        && aclocal \
        && autoheader \
        && automake --force-missing --add-missing \
        && autoconf \
        && ./configure \
                --build=${__buildtype} \
                --host=${__toolchain} \
                --prefix=${GDKPIXBUF_INSTALL_PREFIX} \
                --enable-shared \
                PKG_CONFIG=${PKG_CONFIG} \
        || exit 1
        make -j${__build_proc_num} install || exit 1

        pushd ${CROSSBUILD_INSTALL_PREFIX}
        rm -f gdk-pixbuf && ln -fs gdk-pixbuf-${GDKPIXBUF_VERSION} gdk-pixbuf
        pushd bin;ln -fs ../gdk-pixbuf/bin/*.* ./;popd
        pushd lib;ln -fs ../gdk-pixbuf/lib/*.* ./;popd
        pushd include;ln -fs ../gdk-pixbuf/include/* ./;popd
        pushd lib/pkgconfig;ln -fs ../../gdk-pixbuf/lib/pkgconfig/* ./;popd
        popd
        popd
    fi
fi

# ------------------------------------------------------------------------------
# pixman
# ------------------------------------------------------------------------------
PIXMAN_VERSION=0.30.2
PIXMAN_INSTALL_PREFIX=${CROSSBUILD_INSTALL_PREFIX}/pixman-${PIXMAN_VERSION}
PIXMAN_SOURCE_URL=https://cairographics.org/releases/pixman-${PIXMAN_VERSION}.tar.gz
if [ "${PIXMAN}" == "1" ]; then
    echo "=============================== PIXMAN ==============================="
    if [ "${__download}" == "1" ]; then
        download ${PIXMAN_SOURCE_URL}
    fi

    if [ "${__remove_before_install}" == "1"  ]; then
        remove ${PIXMAN_INSTALL_PREFIX}
    fi

    if [ "${__install}" == "1" ]; then
        tar xvf ${__download_dir}/pixman-${PIXMAN_VERSION}.tar.gz
        pushd ${__build_dir}/pixman-${PIXMAN_VERSION}

        cat << EOF > pixman-${PIXMAN_VERSION}.patch
diff -NurwB --strip-trailing-cr --suppress-common-lines test/utils.c test/utils.c
--- test/utils.c	2016-07-25 16:53:30.100576575 +0200
+++ test/utils.c	2016-07-25 16:54:30.888569832 +0200
@@ -510,8 +510,9 @@
     if (!(info_struct = png_create_info_struct (write_struct)))
 	goto out2;
 
+#ifdef PNG_STDIO_SUPPORTED
     png_init_io (write_struct, f);
-
+#endif
     png_set_IHDR (write_struct, info_struct, width, height,
 		  8, PNG_COLOR_TYPE_RGB_ALPHA,
 		  PNG_INTERLACE_NONE, PNG_COMPRESSION_TYPE_BASE,

EOF
        patch -f -N -i pixman-${PIXMAN_VERSION}.patch -p0
        libtoolize --force \
        && aclocal \
        && autoheader \
        && automake --force-missing --add-missing \
        && autoconf \
        && ./configure \
                --build=${__buildtype} \
                --host=${__toolchain} \
                --prefix=${PIXMAN_INSTALL_PREFIX} \
                --enable-shared \
        || exit 1
        make -j${__build_proc_num} install || exit 1

        pushd ${CROSSBUILD_INSTALL_PREFIX}
        rm -f pixman && ln -fs pixman-${PIXMAN_VERSION} pixman
        pushd bin;ln -fs ../pixman/bin/*.* ./;popd
        pushd lib;ln -fs ../pixman/lib/*.* ./;popd
        pushd include;ln -fs ../pixman/include/* ./;popd
        pushd lib/pkgconfig;ln -fs ../../pixman/lib/pkgconfig/* ./;popd
        popd
        popd
    fi
fi

# ------------------------------------------------------------------------------
# cairo
# ------------------------------------------------------------------------------
CAIRO_VERSION=1.14.6
CAIRO_INSTALL_PREFIX=${CROSSBUILD_INSTALL_PREFIX}/cairo-${CAIRO_VERSION}
CAIRO_SOURCE_URL=https://cairographics.org/releases/cairo-${CAIRO_VERSION}.tar.xz
if [ "${CAIRO}" == "1" ]; then
    echo "=============================== CAIRO ================================"
    if [ "${__download}" == "1" ]; then
        download ${CAIRO_SOURCE_URL}
    fi

    if [ "${__remove_before_install}" == "1"  ]; then
        remove ${CAIRO_INSTALL_PREFIX}
    fi

    if [ "${__install}" == "1" ]; then
        tar xvf ${__download_dir}/cairo-${CAIRO_VERSION}.tar.xz
        pushd ${__build_dir}/cairo-${CAIRO_VERSION}
        libtoolize --force \
        && aclocal \
        && autoheader \
        && automake --force-missing --add-missing \
        && autoconf \
        && ./configure \
                --build=${__buildtype} \
                --host=${__toolchain} \
                --prefix=${CAIRO_INSTALL_PREFIX} \
                --enable-shared \
                --enable-xcb=no \
                --enable-xlib=no \
                --enable-xlib-xcb=no \
                --enable-pthread=no \
        || exit 1
        make -j${__build_proc_num} install || exit 1

        pushd ${CROSSBUILD_INSTALL_PREFIX}
        rm -f cairo && ln -fs cairo-${CAIRO_VERSION} cairo
        pushd bin;ln -fs ../cairo/bin/*.* ./;popd
        pushd lib;ln -fs ../cairo/lib/*.* ./;popd
        pushd include;ln -fs ../cairo/include/* ./;popd
        pushd lib/pkgconfig;ln -fs ../../cairo/lib/pkgconfig/* ./;popd
        popd
        popd
    fi
fi

# ------------------------------------------------------------------------------
# openslide
# ------------------------------------------------------------------------------
OPENSLIDE_VERSION=3.4.2a
OPENSLIDE_INSTALL_PREFIX=${CROSSBUILD_INSTALL_PREFIX}/openslide-${OPENSLIDE_VERSION}
OPENSLIDE_SOURCE_URL=https://github.com/mircen/openslide/archive/master.tar.gz
if [ "${OPENSLIDE}" == "1" ]; then
    echo "========================= OPENSLIDE =============================="
    if [ "${__download}" == "1" ]; then
        if [ "$__use_cea_mirror" = "1" ]; then
            # It was necessary to rename the original file because its name did
            # not contain anything to know that it provides openslide. It is
            # necessary to have particular case where cea mirror file name 
            # is not the same as original file name.
            download "${__mirror_url}/sources/openslide-${OPENSLIDE_VERSION}.tar.gz"
        else
            download ${OPENSLIDE_SOURCE_URL} openslide-${OPENSLIDE_VERSION}.tar.gz
        fi
    fi

    if [ "${__remove_before_install}" == "1"  ]; then
        remove ${OPENSLIDE_INSTALL_PREFIX}
    fi

    if [ "${__install}" == "1" ]; then
        tar xvf ${__download_dir}/openslide-${OPENSLIDE_VERSION}.tar.gz
        pushd ${__build_dir}/openslide-master
        
        cat << EOF > openslide-${OPENSLIDE_VERSION}.patch
diff -NurB --strip-trailing-cr --suppress-common-lines Makefile.am Makefile.am
--- Makefile.am	2017-07-23 23:00:28.915949037 +0200
+++ Makefile.am	2017-07-23 23:09:36.958805364 +0200
@@ -59,7 +59,7 @@
 # openslide-tables.c.  As the lesser of evils, recursively invoke make.
 src/openslide-tables.c: src/make-tables.c
 	@\$(MAKE) \$(AM_MAKEFLAGS) src/make-tables\$(EXEEXT)
-	\$(AM_V_GEN)src/make-tables\$(EXEEXT) "\$@"
+	\$(AM_V_GEN)\$(COMMAND_PREFIX) src/make-tables\$(EXEEXT) "\$@"
 
 if WINDOWS_RESOURCES
 src_libopenslide_la_SOURCES += src/openslide-dll.rc
EOF
        patch -f -N -i openslide-${OPENSLIDE_VERSION}.patch -p0
        libtoolize --force \
        && aclocal \
        && autoheader \
        && automake --force-missing --add-missing \
        && autoconf \
        && ./configure \
                --build=${__buildtype} \
                --host=${__toolchain} \
                --prefix=${OPENSLIDE_INSTALL_PREFIX} \
                --enable-shared \
        || exit 1
        
        COMMAND_PREFIX=${__wine_cmd} \
        make -j${__build_proc_num} install || exit 1

        pushd ${CROSSBUILD_INSTALL_PREFIX}
        rm -f openslide && ln -fs openslide-${OPENSLIDE_VERSION} openslide
        pushd bin;ln -fs ../openslide/bin/*.* ./;popd
        pushd lib;ln -fs ../openslide/lib/*.* ./;popd
        pushd include;ln -fs ../openslide/include/* ./;popd
        pushd lib/pkgconfig;ln -fs ../../openslide/lib/pkgconfig/* ./;popd
        popd
        popd
    fi
fi

# ------------------------------------------------------------------------------
# dcmtk
# ------------------------------------------------------------------------------
DCMTK_VERSION=3.6.0
DCMTK_INSTALL_PREFIX=${CROSSBUILD_INSTALL_PREFIX}/dcmtk-${DCMTK_VERSION}
DCMTK_SOURCE_URL=ftp://dicom.offis.de/pub/dicom/offis/software/dcmtk/dcmtk${DCMTK_VERSION//./}/dcmtk-${DCMTK_VERSION}.tar.gz
if [ "${DCMTK}" == "1" ]; then
    echo "=============================== DCMTK ================================"
    if [ "${__download}" == "1" ]; then
        download ${DCMTK_SOURCE_URL}
    fi

    if [ "${__remove_before_install}" == "1"  ]; then
        remove ${DCMTK_INSTALL_PREFIX}
    fi

    if [ "${__install}" == "1" ]; then
        tar xvf ${__download_dir}/dcmtk-${DCMTK_VERSION}.tar.gz
        pushd ${__build_dir}/dcmtk-${DCMTK_VERSION}

        cat << EOF > dcmtk-${DCMTK_VERSION}.patch
diff -NurwB --strip-trailing-cr --suppress-common-lines ofstd/include/dcmtk/ofstd/offile.h ofstd/include/dcmtk/ofstd/offile.h
--- ofstd/include/dcmtk/ofstd/offile.h  2016-07-26 15:08:40.222470801 +0200
+++ ofstd/include/dcmtk/ofstd/offile.h  2016-07-26 15:08:05.218487436 +0200
@@ -196,7 +196,7 @@
   OFBool popen(const char *command, const char *modes)
   {
     if (file_) fclose();
-#ifdef _WIN32
+#if(defined(_WIN32) && !defined(__MINGW32__))
     file_ = _popen(command, modes);
 #else
     file_ = :: popen(command, modes);
@@ -258,7 +258,7 @@
     {
       if (popened_)
       {
-#ifdef _WIN32
+#if(defined(_WIN32) && !defined(__MINGW32__))
         result = _pclose(file_);
 #else
         result = :: pclose(file_);
diff -NurwB --strip-trailing-cr --suppress-common-lines CMakeLists.txt CMakeLists.txt
--- CMakeLists.txt  2016-07-27 16:45:48.057759327 +0200
+++ CMakeLists.txt  2016-07-27 16:50:08.993674806 +0200
@@ -222,6 +222,11 @@
 # define libraries that must be linked to most Windows applications
 IF(WIN32)
   SET(WIN32_STD_LIBRARIES ws2_32 netapi32 wsock32)
+  FOREACH(WIN32_LIB \${WIN32_STD_LIBRARIES})
+    SET(CMAKE_CXX_STANDARD_LIBRARIES "\${CMAKE_CXX_STANDARD_LIBRARIES} -l\${WIN32_LIB}" )
+  ENDFOREACH()
+  SET(CMAKE_CXX_FLAGS "-fpermissive \${CMAKE_CXX_FLAGS}")
+  
   # settings for Borland C++
   IF(CMAKE_CXX_COMPILER MATCHES bcc32)
     # to be checked: further settings required?
diff -NurwB --strip-trailing-cr --suppress-common-lines dcmpstat/libsrc/CMakeLists.txt dcmpstat/libsrc/CMakeLists.txt
--- dcmpstat/libsrc/CMakeLists.txt  2016-07-27 17:42:30.268570055 +0200
+++ dcmpstat/libsrc/CMakeLists.txt  2016-07-27 17:42:30.268570055 +0200
@@ -3,3 +3,8 @@
 
 # declare installation files
 INSTALL_TARGETS(\${INSTALL_LIBDIR} dcmpstat)
+
+IF ((TARGET dcmpstat) AND BUILD_SHARED_LIBS)
+    ADD_DEPENDENCIES(dcmpstat dcmdsig dcmqrdb dcmqrdb dcmtls dcmsr dcmimgle)
+    TARGET_LINK_LIBRARIES(dcmpstat dcmdsig dcmqrdb dcmqrdb dcmtls dcmsr dcmimgle)
+ENDIF()
diff -NurwB --strip-trailing-cr --suppress-common-lines dcmdata/libsrc/CMakeLists.txt dcmdata/libsrc/CMakeLists.txt
--- dcmdata/libsrc/CMakeLists.txt   2016-07-27 17:42:30.268570055 +0200
+++ dcmdata/libsrc/CMakeLists.txt   2016-07-27 17:42:30.268570055 +0200
@@ -3,3 +3,8 @@
 
 # declare installation files
 INSTALL_TARGETS(\${INSTALL_LIBDIR} dcmdata)
+
+IF ((TARGET dcmdata) AND BUILD_SHARED_LIBS)
+    ADD_DEPENDENCIES(dcmdata oflog)
+    TARGET_LINK_LIBRARIES(dcmdata oflog)
+ENDIF()
diff -NurwB --strip-trailing-cr --suppress-common-lines dcmdata/libi2d/CMakeLists.txt dcmdata/libi2d/CMakeLists.txt
--- dcmdata/libi2d/CMakeLists.txt   2016-07-27 17:42:30.268570055 +0200
+++ dcmdata/libi2d/CMakeLists.txt   2016-07-27 17:42:30.268570055 +0200
@@ -3,3 +3,8 @@
 
 # declare installation files
 INSTALL_TARGETS(\${INSTALL_LIBDIR} libi2d)
+
+IF ((TARGET libi2d) AND BUILD_SHARED_LIBS)
+    ADD_DEPENDENCIES(libi2d dcmdata)
+    TARGET_LINK_LIBRARIES(libi2d dcmdata)
+ENDIF()
diff -NurwB --strip-trailing-cr --suppress-common-lines dcmimgle/libsrc/CMakeLists.txt dcmimgle/libsrc/CMakeLists.txt
--- dcmimgle/libsrc/CMakeLists.txt  2016-07-27 17:42:30.268570055 +0200
+++ dcmimgle/libsrc/CMakeLists.txt  2016-07-27 17:42:30.268570055 +0200
@@ -3,3 +3,8 @@
 
 # declare installation files
 INSTALL_TARGETS(\${INSTALL_LIBDIR} dcmimgle)
+
+IF ((TARGET dcmimgle) AND BUILD_SHARED_LIBS)
+    ADD_DEPENDENCIES(dcmimgle dcmdata)
+    TARGET_LINK_LIBRARIES(dcmimgle dcmdata)
+ENDIF()
diff -NurwB --strip-trailing-cr --suppress-common-lines dcmjpls/libsrc/CMakeLists.txt dcmjpls/libsrc/CMakeLists.txt
--- dcmjpls/libsrc/CMakeLists.txt   2016-07-27 17:42:30.268570055 +0200
+++ dcmjpls/libsrc/CMakeLists.txt   2016-07-27 17:42:30.268570055 +0200
@@ -6,3 +6,8 @@
 
 # declare installation files
 INSTALL_TARGETS(\${INSTALL_LIBDIR} dcmjpls)
+
+IF ((TARGET dcmjpls) AND BUILD_SHARED_LIBS)
+    ADD_DEPENDENCIES(dcmjpls dcmjpeg charls)
+    TARGET_LINK_LIBRARIES(dcmjpls dcmjpeg charls)
+ENDIF()
diff -NurwB --strip-trailing-cr --suppress-common-lines dcmjpeg/libsrc/CMakeLists.txt dcmjpeg/libsrc/CMakeLists.txt
--- dcmjpeg/libsrc/CMakeLists.txt   2016-07-27 17:42:30.268570055 +0200
+++ dcmjpeg/libsrc/CMakeLists.txt   2016-07-27 17:42:30.268570055 +0200
@@ -6,3 +6,8 @@
 
 # declare installation files
 INSTALL_TARGETS(\${INSTALL_LIBDIR} dcmjpeg)
+
+IF ((TARGET dcmjpeg) AND BUILD_SHARED_LIBS)
+    ADD_DEPENDENCIES(dcmjpeg dcmimgle ijg8 ijg12 ijg16)
+    TARGET_LINK_LIBRARIES(dcmjpeg dcmimgle ijg8 ijg12 ijg16)
+ENDIF()
diff -NurwB --strip-trailing-cr --suppress-common-lines dcmnet/libsrc/CMakeLists.txt dcmnet/libsrc/CMakeLists.txt
--- dcmnet/libsrc/CMakeLists.txt    2016-07-27 17:42:30.268570055 +0200
+++ dcmnet/libsrc/CMakeLists.txt    2016-07-27 17:42:30.272570054 +0200
@@ -3,3 +3,8 @@
 
 # declare installation files
 INSTALL_TARGETS(\${INSTALL_LIBDIR} dcmnet)
+
+IF ((TARGET dcmnet) AND BUILD_SHARED_LIBS)
+    ADD_DEPENDENCIES(dcmnet dcmdata)
+    TARGET_LINK_LIBRARIES(dcmnet dcmdata)
+ENDIF()
diff -NurwB --strip-trailing-cr --suppress-common-lines dcmqrdb/libsrc/CMakeLists.txt dcmqrdb/libsrc/CMakeLists.txt
--- dcmqrdb/libsrc/CMakeLists.txt   2016-07-27 17:42:30.268570055 +0200
+++ dcmqrdb/libsrc/CMakeLists.txt   2016-07-27 17:42:30.268570055 +0200
@@ -3,3 +3,8 @@
 
 # declare installation files
 INSTALL_TARGETS(\${INSTALL_LIBDIR} dcmqrdb)
+
+IF ((TARGET dcmqrdb) AND BUILD_SHARED_LIBS)
+    ADD_DEPENDENCIES(dcmqrdb ofstd dcmdata dcmnet)
+    TARGET_LINK_LIBRARIES(dcmqrdb ofstd dcmdata dcmnet)
+ENDIF()
diff -NurwB --strip-trailing-cr --suppress-common-lines dcmwlm/libsrc/CMakeLists.txt dcmwlm/libsrc/CMakeLists.txt
--- dcmwlm/libsrc/CMakeLists.txt    2016-07-27 17:42:30.268570055 +0200
+++ dcmwlm/libsrc/CMakeLists.txt    2016-07-27 17:42:30.268570055 +0200
@@ -3,3 +3,8 @@
 
 # declare installation files
 INSTALL_TARGETS(\${INSTALL_LIBDIR} dcmwlm)
+
+IF ((TARGET dcmwlm) AND BUILD_SHARED_LIBS)
+    ADD_DEPENDENCIES(dcmwlm dcmnet)
+    TARGET_LINK_LIBRARIES(dcmwlm dcmnet)
+ENDIF()
diff -NurwB --strip-trailing-cr --suppress-common-lines dcmsign/libsrc/CMakeLists.txt dcmsign/libsrc/CMakeLists.txt
--- dcmsign/libsrc/CMakeLists.txt   2016-07-27 17:42:30.268570055 +0200
+++ dcmsign/libsrc/CMakeLists.txt   2016-07-27 17:42:30.272570054 +0200
@@ -3,3 +3,8 @@
 
 # declare installation files
 INSTALL_TARGETS(\${INSTALL_LIBDIR} dcmdsig)
+
+IF ((TARGET dcmdsig) AND BUILD_SHARED_LIBS)
+    ADD_DEPENDENCIES(dcmdsig dcmdata)
+    TARGET_LINK_LIBRARIES(dcmdsig dcmdata)
+ENDIF()
diff -NurwB --strip-trailing-cr --suppress-common-lines dcmimage/libsrc/CMakeLists.txt dcmimage/libsrc/CMakeLists.txt
--- dcmimage/libsrc/CMakeLists.txt  2016-07-27 17:42:30.268570055 +0200
+++ dcmimage/libsrc/CMakeLists.txt  2016-07-27 17:42:30.268570055 +0200
@@ -3,3 +3,8 @@
 
 # declare installation files
 INSTALL_TARGETS(\${INSTALL_LIBDIR} dcmimage)
+
+IF ((TARGET dcmimage) AND BUILD_SHARED_LIBS)
+    ADD_DEPENDENCIES(dcmimage dcmimgle)
+    TARGET_LINK_LIBRARIES(dcmimage dcmimgle)
+ENDIF()
diff -NurwB --strip-trailing-cr --suppress-common-lines dcmtls/libsrc/CMakeLists.txt dcmtls/libsrc/CMakeLists.txt
--- dcmtls/libsrc/CMakeLists.txt    2016-07-27 17:42:30.268570055 +0200
+++ dcmtls/libsrc/CMakeLists.txt    2016-07-27 17:42:30.268570055 +0200
@@ -3,3 +3,8 @@
 
 # declare installation files
 INSTALL_TARGETS(\${INSTALL_LIBDIR} dcmtls)
+
+IF ((TARGET dcmtls) AND BUILD_SHARED_LIBS)
+    ADD_DEPENDENCIES(dcmtls dcmnet)
+    TARGET_LINK_LIBRARIES(dcmtls dcmnet)
+ENDIF()
diff -NurwB --strip-trailing-cr --suppress-common-lines oflog/libsrc/CMakeLists.txt oflog/libsrc/CMakeLists.txt
--- oflog/libsrc/CMakeLists.txt 2016-07-27 17:42:30.268570055 +0200
+++ oflog/libsrc/CMakeLists.txt 2016-07-27 17:42:30.268570055 +0200
@@ -10,3 +10,8 @@
 
 # declare installation files
 INSTALL_TARGETS(\${INSTALL_LIBDIR} oflog)
+
+IF ((TARGET oflog) AND BUILD_SHARED_LIBS)
+    ADD_DEPENDENCIES(oflog ofstd)
+    TARGET_LINK_LIBRARIES(oflog ofstd)
+ENDIF()
diff -NurwB --strip-trailing-cr --suppress-common-lines dcmsr/libsrc/CMakeLists.txt dcmsr/libsrc/CMakeLists.txt
--- dcmsr/libsrc/CMakeLists.txt 2016-07-27 17:42:30.268570055 +0200
+++ dcmsr/libsrc/CMakeLists.txt 2016-07-27 17:42:30.268570055 +0200
@@ -3,3 +3,8 @@
 
 # declare installation files
 INSTALL_TARGETS(\${INSTALL_LIBDIR} dcmsr)
+
+IF ((TARGET dcmsr) AND BUILD_SHARED_LIBS)
+    ADD_DEPENDENCIES(dcmsr dcmdata)
+    TARGET_LINK_LIBRARIES(dcmsr dcmdata)
+ENDIF()
diff -NurwB --strip-trailing-cr --suppress-common-lines CMake/osconfig.h.in CMake/osconfig.h.in
--- CMake/osconfig.h.in       2016-09-04 22:05:16.440017095 +0200
+++ CMake/osconfig.h.in       2016-09-04 22:07:29.231895567 +0200
@@ -677,7 +677,10 @@
 #define PACKAGE_VERSION_SUFFIX "@DCMTK_PACKAGE_VERSION_SUFFIX@"
 
 /* Define to the version number of this package. */
-#define PACKAGE_VERSION_NUMBER "@DCMTK_PACKAGE_VERSION_NUMBER@"
+#define PACKAGE_VERSION_NUMBER @DCMTK_PACKAGE_VERSION_NUMBER@
+
+/* Define to the version number string of this package. */
+#define PACKAGE_VERSION_NUMBER_STRING "@DCMTK_PACKAGE_VERSION_NUMBER@"
 
 /* Define path separator */
 #define PATH_SEPARATOR '@PATH_SEPARATOR@'
diff -Nruwb dcmdata/include/dcmtk/dcmdata/dcuid.h dcmdata/include/dcmtk/dcmdata/dcuid.h
--- dcmdata/include/dcmtk/dcmdata/dcuid.h       2016-09-04 22:25:38.394956271 +0200
+++ dcmdata/include/dcmtk/dcmdata/dcuid.h       2016-09-04 22:31:28.442635450 +0200
@@ -171,10 +171,10 @@
  */
 
 /// implementation version name for this version of the toolkit
-#define OFFIS_DTK_IMPLEMENTATION_VERSION_NAME   "OFFIS_DCMTK_" PACKAGE_VERSION_NUMBER
+#define OFFIS_DTK_IMPLEMENTATION_VERSION_NAME   "OFFIS_DCMTK_" PACKAGE_VERSION_NUMBER_STRING
 
 /// implementation version name for this version of the toolkit, used for files received in "bit preserving" mode
-#define OFFIS_DTK_IMPLEMENTATION_VERSION_NAME2  "OFFIS_DCMBP_" PACKAGE_VERSION_NUMBER
+#define OFFIS_DTK_IMPLEMENTATION_VERSION_NAME2  "OFFIS_DCMBP_" PACKAGE_VERSION_NUMBER_STRING
EOF

        patch -f -N -i dcmtk-${DCMTK_VERSION}.patch -p0
        cmake -DCMAKE_INSTALL_PREFIX=${DCMTK_INSTALL_PREFIX} \
              -DCMAKE_FIND_ROOT_PATH=${CROSSBUILD_INSTALL_PREFIX} \
              -DCMAKE_TOOLCHAIN_FILE=${__build_dir}/toolchain-${__toolchain}.cmake \
              -DCMAKE_CROSSCOMPILING=ON \
              -DC_CHAR_SIGNED=FAILED_TO_RUN \
              -DBUILD_SHARED_LIBS=ON \
              -DDCMTK_WITH_ZLIB=${ZLIB_INSTALL_PREFIX} \
              -DDCMTK_WITH_PNG=${LIBPNG_INSTALL_PREFIX} \
              -DDCMTK_WITH_TIFF=${LIBTIFF_INSTALL_PREFIX} \
        || exit 1

        make -j${__build_proc_num} install || exit 1

        pushd ${CROSSBUILD_INSTALL_PREFIX}
        rm -f dcmtk && ln -fs dcmtk-${DCMTK_VERSION} dcmtk
        mv dcmtk/lib/*.dll dcmtk/bin/
        pushd bin;ln -fs ../dcmtk/bin/*.* ./;popd
        pushd lib;ln -fs ../dcmtk/lib/*.* ./;popd
        pushd include;ln -fs ../dcmtk/include/* ./;popd
        #pushd lib/pkgconfig;ln -fs ../../dcmtk/lib/pkgconfig/* ./;popd
        popd
        popd
    fi
fi

# ------------------------------------------------------------------------------
# netcdf
# ------------------------------------------------------------------------------
NETCDF_VERSION=4.1.3
NETCDF_INSTALL_PREFIX=${CROSSBUILD_INSTALL_PREFIX}/netcdf-${NETCDF_VERSION}
NETCDF_SOURCE_URL=ftp://ftp.unidata.ucar.edu/pub/netcdf/netcdf-${NETCDF_VERSION}.tar.gz
if [ "${NETCDF}" == "1" ]; then
    echo "========================= NETCDF =============================="
    if [ "${__download}" == "1" ]; then
        download ${NETCDF_SOURCE_URL}
    fi

    if [ "${__remove_before_install}" == "1"  ]; then
        remove ${NETCDF_INSTALL_PREFIX}
    fi

    if [ "${__install}" == "1" ]; then
        tar xvf ${__download_dir}/netcdf-${NETCDF_VERSION}.tar.gz
        pushd ${__build_dir}/netcdf-${NETCDF_VERSION}

        cat << EOF > netcdf-${NETCDF_VERSION}.patch
diff -NurwB --strip-trailing-cr --suppress-common-lines man4/netcdf-f90.texi man4/netcdf-f90.texi
--- man4/netcdf-f90.texi   2016-09-30 12:02:50.765773875 +0200
+++ man4/netcdf-f90.texi   2016-09-30 12:07:27.193736177 +0200
@@ -2082,7 +2082,6 @@
 The name of the
 group will be copied to this character array. The name will be less
 than NF90_MAX_NAME in length.
-@item
 
 @end table
 
@@ -6979,7 +6978,7 @@
 @node FORTRAN 77 to Fortran 90 Transition Guide, Combined Index, Summary of Fortran 90 Interface, Top
 @appendix Appendix B - FORTRAN 77 to Fortran 90 Transition Guide
 
-@unnumberedsubsec The new Fortran 90 interface 
+@unnumberedsec The new Fortran 90 interface 
 
 The Fortran 90 interface to the netCDF library closely follows the
 FORTRAN 77 interface. In most cases, function and constant names and
@@ -7001,7 +7000,7 @@
 versions may be implemented entirely in Fortran 90, adding additional
 error checking possibilities.
 
-@unnumberedsubsec Changes to Inquiry functions 
+@unnumberedsec Changes to Inquiry functions 
 
 In the Fortran 90 interface there are two inquiry functions each for
 dimensions, variables, and attributes, and a single inquiry function
@@ -7035,7 +7034,7 @@
  INTEGER FUNCTION  NF_INQ_ATTNAME    (NCID, VARID, ATTNUM, name)
 @end example
 
-@unnumberedsubsec Changes to put and get function 
+@unnumberedsec Changes to put and get function 
 
 The biggest simplification in the Fortran 90 is in the nf90_put_var
 and nf90_get_var functions. Both functions are overloaded: the values

diff -NurB --strip-trailing-cr --suppress-common-lines libdispatch/v2i.c libdispatch/v2i.c
--- libdispatch/v2i.c   2017-06-24 02:08:44.200352916 +0200
+++ libdispatch/v2i.c   2017-06-24 22:43:16.372951392 +0200
@@ -11,6 +11,7 @@
 #include <stdio.h>
 #include <stdarg.h>
 #include "netcdf.h"
+#include "nc.h"
 
 /* The subroutines in error.c emit no messages unless NC_VERBOSE bit
  * is on.  They call exit() when NC_FATAL bit is on. */
@@ -38,7 +39,7 @@
  * any additional cost was lost in measurement variation.
  */
 
-# include "onstack.h"
+# include "../libsrc/onstack.h"
 
 static size_t
 nvdims(int ncid, int varid)
EOF
        patch -f -N -i netcdf-${NETCDF_VERSION}.patch -p0
        libtoolize --force \
        && aclocal \
        && autoheader \
        && automake --force-missing --add-missing \
        && autoconf \
        && ./configure \
                --build=${__buildtype} \
                --host=${__toolchain} \
                --prefix=${NETCDF_INSTALL_PREFIX} \
                --enable-shared \
                --enable-dll \
                --disable-fortran-type-check \
        || exit 1
        make -j${__build_proc_num} install || exit 1

        pushd ${CROSSBUILD_INSTALL_PREFIX}
        rm -f netcdf && ln -fs netcdf-${NETCDF_VERSION} netcdf
        pushd bin;ln -fs ../netcdf/bin/*.* ./;popd
        pushd lib;ln -fs ../netcdf/lib/*.* ./;popd
        pushd include;ln -fs ../netcdf/include/* ./;popd
        pushd lib/pkgconfig;ln -fs ../../netcdf/lib/pkgconfig/* ./;popd
        popd
        popd
    fi
fi

# ------------------------------------------------------------------------------
# minc
# ------------------------------------------------------------------------------
MINC_VERSION=2.2.00
MINC_INSTALL_PREFIX=${CROSSBUILD_INSTALL_PREFIX}/minc-${MINC_VERSION}
MINC_SOURCE_URL=http://packages.bic.mni.mcgill.ca/tgz/minc-${MINC_VERSION}.tar.gz
if [ "${MINC}" == "1" ]; then
    echo "========================= MINC =============================="
    if [ "${__download}" == "1" ]; then
        download ${MINC_SOURCE_URL}
    fi

    if [ "${__remove_before_install}" == "1"  ]; then
        remove ${MINC_INSTALL_PREFIX}
    fi

    if [ "${__install}" == "1" ]; then
        tar xvf ${__download_dir}/minc-${MINC_VERSION}.tar.gz
        pushd ${__build_dir}/minc-${MINC_VERSION}

        cat << EOF > minc-${MINC_VERSION}.patch
diff -NurwB --strip-trailing-cr --suppress-common-lines progs/CMakeLists.txt progs/CMakeLists.txt
--- progs/CMakeLists.txt    2016-10-03 10:37:06.979561616 +0200
+++ progs/CMakeLists.txt    2016-10-03 10:41:26.611522473 +0200
@@ -188,12 +188,22 @@
  DEPENDS \${CMAKE_CURRENT_SOURCE_DIR}/mincpik/mincpik.in)
 
 
-INSTALL(FILES
-  \${CMAKE_CURRENT_BINARY_DIR}/minchistory
-  PERMISSIONS OWNER_EXECUTE OWNER_WRITE OWNER_READ GROUP_EXECUTE GROUP_READ  WORLD_EXECUTE WORLD_READ
-   DESTINATION bin )
+INSTALL(FILES \${CMAKE_CURRENT_BINARY_DIR}/minchistory
+        DESTINATION bin
+        PERMISSIONS OWNER_EXECUTE 
+                    OWNER_WRITE 
+                    OWNER_READ 
+                    GROUP_EXECUTE 
+                    GROUP_READ  
+                    WORLD_EXECUTE 
+                    WORLD_READ )
 
-INSTALL(PROGRAMS
-  \${CMAKE_CURRENT_BINARY_DIR}/mincpik
-  PERMISSIONS OWNER_EXECUTE OWNER_WRITE OWNER_READ GROUP_EXECUTE GROUP_READ  WORLD_EXECUTE WORLD_READ
-   DESTINATION bin )
+INSTALL(PROGRAMS \${CMAKE_CURRENT_BINARY_DIR}/mincpik
+        DESTINATION bin
+        PERMISSIONS OWNER_EXECUTE 
+                    OWNER_WRITE 
+                    OWNER_READ 
+                    GROUP_EXECUTE 
+                    GROUP_READ     
+                    WORLD_EXECUTE 
+                    WORLD_READ )
diff -NurwB --strip-trailing-cr --suppress-common-lines libsrc/minc_convenience.c libsrc/minc_convenience.c
--- libsrc/minc_convenience.c   2016-10-03 16:25:12.791989614 +0200
+++ libsrc/minc_convenience.c   2016-10-03 16:38:58.115598859 +0200
@@ -159,6 +159,10 @@
 #include <unistd.h>             /* for getpid() */
 #endif /* HAVE_UNISTD_H */
 
+#if WIN32
+#include <winsock2.h>
+#endif
+
 /* Private functions */
 PRIVATE int MI_create_dim_variable(int cdfid, char *name, 
                                    nc_type datatype, int ndims);
@@ -1501,7 +1505,7 @@
 
 
     time(&now);
-#ifdef _MSC_VER
+#if defined(_MSC_VER) || defined(WIN32)
     memcpy(&tm_buf, localtime(&now), sizeof(tm_buf));
 #else
     localtime_r(&now, &tm_buf);

diff -NurwB --strip-trailing-cr --suppress-common-lines CMakeLists.txt CMakeLists.txt
--- CMakeLists.txt  2016-10-03 17:39:10.978733514 +0200
+++ CMakeLists.txt  2016-10-03 17:44:58.094678288 +0200
@@ -317,8 +317,14 @@
 
 ADD_DEPENDENCIES(\${VOLUME_IO_LIBRARY} \${MINC2_LIBRARY})
 
-INSTALL(TARGETS \${MINC2_LIBRARY}     \${LIBRARY_INSTALL} DESTINATION lib)
-INSTALL(TARGETS \${VOLUME_IO_LIBRARY} \${LIBRARY_INSTALL} DESTINATION lib)
+INSTALL(TARGETS \${MINC2_LIBRARY}
+        RUNTIME DESTINATION bin
+        LIBRARY DESTINATION lib
+        ARCHIVE DESTINATION lib)
+INSTALL(TARGETS \${VOLUME_IO_LIBRARY}
+        RUNTIME DESTINATION bin
+        LIBRARY DESTINATION lib
+        ARCHIVE DESTINATION lib)
 INSTALL(FILES   \${minc_HEADERS}      DESTINATION  include  )
 INSTALL(FILES   \${volume_io_HEADERS} DESTINATION include/volume_io)
 

diff -NurwB --strip-trailing-cr --suppress-common-lines conversion/dcm2mnc/minc_file.c conversion/dcm2mnc/minc_file.c
--- conversion/dcm2mnc/minc_file.c  2016-10-03 17:22:44.926912844 +0200
+++ conversion/dcm2mnc/minc_file.c  2016-10-03 17:24:34.250890709 +0200
@@ -375,7 +375,11 @@
         strcat(full_path, temp_name);
 
         if (strlen(full_path) != 0) {
+#ifdef WIN32
+            if (mkdir(full_path) && G.Debug) {
+#else
             if (mkdir(full_path, 0777) && G.Debug) {
+#endif
                 printf("Directory %s exists...\\n", full_path);
             }
             strcat(full_path, "/");
diff -NurwB --strip-trailing-cr --suppress-common-lines conversion/Acr_nema/dicom_client_routines.c conversion/Acr_nema/dicom_client_routines.c
--- conversion/Acr_nema/dicom_client_routines.c 2016-10-03 17:06:36.379124400 +0200
+++ conversion/Acr_nema/dicom_client_routines.c 2016-10-03 17:15:09.074996908 +0200
@@ -128,17 +128,24 @@
               software for any purpose.  It is provided "as is" without
               express or implied warranty.
 ---------------------------------------------------------------------------- */
+#ifdef WIN32
+#include <windows.h>
+#define sleep Sleep
+#define SIGALRM SIGTERM
+#endif
 
 #include <stdio.h>
 #include <stdlib.h>
 #include <unistd.h>
 #include <sys/types.h>
 #include <sys/stat.h>
+#ifndef WIN32
 #include <sys/wait.h>
 #include <sys/socket.h>
 #include <netinet/in.h>
 #include <arpa/inet.h>
 #include <netdb.h>
+#endif
 #include <signal.h>
 #include <sys/time.h>
 #ifdef sgi
@@ -507,9 +514,11 @@
       return FALSE;
    }
 
+#ifndef WIN32
    /* Ignore SIGPIPES in case the output connection gets closed when
       we are doing output. */
    (void) signal(SIGPIPE, SIG_IGN);
+#endif
 
    return TRUE;
 }

EOF
        patch -f -N -i minc-${MINC_VERSION}.patch -p0

        mkdir -p build
        pushd build
        cmake -DCMAKE_INSTALL_PREFIX=${MINC_INSTALL_PREFIX} \
              -DCMAKE_TOOLCHAIN_FILE=${__build_dir}/toolchain-${__toolchain}.cmake \
              -DCMAKE_CROSSCOMPILING=ON \
              -DMINC2_BUILD_SHARED_LIBS=ON \
              -DMINC2_BUILD_TOOLS=OFF \
              -DNETCDF_INCLUDE_DIR=${CROSSBUILD_INSTALL_PREFIX}/include \
              -DNETCDF_LIBRARY=${CROSSBUILD_INSTALL_PREFIX}/lib/libnetcdf.dll.a \
              -DZLIB_INCLUDE_DIR=${CROSSBUILD_INSTALL_PREFIX}/include \
              -DZLIB_LIBRARY=${CROSSBUILD_INSTALL_PREFIX}/lib/libz.dll.a \
              -DHDF5_INCLUDE_DIR=${CROSSBUILD_INSTALL_PREFIX}/include \
              -DHDF5_LIBRARY=${CROSSBUILD_INSTALL_PREFIX}/lib/libhdf5.dll.a \
5\              -DCMAKE_C_STANDARD_LIBRARIES=-lws2_32 \
              .. \
        || exit 1

        make -j${__build_proc_num} install || exit 1
        popd

        pushd ${CROSSBUILD_INSTALL_PREFIX}
        rm -f minc && ln -fs minc-${MINC_VERSION} minc
        pushd bin;ln -fs ../minc/bin/*.* ./;popd
        pushd lib;ln -fs ../minc/lib/*.* ./;popd
        pushd include;ln -fs ../minc/include/* ./;popd
        pushd lib/pkgconfig;ln -fs ../../minc/lib/pkgconfig/* ./;popd
        popd
        popd
    fi
fi

# ------------------------------------------------------------------------------
# libsvm
# ------------------------------------------------------------------------------
LIBSVM_VERSION=3.12
LIBSVM_INSTALL_PREFIX=${CROSSBUILD_INSTALL_PREFIX}/libsvm-${LIBSVM_VERSION}
LIBSVM_SOURCE_URL=http://www.csie.ntu.edu.tw/~cjlin/libsvm/oldfiles/libsvm-${LIBSVM_VERSION}.tar.gz
if [ "${LIBSVM}" == "1" ]; then
    echo "============================= LIBSVM ================================="
    if [ "${__download}" == "1" ]; then
        download ${LIBSVM_SOURCE_URL}
    fi

    if [ "${__remove_before_install}" == "1"  ]; then
        remove ${LIBSVM_INSTALL_PREFIX}
    fi

    if [ "${__install}" == "1" ]; then
        tar xvf ${__download_dir}/libsvm-${LIBSVM_VERSION}.tar.gz
        pushd ${__build_dir}/libsvm-${LIBSVM_VERSION}

        cat << EOF > libsvm-${LIBSVM_VERSION}.patch
diff -NurwB --strip-trailing-cr --suppress-common-lines Makefile Makefile
--- Makefile	2016-10-04 09:23:47.563669927 +0200
+++ Makefile	2016-10-04 11:35:02.869462182 +0200
@@ -1,25 +1,97 @@
 CXX ?= g++
+INSTALL ?= install
+INSTALL_PREFIX ?= /usr/local/libsvm
+INSTALL_BIN_PREFIX = \$(INSTALL_PREFIX)/bin
+INSTALL_LIB_PREFIX = \$(INSTALL_PREFIX)/lib
+INSTALL_INCLUDE_PREFIX = \$(INSTALL_PREFIX)/include
+MKDIR ?= mkdir -p
+
 CFLAGS = -Wall -Wconversion -O3 -fPIC
 SHVER = 2
 OS = \$(shell uname)
 
-all: svm-train svm-predict svm-scale
+ifeq ("\$(TARGET_OS)", "Windows")
+	EXE_SUFFIX = .exe
+else
+	EXE_SUFFIX =
+endif
+
+SHARED_LIB_NAME = libsvm.so.\$(SHVER)
+IMP_LIB_NAME =
+
+ifeq ("\$(CROSS_COMPILE)", "1")
+	ifeq ("\$(TARGET_OS)", "Windows")
+		SHARED_LIB_NAME = libsvm-\$(SHVER).dll
+		IMP_LIB_NAME = libsvm.dll.a
+		SHARED_LIB_FLAG = -shared -Wl,--out-implib,\$(IMP_LIB_NAME) -Wl,--major-image-version,3,--minor-image-version,12 -Wl,--no-whole-archive
+	endif
+else
+	ifeq ("\$(OS)", "Darwin")
+		SHARED_LIB_FLAG = -dynamiclib -W1,-install_name,\$(SHARED_LIB_NAME)
+	else
+		SHARED_LIB_FLAG = -shared -W1,-soname,\$(SHARED_LIB_NAME)
+	endif
+endif
+
+all: svm-train\$(EXE_SUFFIX) svm-predict\$(EXE_SUFFIX) svm-scale\$(EXE_SUFFIX)
 
 lib: svm.o
-	if [ "\$(OS)" = "Darwin" ]; then \\
-		SHARED_LIB_FLAG="-dynamiclib -W1,-install_name,libsvm.so.\$(SHVER)"; \\
-	else \\
-		SHARED_LIB_FLAG="-shared -W1,-soname,libsvm.so.\$(SHVER)"; \\
-	fi; \\
-	\$(CXX) \$\${SHARED_LIB_FLAG} svm.o -o libsvm.so.\$(SHVER)
-
-svm-predict: svm-predict.c svm.o
-	\$(CXX) \$(CFLAGS) svm-predict.c svm.o -o svm-predict -lm
-svm-train: svm-train.c svm.o
-	\$(CXX) \$(CFLAGS) svm-train.c svm.o -o svm-train -lm
-svm-scale: svm-scale.c
-	\$(CXX) \$(CFLAGS) svm-scale.c -o svm-scale
+	\$(CXX) \$(SHARED_LIB_FLAG) svm.o -o \$(SHARED_LIB_NAME)
+
+svm-predict\$(EXE_SUFFIX): svm-predict.c svm.o
+	\$(CXX) \$(CFLAGS) svm-predict.c svm.o -o svm-predict\$(EXE_SUFFIX) -lm
+svm-train\$(EXE_SUFFIX): svm-train.c svm.o
+	\$(CXX) \$(CFLAGS) svm-train.c svm.o -o svm-train\$(EXE_SUFFIX) -lm
+svm-scale\$(EXE_SUFFIX): svm-scale.c
+	\$(CXX) \$(CFLAGS) svm-scale.c -o svm-scale\$(EXE_SUFFIX)
 svm.o: svm.cpp svm.h
 	\$(CXX) \$(CFLAGS) -c svm.cpp
 clean:
-	rm -f *~ svm.o svm-train svm-predict svm-scale libsvm.so.\$(SHVER)
+	rm -f *~ svm.o \\
+		 svm-train\$(EXE_SUFFIX) \\
+		 svm-predict\$(EXE_SUFFIX) \\
+		 svm-scale\$(EXE_SUFFIX) \\
+		 \$(SHARED_LIB_NAME) \\
+		 \$(IMP_LIB_NAME)
+	
+install-svm-predict: svm-predict\$(EXE_SUFFIX)
+	\$(MKDIR) \$(INSTALL_BIN_PREFIX); \\
+	\$(INSTALL) \\
+		svm-predict\$(EXE_SUFFIX) \\
+		\$(INSTALL_BIN_PREFIX)
+	
+install-svm-train: svm-train\$(EXE_SUFFIX)
+	\$(MKDIR) \$(INSTALL_BIN_PREFIX); \\
+	\$(INSTALL) \\
+		svm-train\$(EXE_SUFFIX) \\
+		\$(INSTALL_BIN_PREFIX)
+	
+install-svm-scale: svm-scale\$(EXE_SUFFIX)
+	\$(MKDIR) \$(INSTALL_BIN_PREFIX); \\
+	\$(INSTALL) \\
+		svm-scale\$(EXE_SUFFIX) \\
+		\$(INSTALL_BIN_PREFIX)
+
+install-lib: lib
+	\$(MKDIR) \$(INSTALL_LIB_PREFIX); \\
+	if [ "\$(TARGET_OS)" = "Windows" ]; then \\
+		\$(MKDIR) \$(INSTALL_BIN_PREFIX); \\
+		\$(INSTALL) \\
+			\$(SHARED_LIB_NAME) \\
+			\$(INSTALL_BIN_PREFIX); \\
+		\$(INSTALL) \\
+			\$(IMP_LIB_NAME) \\
+			\$(INSTALL_LIB_PREFIX); \\
+	else \\
+		\$(INSTALL) \\
+			\$(SHARED_LIB_NAME) \\
+			\$(INSTALL_LIB_PREFIX); \\
+	fi
+
+install-include: svm.h
+	\$(MKDIR) \$(INSTALL_INCLUDE_PREFIX); \\
+	\$(INSTALL) \\
+		svm.h \\
+		\$(INSTALL_INCLUDE_PREFIX);
+
+install: install-svm-predict install-svm-train install-svm-scale install-lib install-include

EOF
        patch -f -N -i libsvm-${LIBSVM_VERSION}.patch -p0

        INSTALL_PREFIX=${LIBSVM_INSTALL_PREFIX} \
        CROSS_COMPILE=1 \
        TARGET_OS=Windows \
        make -j${__build_proc_num} install || exit 1

        pushd ${CROSSBUILD_INSTALL_PREFIX}
        rm -f libsvm && ln -fs libsvm-${LIBSVM_VERSION} libsvm
        pushd bin;ln -fs ../libsvm/bin/*.* ./;popd
        pushd lib;ln -fs ../libsvm/lib/*.* ./;popd
        pushd include;ln -fs ../libsvm/include/* ./;popd
        #pushd lib/pkgconfig;ln -fs ../../libsvm/lib/pkgconfig/* ./;popd
        popd
        popd
    fi
fi

# ------------------------------------------------------------------------------
# qt
# ------------------------------------------------------------------------------
QT_VERSION=4.8.6
QT_INSTALL_PREFIX=${CROSSBUILD_INSTALL_PREFIX}/qt-${QT_VERSION}
QT_INSTALL_PREFIX_WINE=${CROSSBUILD_INSTALL_PREFIX_WINE}\\qt-${QT_VERSION}
QT_SOURCE_URL=http://www.mirrorservice.org/sites/download.qt-project.org/archive/qt/${QT_VERSION%.*}/${QT_VERSION}/qt-everywhere-opensource-src-${QT_VERSION}.tar.gz
QT_DEPENDENCIES="zlib libiconv libpng libtiff libjpeg"
if [ "${QT}" == "1" ]; then
    echo "================================= QT ================================="
    if [ "${__download}" == "1" ]; then
        download ${QT_SOURCE_URL}
    fi

    if [ "${__remove_before_install}" == "1"  ]; then
        remove ${QT_INSTALL_PREFIX}
    fi

    if [ "${__install}" == "1" ]; then
        tar xvf ${__download_dir}/qt-everywhere-opensource-src-${QT_VERSION}.tar.gz
        pushd ${__build_dir}/qt-everywhere-opensource-src-${QT_VERSION}
        cat << EOF > qt-${QT_VERSION}.patch
diff -NurwB --strip-trailing-cr --suppress-common-lines mkspecs/win32-g++/qmake.conf mkspecs/win32-g++/qmake.conf
--- mkspecs/win32-g++/qmake.conf	2016-09-19 12:00:31.525586417 +0200
+++ mkspecs/win32-g++/qmake.conf	2016-09-19 12:08:59.169464672 +0200
@@ -82,26 +82,16 @@
 QMAKE_LIBS_COMPAT       = -ladvapi32 -lshell32 -lcomdlg32 -luser32 -lgdi32 -lws2_32
 QMAKE_LIBS_QT_ENTRY     = -lmingw32 -lqtmain
 
-!isEmpty(QMAKE_SH) {
     MINGW_IN_SHELL      = 1
 	QMAKE_DIR_SEP		= /
 	QMAKE_QMAKE		~= s,\\\\\\\\,/,
-	QMAKE_COPY		= cp
-	QMAKE_COPY_DIR		= cp -r
+	QMAKE_COPY		= cp -f
+	QMAKE_COPY_DIR		= cp -rf
 	QMAKE_MOVE		= mv
-	QMAKE_DEL_FILE		= rm
+	QMAKE_DEL_FILE		= rm -f
 	QMAKE_MKDIR		= mkdir -p
 	QMAKE_DEL_DIR		= rmdir
     QMAKE_CHK_DIR_EXISTS = test -d
-} else {
-	QMAKE_COPY		= copy /y
-	QMAKE_COPY_DIR		= xcopy /s /q /y /i
-	QMAKE_MOVE		= move
-	QMAKE_DEL_FILE		= del
-	QMAKE_MKDIR		= mkdir
-	QMAKE_DEL_DIR		= rmdir
-    QMAKE_CHK_DIR_EXISTS	= if not exist
-}
 
 QMAKE_MOC		= \$\$[QT_INSTALL_BINS]\$\${DIR_SEPARATOR}moc\$\${EXE_SUFFIX}
 QMAKE_UIC		= \$\$[QT_INSTALL_BINS]\$\${DIR_SEPARATOR}uic\$\${EXE_SUFFIX}

diff -NurwB --strip-trailing-cr --suppress-common-lines src/3rdparty/webkit/Source/WebKit/qt/tests/hybridPixmap/hybridPixmap.pro src/3rdparty/webkit/Source/WebKit/qt/tests/hybridPixmap/hybridPixmap.pro
--- src/3rdparty/webkit/Source/WebKit/qt/tests/hybridPixmap/hybridPixmap.pro    2016-09-06 11:06:13.059378011 +0200
+++ src/3rdparty/webkit/Source/WebKit/qt/tests/hybridPixmap/hybridPixmap.pro    2016-09-06 11:07:29.939305675 +0200
@@ -8,4 +8,5 @@
 HEADERS += widget.h
 FORMS += widget.ui
 RESOURCES += resources.qrc
+INCLUDEPATH += \$\$PWD
 CONFIG += console
diff -NurwB --strip-trailing-cr --suppress-common-lines src/gui/dialogs/dialogs.pri src/gui/dialogs/dialogs.pri
--- src/gui/dialogs/dialogs.pri 2016-09-06 10:41:23.959866021 +0200
+++ src/gui/dialogs/dialogs.pri 2016-09-06 10:43:33.495858178 +0200
@@ -89,7 +89,8 @@
 wince*|symbian: FORMS += dialogs/qfiledialog_embedded.ui
 else: FORMS += dialogs/qfiledialog.ui
 
-INCLUDEPATH += \$\$PWD
+INCLUDEPATH += \$\$PWD \\
+               \$\$PWD/..
 SOURCES += \\
 	dialogs/qabstractprintdialog.cpp \\
 	dialogs/qabstractpagesetupdialog.cpp \\

diff -NurwB --strip-trailing-cr --suppress-common-lines src/activeqt/container/container.pro src/activeqt/container/container.pro
--- src/activeqt/container/container.pro	2016-09-16 09:28:36.776433633 +0200
+++ src/activeqt/container/container.pro	2016-09-16 10:38:36.425704796 +0200
@@ -20,6 +20,7 @@
 LIBS    += -lole32 -loleaut32
 !wince*:LIBS    += -luser32 -lgdi32 -ladvapi32
 win32-g++*:LIBS += -luuid
+UI_HEADERS_DIR = ../../../include/ActiveQt
 
 HEADERS =   ../control/qaxaggregated.h \\
             qaxbase.h \\
diff -NurwB --strip-trailing-cr --suppress-common-lines src/activeqt/control/qaxserverbase.cpp src/activeqt/control/qaxserverbase.cpp
--- src/activeqt/control/qaxserverbase.cpp  2016-09-16 11:52:56.857774853 +0200
+++ src/activeqt/control/qaxserverbase.cpp  2016-09-16 12:11:18.314979120 +0200
@@ -1800,9 +1800,7 @@
     // make sure we get a resize event even if not embedded as a control
     if (!m_hWnd && !qt.widget->isVisible() && newSize != oldSize) {
         QResizeEvent resizeEvent(newSize, oldSize);
-#ifndef QT_DLL // import from static library
-        extern bool qt_sendSpontaneousEvent(QObject*,QEvent*);
-#endif
+//        extern bool qt_sendSpontaneousEvent(QObject*,QEvent*);
         qt_sendSpontaneousEvent(qt.widget, &resizeEvent);
     }
     m_currentExtent = qt.widget->size();
@@ -4069,12 +4067,12 @@
 }
 
 
-#ifdef QT_DLL // avoid conflict with symbol in static lib
+//#ifdef QT_DLL // avoid conflict with symbol in static lib
 bool qt_sendSpontaneousEvent(QObject *o, QEvent *e)
 {
     return QCoreApplication::sendSpontaneousEvent(o, e);
 }
-#endif
+//#endif
 
 /*
     Tries to set the size of the control.

diff -NurB --strip-trailing-cr --suppress-common-lines tools/activeqt/testcon/mainwindow.h tools/activeqt/testcon/mainwindow.h
--- tools/activeqt/testcon/mainwindow.h 2017-07-28 14:30:34.418259465 +0200
+++ tools/activeqt/testcon/mainwindow.h 2017-07-28 14:30:54.506072286 +0200
@@ -42,6 +42,7 @@
 #ifndef MAINWINDOW_H
 #define MAINWINDOW_H
 
+#include <QtCore/qglobal.h>
 #include "ui_mainwindow.h"
 
 QT_BEGIN_NAMESPACE

diff -NurwB --strip-trailing-cr --suppress-common-lines tools/linguist/shared/profileevaluator.cpp tools/linguist/shared/profileevaluator.cpp
--- tools/linguist/shared/profileevaluator.cpp  2016-09-16 12:17:03.442184174 +0200
+++ tools/linguist/shared/profileevaluator.cpp  2016-09-16 12:17:13.118162380 +0200
@@ -65,7 +65,7 @@
 #include <unistd.h>
 #include <sys/utsname.h>
 #else
-#include <Windows.h>
+#include <windows.h>
 #endif
 #include <stdio.h>
 #include <stdlib.h>

diff -NurwB --strip-trailing-cr --suppress-common-lines examples/help/contextsensitivehelp/contextsensitivehelp.pro examples/help/contextsensitivehelp/contextsensitivehelp.pro
--- examples/help/contextsensitivehelp/contextsensitivehelp.pro 2016-09-16 12:22:24.917473766 +0200
+++ examples/help/contextsensitivehelp/contextsensitivehelp.pro 2016-09-16 12:23:52.833284234 +0200
@@ -1,5 +1,7 @@
 TEMPLATE = app
 
+INCLUDEPATH += \$\$PWD
+
 CONFIG += help
 
 SOURCES += main.cpp \\

diff -NurwB --strip-trailing-cr --suppress-common-lines examples/ipc/ipc.pro examples/ipc/ipc.pro
--- examples/ipc/ipc.pro    2016-09-06 11:26:06.041900104 +0200
+++ examples/ipc/ipc.pro    2016-09-06 11:26:16.641888238 +0200
@@ -1,6 +1,6 @@
 TEMPLATE      = subdirs
 # no QSharedMemory
-!vxworks:!qnx:SUBDIRS = sharedmemory
+!vxworks:!qnx:SUBDIRS = sharedmemory
 !wince*: SUBDIRS += localfortuneserver localfortuneclient
 
 # install
diff -NurwB --strip-trailing-cr --suppress-common-lines demos/browser/browser.pro demos/browser/browser.pro
--- demos/browser/browser.pro   2016-09-06 11:32:14.229502420 +0200
+++ demos/browser/browser.pro   2016-09-06 11:34:09.937383362 +0200
@@ -63,6 +63,8 @@
     xbel.cpp \\
     main.cpp
 
+INCLUDEPATH += \$\$PWD
+
 RESOURCES += data/data.qrc htmls/htmls.qrc
 
 build_all:!build_pass {
EOF
        patch -f -N -i qt-${QT_VERSION}.patch -p0

        # It is necessary to unset toolchain for qmake build otherwise -platform 
        # parameter is overriden and qmake build fails
        unset_toolchain

        #CFLAGS="$(get_c_flags ${QT_DEPENDENCIES}) -DMNG_USE_DLL"
        CFLAGS="$(get_c_flags ${QT_DEPENDENCIES})"
        CXXFLAGS="${CFLAGS}"
        LDFLAGS="$(get_link_flags ${QT_DEPENDENCIES})"
        #echo "CFLAGS: ${CFLAGS}"
        #echo "CXXFLAGS: ${CXXFLAGS}"
        #echo "LDFLAGS: ${LDFLAGS}"

        #-arch x86_64
        ./configure \
                -opensource \
                -confirm-license \
                -debug-and-release \
                -verbose \
                -xplatform win32-g++ \
                -platform linux-g++-64 \
                -no-pch \
                -make libs \
                -make tools \
                -make examples \
                -make demos \
                -make docs \
                -make translations \
                -device-option CROSS_COMPILE=${__toolchain}- \
                -device-option QMAKE_SH=bash \
                -prefix ${QT_INSTALL_PREFIX} \
                -D QT_SHAREDMEMORY \
                -D QT_SYSTEMSEMAPHORE \
                -I ${CROSSBUILD_INSTALL_PREFIX}/include \
                ${CXXFLAGS} \
                -L ${CROSSBUILD_INSTALL_PREFIX}/lib \
                ${LDFLAGS} \
        || exit 1

        make -j${__build_proc_num} || exit 1
        make -j${__build_proc_num} install || exit 1
        
        # Set toolchain again
        set_toolchain

        pushd ${CROSSBUILD_INSTALL_PREFIX}
        cat << EOF > qt-${QT_VERSION}/bin/qt.conf
[Paths]
Prefix = ..
Plugins = plugins
EOF
        rm -f qt && ln -fs qt-${QT_VERSION} qt
        pushd bin;ln -fs ../qt/bin/*.* ./;popd
        pushd lib;ln -fs ../qt/lib/*.* ./;popd
        pushd include;ln -fs ../qt/include/* ./;popd
        pushd lib/pkgconfig;ln -fs ../../qt/lib/pkgconfig/* ./;popd
        popd
        popd
    fi
fi

# ------------------------------------------------------------------------------
# qwt5
# ------------------------------------------------------------------------------
QWT5_VERSION=5.2.3
QWT5_INSTALL_PREFIX=${CROSSBUILD_INSTALL_PREFIX}/qwt5-${QWT5_VERSION}
QWT5_SOURCE_URL=http://sourceforge.mirrorservice.org/q/qw/qwt/qwt/${QWT5_VERSION}/qwt-${QWT5_VERSION}.tar.bz2

if [ "${QWT5}" == "1" ]; then
    echo "============================= QWT5 ================================="
    if [ "${__download}" == "1" ]; then
        download ${QWT5_SOURCE_URL}
    fi

    if [ "${__remove_before_install}" == "1"  ]; then
        remove ${QWT5_INSTALL_PREFIX}
    fi

    if [ "${__install}" == "1" ]; then
        tar xvf ${__download_dir}/qwt-${QWT5_VERSION}.tar.bz2
        pushd ${__build_dir}/qwt-${QWT5_VERSION}

        cat << EOF > qwt5-${QWT5_VERSION}.patch
diff -NurB --strip-trailing-cr --suppress-common-lines qwtconfig.pri qwtconfig.pri
--- qwtconfig.pri	2016-12-09 23:59:04.661994152 +0100
+++ qwtconfig.pri	2016-12-09 23:59:35.869977694 +0100
@@ -12,7 +12,7 @@
 }
 
 win32 {
-    INSTALLBASE    = C:/Qwt-\$\$VERSION
+    INSTALLBASE    = ${QWT5_INSTALL_PREFIX}
 }
 
 target.path    = $$INSTALLBASE/lib

EOF
        patch -f -N -i qwt5-${QWT5_VERSION}.patch -p0

        export QTDIR=${QT_INSTALL_PREFIX}
        export QMAKESPEC=${QT_INSTALL_PREFIX}/mkspecs/win32-g++
        ${QT_INSTALL_PREFIX}/bin/qmake

        make -j${__build_proc_num} install || exit 1

        pushd ${CROSSBUILD_INSTALL_PREFIX}
        rm -f qwt5 && ln -fs qwt5-${QWT5_VERSION} qwt5

        mkdir -p qwt5-${QWT5_VERSION}/bin;
        cp -f qwt5-${QWT5_VERSION}/lib/*.dll qwt5-${QWT5_VERSION}/bin/;
        pushd bin;ln -fs ../qwt5/bin/*.* ./;popd
        pushd lib;ln -fs ../qwt5/lib/*.* ./;popd
        pushd include;ln -fs ../qwt5/include/* ./;popd
        #pushd lib/pkgconfig;ln -fs ../../qwt5/lib/pkgconfig/* ./;popd
        popd
        popd
    fi
fi

# ------------------------------------------------------------------------------
# yaml
# ------------------------------------------------------------------------------
YAML_VERSION=0.1.4
YAML_INSTALL_PREFIX=${CROSSBUILD_INSTALL_PREFIX}/yaml-${YAML_VERSION}
YAML_SOURCE_URL=http://pyyaml.org/download/libyaml/yaml-${YAML_VERSION}.tar.gz

if [ "${YAML}" == "1" ]; then
    echo "============================= YAML ================================="
    if [ "${__download}" == "1" ]; then
        download ${YAML_SOURCE_URL}
    fi

    if [ "${__remove_before_install}" == "1"  ]; then
        remove ${YAML_INSTALL_PREFIX}
    fi

    if [ "${__install}" == "1" ]; then
        tar xvf ${__download_dir}/yaml-${YAML_VERSION}.tar.gz
        pushd ${__build_dir}/yaml-${YAML_VERSION}

        cat << EOF > yaml-${YAML_VERSION}.patch
diff -NurB --strip-trailing-cr --suppress-common-lines src/Makefile.am src/Makefile.am
--- src/Makefile.am 2017-01-25 11:01:35.361746225 +0100
+++ src/Makefile.am 2017-01-25 11:12:54.689638390 +0100
@@ -1,4 +1,4 @@
 AM_CPPFLAGS = -I\$(top_srcdir)/include
 lib_LTLIBRARIES = libyaml.la
 libyaml_la_SOURCES = yaml_private.h api.c reader.c scanner.c parser.c loader.c writer.c emitter.c dumper.c
-libyaml_la_LDFLAGS = -release \$(YAML_LT_RELEASE) -version-info \$(YAML_LT_CURRENT):\$(YAML_LT_REVISION):\$(YAML_LT_AGE)
+libyaml_la_LDFLAGS = -no-undefined -release \$(YAML_LT_RELEASE) -version-info \$(YAML_LT_CURRENT):\$(YAML_LT_REVISION):\$(YAML_LT_AGE)
diff -NurB --strip-trailing-cr --suppress-common-lines include/yaml.h include/yaml.h
--- include/yaml.h  2017-01-25 11:23:50.941684681 +0100
+++ include/yaml.h  2017-01-25 11:19:10.621665846 +0100
@@ -27,13 +27,7 @@
 /** The public API declaration. */
 
 #ifdef _WIN32
-#   if defined(YAML_DECLARE_STATIC)
-#       define  YAML_DECLARE(type)  type
-#   elif defined(YAML_DECLARE_EXPORT)
-#       define  YAML_DECLARE(type)  __declspec(dllexport) type
-#   else
-#       define  YAML_DECLARE(type)  __declspec(dllimport) type
-#   endif
+#   define  YAML_DECLARE(type)  type
 #else
 #   define  YAML_DECLARE(type)  type
 #endif

EOF
        patch -f -N -i yaml-${YAML_VERSION}.patch -p0

        libtoolize --force \
        && aclocal \
        && autoheader \
        && automake --force-missing --add-missing \
        && autoconf \
        && ./configure \
                --build=${__buildtype} \
                --host=${__toolchain} \
                --prefix=${YAML_INSTALL_PREFIX} \
                --enable-shared \
        || exit 1
        make -j${__build_proc_num} install || exit 1

        pushd ${CROSSBUILD_INSTALL_PREFIX}
        rm -f yaml && ln -fs yaml-${YAML_VERSION} yaml

        mkdir -p yaml-${YAML_VERSION}/bin;
        pushd bin;ln -fs ../yaml/bin/*.* ./;popd
        pushd lib;ln -fs ../yaml/lib/*.* ./;popd
        pushd include;ln -fs ../yaml/include/* ./;popd
        pushd lib/pkgconfig;ln -fs ../../yaml/lib/pkgconfig/* ./;popd
        popd
        popd
    fi
fi

# ------------------------------------------------------------------------------
# qt installer framework
# ------------------------------------------------------------------------------
QTIFW_VERSION=2.0.5-1
QTIFW_INSTALL_PREFIX=${CROSSBUILD_INSTALL_PREFIX}/qtifw-${QTIFW_VERSION}
QTIFW_INSTALL_PREFIX_WINE=$(winepath -w ${QTIFW_INSTALL_PREFIX})
QTIFW_SOURCE_URL=http://www.mirrorservice.org/sites/download.qt-project.org/official_releases/qt-installer-framework/${QTIFW_VERSION}/QtInstallerFramework-win-x86.exe
if [ "${QTIFW}" == "1" ]; then
    echo "============================== QTIFW ==============================="
    if [ "${__download}" == "1" ]; then
        if [ "$__use_cea_mirror" = "1" ]; then
            # It was necessary to rename the original file because its name did
            # not contain anything to know that it provides openslide. It is
            # necessary to have particular case where cea mirror file name 
            # is not the same as original file name.
            download "i686" \
                     "${__mirror_url}/QtInstallerFramework-win-x86-${QTIFW_VERSION}.exe"
        else
            download "i686" \
                     ${QTIFW_SOURCE_URL} \
                     QtInstallerFramework-win-x86-${QTIFW_VERSION}.exe
        fi

        chmod +x ${__download_dir}/QtInstallerFramework-win-x86-${QTIFW_VERSION}.exe
    fi

    if [ "${__remove_before_install}" == "1"  ]; then
        remove ${QTIFW_INSTALL_PREFIX}
    fi

    if [ "${__install}" == "1" ]; then
        mkdir -p ${QTIFW_INSTALL_PREFIX}
        mkdir -p ${__build_dir}/qtifw-${QTIFW_VERSION}

        pushd ${__build_dir}/qtifw-${QTIFW_VERSION}

        cat << EOF > qtifw-${QTIFW_VERSION}.patch
diff -NurB --strip-trailing-cr --suppress-common-lines qt_installer_script qt_installer_script
--- qt_installer_script    2017-06-23 14:14:19.909643482 +0200
+++ qt_installer_script    2017-06-23 14:14:19.909643482 +0200
@@ -0,0 +1,47 @@
+var install_dir = "${QTIFW_INSTALL_PREFIX_WINE//\\/\\\\}";
+
+function Controller()
+{
+}
+
+Controller.prototype.IntroductionPageCallback = function()
+{
+    var widget = gui.currentPageWidget(); // get the current wizard page
+    gui.clickButton(buttons.NextButton)
+}
+
+Controller.prototype.TargetDirectoryPageCallback = function()
+{
+    var widget = gui.currentPageWidget();
+    widget.TargetDirectoryLineEdit.setText(install_dir);
+    gui.clickButton(buttons.NextButton);
+}
+
+Controller.prototype.ComponentSelectionPageCallback = function()
+{
+    var widget = gui.currentPageWidget();
+    widget.selectAll();
+    gui.clickButton(buttons.NextButton);
+}
+
+Controller.prototype.LicenseAgreementPageCallback = function()
+{
+    var widget = gui.currentPageWidget();
+    widget.AcceptLicenseRadioButton.setChecked(true);
+    gui.clickButton(buttons.NextButton);
+}
+
+Controller.prototype.ReadyForInstallationPageCallback = function()
+{
+    gui.clickButton(buttons.CommitButton);
+}
+
+Controller.prototype.PerformInstallationPageCallback = function()
+{
+    gui.clickButton(buttons.CommitButton);
+}
+
+Controller.prototype.FinishedPageCallback = function()
+{
+    gui.clickButton(buttons.FinishButton);
+}
EOF
        patch -f -N -i qtifw-${QTIFW_VERSION}.patch -p0

        xvfb-run ${__wine_cmd} ${__download_dir}/QtInstallerFramework-win-x86-${QTIFW_VERSION}.exe \
            --script ${__build_dir}/qtifw-${QTIFW_VERSION}/qt_installer_script

        pushd ${CROSSBUILD_INSTALL_PREFIX}
        rm -f qtifw && ln -fs qtifw-${QTIFW_VERSION} qtifw
        pushd bin;ln -fs ../qtifw/bin/*.* ./;popd

        popd
        popd
    fi
fi

# ------------------------------------------------------------------------------
# sip
# ------------------------------------------------------------------------------
PYTHON_SIP_VERSION=4.15.5
PYTHON_SIP_INSTALL_PREFIX=${PYTHON_INSTALL_PREFIX}
PYTHON_SIP_SOURCE_URL=https://sourceforge.net/projects/pyqt/files/sip/sip-${PYTHON_SIP_VERSION}/sip-${PYTHON_SIP_VERSION}.tar.gz
if [ "${PYTHON_SIP}" == "1" ]; then
    echo "================================= PYTHON_SIP ================================"
    if [ "${__download}" == "1" ]; then
        download ${PYTHON_SIP_SOURCE_URL}
    fi

    if [ "${__remove_before_install}" == "1"  ]; then
        \rm -f ${PYTHON_INSTALL_PREFIX}/include/sip.h
        \rm -f ${PYTHON_INSTALL_PREFIX}/sip.exe
        \rm -f ${PYTHON_INSTALL_PREFIX}/Lib/site-packages/sip*
    fi

    if [ "${__install}" == "1" ]; then
        tar xvf ${__download_dir}/sip-${PYTHON_SIP_VERSION}.tar.gz
        pushd ${__build_dir}/sip-${PYTHON_SIP_VERSION}

        cat << EOF > sip-${PYTHON_SIP_VERSION}.patch
diff -NurwB --strip-trailing-cr --suppress-common-lines specs/win32-g++ specs/win32-g++
--- specs/win32-g++	2016-09-12 15:20:27.299630733 +0200
+++ specs/win32-g++	2016-09-12 15:23:03.363576580 +0200
@@ -3,31 +3,39 @@
 #
 # Written for MinGW
 #
+# Cross compile example for i686-w64-mingw32-g++:
+#   configure -xplatform win32-g++ -device-option CROSS_COMPILE=i686-w64-mingw32-
+#
 
 MAKEFILE_GENERATOR	= MINGW
+
+load(device_config)
+
+equals(QMAKE_HOST.os, Windows): EXE_SUFFIX = .exe
+
 TEMPLATE		= app
 CONFIG			+= qt warn_on release link_prl copy_dir_files debug_and_release debug_and_release_target precompile_header
 QT			+= core gui
-DEFINES			+= UNICODE QT_LARGEFILE_SUPPORT
+DEFINES			+= UNICODE
 QMAKE_COMPILER_DEFINES  += __GNUC__ WIN32
 
 QMAKE_EXT_OBJ           = .o
+QMAKE_EXT_RES           = _res.o
 
-QMAKE_CC		= gcc
+QMAKE_CC		= \$\${CROSS_COMPILE}gcc
 QMAKE_LEX		= flex
 QMAKE_LEXFLAGS		=
 QMAKE_YACC		= byacc
 QMAKE_YACCFLAGS		= -d
-QMAKE_CFLAGS		=
+QMAKE_CFLAGS		= -pipe
 QMAKE_CFLAGS_DEPS	= -M
-QMAKE_CFLAGS_WARN_ON	= -Wall 
+QMAKE_CFLAGS_WARN_ON	= -Wall -Wextra
 QMAKE_CFLAGS_WARN_OFF	= -w
 QMAKE_CFLAGS_RELEASE	= -O2
 QMAKE_CFLAGS_DEBUG	= -g
 QMAKE_CFLAGS_YACC	= -Wno-unused -Wno-parentheses
-QMAKE_CFLAGS_THREAD	= -mthreads
 
-QMAKE_CXX		= g++
+QMAKE_CXX		= \$\${CROSS_COMPILE}g++
 QMAKE_CXXFLAGS		= \$\$QMAKE_CFLAGS
 QMAKE_CXXFLAGS_DEPS	= \$\$QMAKE_CFLAGS_DEPS
 QMAKE_CXXFLAGS_WARN_ON	= \$\$QMAKE_CFLAGS_WARN_ON
@@ -38,7 +46,7 @@
 QMAKE_CXXFLAGS_THREAD	= \$\$QMAKE_CFLAGS_THREAD
 QMAKE_CXXFLAGS_RTTI_ON	= -frtti
 QMAKE_CXXFLAGS_RTTI_OFF	= -fno-rtti
-QMAKE_CXXFLAGS_EXCEPTIONS_ON = -fexceptions
+QMAKE_CXXFLAGS_EXCEPTIONS_ON = -fexceptions -mthreads
 QMAKE_CXXFLAGS_EXCEPTIONS_OFF = -fno-exceptions
 
 QMAKE_INCDIR		=
@@ -50,8 +58,11 @@
 QMAKE_RUN_CXX		= \$(CXX) -c \$(CXXFLAGS) \$(INCPATH) -o \$obj \$src
 QMAKE_RUN_CXX_IMP	= \$(CXX) -c \$(CXXFLAGS) \$(INCPATH) -o \$@ \$<
 
-QMAKE_LINK		= g++
-QMAKE_LFLAGS		= -mthreads -Wl,-enable-stdcall-fixup -Wl,-enable-auto-import -Wl,-enable-runtime-pseudo-reloc
+QMAKE_LINK		= \$\${CROSS_COMPILE}g++
+QMAKE_LINK_C		= \$\${CROSS_COMPILE}gcc
+QMAKE_LFLAGS		=
+QMAKE_LFLAGS_EXCEPTIONS_ON = -mthreads
+QMAKE_LFLAGS_EXCEPTIONS_OFF =
 QMAKE_LFLAGS_RELEASE	= -Wl,-s
 QMAKE_LFLAGS_DEBUG	=
 QMAKE_LFLAGS_CONSOLE	= -Wl,-subsystem,console
@@ -59,44 +70,39 @@
 QMAKE_LFLAGS_DLL        = -shared
 QMAKE_LINK_OBJECT_MAX	= 10
 QMAKE_LINK_OBJECT_SCRIPT= object_script
+QMAKE_PREFIX_STATICLIB  = lib
+QMAKE_EXTENSION_STATICLIB = a
 
 
 QMAKE_LIBS		=
-QMAKE_LIBS_CORE         = -lkernel32 -luser32 -lshell32 -luuid -lole32 -ladvapi32 -lws2_32
-QMAKE_LIBS_GUI          = -lgdi32 -lcomdlg32 -loleaut32 -limm32 -lwinmm -lwinspool -lws2_32 -lole32 -luuid -luser32
+QMAKE_LIBS_CORE         = -lole32 -luuid -lws2_32 -ladvapi32 -lshell32 -luser32 -lkernel32
+QMAKE_LIBS_GUI          = -lgdi32 -lcomdlg32 -loleaut32 -limm32 -lwinmm -lwinspool -lws2_32 -lole32 -luuid -luser32 -ladvapi32
 QMAKE_LIBS_NETWORK      = -lws2_32
-QMAKE_LIBS_OPENGL       = -lopengl32 -lglu32 -lgdi32 -luser32
+QMAKE_LIBS_OPENGL       = -lglu32 -lopengl32 -lgdi32 -luser32
 QMAKE_LIBS_COMPAT       = -ladvapi32 -lshell32 -lcomdlg32 -luser32 -lgdi32 -lws2_32
 QMAKE_LIBS_QT_ENTRY     = -lmingw32 -lqtmain
 
-MINGW_IN_SHELL = \$\$(MINGW_IN_SHELL)
-isEqual(MINGW_IN_SHELL, 1) {
+MINGW_IN_SHELL      = 1
 	QMAKE_DIR_SEP		= /
-	QMAKE_COPY		= cp
-	QMAKE_COPY_DIR		= xcopy /s /q /y /i
+QMAKE_QMAKE		~= s,\\\\\\\\,/,
+QMAKE_COPY		= cp -f
+QMAKE_COPY_DIR		= cp -rf
 	QMAKE_MOVE		= mv
-	QMAKE_DEL_FILE		= rm
-	QMAKE_MKDIR		= mkdir
+QMAKE_DEL_FILE		= rm -f
+QMAKE_MKDIR		= mkdir -p
 	QMAKE_DEL_DIR		= rmdir
-} else {
-	QMAKE_COPY		= copy /y
-	QMAKE_COPY_DIR		= xcopy /s /q /y /i
-	QMAKE_MOVE		= move
-	QMAKE_DEL_FILE		= del
-	QMAKE_MKDIR		= mkdir
-	QMAKE_DEL_DIR		= rmdir
-}
-QMAKE_MOC		= \$\$[QT_INSTALL_BINS]\$\${DIR_SEPARATOR}moc.exe
-QMAKE_UIC		= \$\$[QT_INSTALL_BINS]\$\${DIR_SEPARATOR}uic.exe
-QMAKE_IDC		= \$\$[QT_INSTALL_BINS]\$\${DIR_SEPARATOR}idc.exe
+QMAKE_CHK_DIR_EXISTS = test -d
 
-QMAKE_IDL		= midl
-QMAKE_LIB		= ar -ru
-QMAKE_RC		= windres
+QMAKE_MOC		= ${__wine_cmd} \$\$[QT_INSTALL_BINS]\$\${DIR_SEPARATOR}moc\$\${EXE_SUFFIX}
+QMAKE_UIC		= ${__wine_cmd} \$\$[QT_INSTALL_BINS]\$\${DIR_SEPARATOR}uic\$\${EXE_SUFFIX}
+QMAKE_IDC		= ${__wine_cmd} \$\$[QT_INSTALL_BINS]\$\${DIR_SEPARATOR}idc\$\${EXE_SUFFIX}
+QMAKE_RCC		= ${__wine_cmd} \$\$[QT_INSTALL_BINS]\$\${DIR_SEPARATOR}rcc\$\${EXE_SUFFIX}
 
+QMAKE_IDL		= midl
+QMAKE_LIB		= \$\${CROSS_COMPILE}ar -ru
+QMAKE_RC		= \$\${CROSS_COMPILE}windres
 QMAKE_ZIP		= zip -r -9
 
-QMAKE_STRIP		= strip
+QMAKE_STRIP		= \$\${CROSS_COMPILE}strip
 QMAKE_STRIPFLAGS_LIB 	+= --strip-unneeded
-QMAKE_CHK_DIR_EXISTS	= if not exist
 load(qt_config)
diff -NurwB --strip-trailing-cr --suppress-common-lines siputils.py siputils.py
--- siputils.py	2016-09-12 15:20:53.359621706 +0200
+++ siputils.py	2016-09-12 15:26:37.515501912 +0200
@@ -91,6 +90,11 @@
         """
         self._macros = macros
 
+    def target_platform(self):
+        return self.platform.strip().split('-', 1)[0]
+    
+    def build_platform(self):
+        return sys.platform
 
 class _UniqueList:
     """A limited list that ensures all its elements are unique.
@@ -321,7 +325,7 @@
         self.extra_libs = []
 
         # Get these once and make them available to sub-classes.
-        if sys.platform == "win32":
+        if configuration.build_platform() == "win32":
             def_copy = "copy"
             def_rm = "del"
             def_mkdir = "mkdir"
@@ -440,12 +444,12 @@
             incdir.append(self.config.py_inc_dir)
             incdir.append(self.config.py_conf_inc_dir)
 
-            if sys.platform == "cygwin":
+            if self.config.build_platform() == "cygwin":
                 libdir.append(self.config.py_lib_dir)
 
                 py_lib = "python%u.%u" % ((self.config.py_version >> 16), ((self.config.py_version >> 8) & 0xff))
                 libs.append(self.platform_lib(py_lib))
-            elif sys.platform == "win32":
+            elif self.config.build_platform() == "win32":
                 libdir.append(self.config.py_lib_dir)
 
                 py_lib = "python%u%u" % ((self.config.py_version >> 16), ((self.config.py_version >> 8) & 0xff))
@@ -696,7 +700,7 @@
                     lib = self._qt_module_to_lib(mod)
                     libs.append(self.platform_lib(lib, self._is_framework(mod)))
 
-                    if sys.platform == "win32":
+                    if self.config.build_platform() == "win32":
                         # On Windows the dependent libraries seem to be in
                         # qmake.conf rather than the .prl file and the
                         # inter-dependencies between Qt libraries don't seem to
@@ -854,7 +858,7 @@
         lib += self._infix
 
         if self._debug:
-            if sys.platform == "win32":
+            if self.config.build_platform() == "win32":
                 lib = lib + "d"
             elif sys.platform == "darwin":
                 if not self._is_framework(mname):
@@ -864,7 +868,7 @@
 
         qt5_rename = False
 
-        if sys.platform == "win32" and "shared" in self.config.qt_winconfig.split():
+        if self.config.target_platform() == "win32" and "shared" in self.config.qt_winconfig.split():
             if (mname in ("QtCore", "QtDeclarative", "QtDesigner", "QtGui",
                           "QtHelp", "QtMultimedia", "QtNetwork", "QtOpenGL",
                           "QtScript", "QtScriptTools", "QtSql", "QtSvg",
@@ -879,7 +883,7 @@
                     qt5_rename = True
                 else:
                     lib = lib + "4"
-        elif sys.platform.startswith("linux") and qt_version >= 0x050000:
+        elif self.config.target_platform().startswith("linux") and qt_version >= 0x050000:
             qt5_rename = True
 
         if qt5_rename:
@@ -1188,6 +1192,7 @@
 
         libs.extend(self.optional_list("LIBS"))
 
+        mfile.write("CROSS_COMPILE = %s\\n" % self.optional_string("CROSS_COMPILE"))
         mfile.write("CPPFLAGS = %s\\n" % ' '.join(cppflags))
 
         mfile.write("CFLAGS = %s\\n" % self.optional_string("CFLAGS"))
@@ -1303,12 +1308,12 @@
         strip is set if the files should be stripped after been installed.
         """
         # Help package builders.
-        if self.generator == "UNIX":
+        if self.generator == "UNIX" or self.config.build_platform().startswith("linux"):
             dst = "\$(DESTDIR)" + dst
 
         mfile.write("\\t@%s %s " % (self.chkdir, _quote(dst)))
 
-        if self.generator == "UNIX":
+        if self.generator == "UNIX" or self.config.build_platform().startswith("linux"):
             mfile.write("|| ")
 
         mfile.write("%s %s\\n" % (self.mkdir, _quote(dst)))
@@ -1505,10 +1511,10 @@
         else:
             self._entry_point = "init%s" % self._target
 
-        if sys.platform != "win32" and static:
+        if self.config.target_platform() != "win32" and static:
             self._target = "lib" + self._target
 
-        if sys.platform == "win32" and debug:
+        if self.config.target_platform() == "win32" and debug:
             self._target = self._target + "_d"
 
     def finalise(self):
@@ -1625,16 +1631,16 @@
         mfile is the file object.
         """
         if self.static:
-            if sys.platform == "win32":
+            if self.config.target_platform() == "win32":
                 ext = "lib"
             else:
                 ext = "a"
         else:
-            if sys.platform == "win32":
+            if self.config.target_platform() == "win32":
                 ext = "pyd"
-            elif sys.platform == "darwin":
+            elif self.config.target_platform() == "darwin":
                 ext = "so"
-            elif sys.platform == "cygwin":
+            elif self.config.target_platform() == "cygwin":
                 ext = "dll"
             else:
                 ext = self.optional_string("EXTENSION_PLUGIN")
@@ -1838,10 +1844,10 @@
         # The name of the executable.
         self._target, _ = os.path.splitext(source)
 
-        if sys.platform in ("win32", "cygwin"):
+        if self.config.target_platform() in ("win32", "cygwin"):
             exe = self._target + ".exe"
         else:
-            exe = self._target
+            exe = self._target + self.optional_string("EXE_SUFFIX")
 
         self.ready()
 
@@ -1946,8 +1952,10 @@
 
         target = self._build["target"]
 
-        if sys.platform in ("win32", "cygwin"):
+        if self.config.target_platform() in ("win32", "cygwin"):
             target = target + ".exe"
+        else:
+            target = target + self.optional_string("EXE_SUFFIX")
 
         mfile.write("TARGET = %s\\n" % target)
         mfile.write("OFILES = %s\\n" % self._build["objects"])
@@ -2632,12 +2639,19 @@
 
     Returns the platform specific name of the wrapper.
     """
-    if sys.platform == "win32":
+    sipcfg = Configuration()
+    if "win32" in (sys.platform, sipcfg.target_platform()):
         wrapper = wrapper + ".bat"
 
     wf = open(wrapper, "w")
 
-    if sys.platform == "win32":
+    if "win32" in (sys.platform, sipcfg.target_platform()):
+        if sys.platform != sipcfg.target_platform():
+            # We are cross compiling so we do not know the location of the 
+            # target python executable
+            exe = "python.exe"
+            
+        else:
-        exe = sys.executable
+            exe = sys.executable
 
         if gui:
diff -NurwB --strip-trailing-cr --suppress-common-lines configure.py configure.py
--- configure.py	2016-09-12 15:20:39.639626460 +0200
+++ configure.py	2016-09-12 15:21:42.355604717 +0200
@@ -53,6 +53,10 @@
 default_sipmoddir = None
 default_sipincdir = None
 default_sipsipdir = None
+default_pyversion = None
+default_pyincdir = None
+default_pyconfincdir = None
+default_pylibdir = None
 
 # The names of build macros extracted from the platform specific configuration
 # files.
@@ -77,7 +81,9 @@
     "CXXFLAGS_RTTI_ON", "CXXFLAGS_RTTI_OFF",
     "CXXFLAGS_STL_ON", "CXXFLAGS_STL_OFF",
     "CXXFLAGS_WARN_ON", "CXXFLAGS_WARN_OFF",
+    "CROSS_COMPILE",
     "DEL_FILE",
+    "EXE_SUFFIX",
     "EXTENSION_SHLIB", "EXTENSION_PLUGIN",
     "INCDIR", "INCDIR_X11", "INCDIR_OPENGL",
     "LIBS_CORE", "LIBS_GUI", "LIBS_NETWORK", "LIBS_OPENGL", "LIBS_WEBKIT",
@@ -127,6 +133,8 @@
     """
     global default_platform, default_sipbindir, default_sipmoddir
     global default_sipincdir, default_sipsipdir
+    global default_pyversion, default_pyincdir, default_pyconfincdir, \\
+           default_pylibdir
 
     # Set the platform specific default specification.
     platdefaults = {
@@ -176,7 +184,10 @@
     default_sipmoddir = plat_py_site_dir
     default_sipincdir = plat_py_inc_dir
     default_sipsipdir = plat_sip_dir
-
+    default_pyversion = py_version
+    default_pyincdir  = plat_py_inc_dir
+    default_pyconfincdir  = plat_py_conf_inc_dir
+    default_pylibdir  = plat_py_lib_dir
 
 def inform_user():
     """Tell the user the option values that are going to be used.
@@ -266,21 +277,26 @@
     """
     siputils.inform("Creating %s..." % module)
 
+    if opts.platform.startswith('win32'):
+        exe_suffix = '.exe'
+    else:
+        exe_suffix = ''
+
     content = {
         "sip_config_args":  sys.argv[1:],
         "sip_version":      sip_version,
         "sip_version_str":  sip_version_str,
         "platform":         opts.platform,
-        "sip_bin":          os.path.join(opts.sipbindir, "sip"),
+        "sip_bin":          os.path.join(opts.sipbindir, "sip" + exe_suffix),
         "sip_inc_dir":      opts.sipincdir,
         "sip_mod_dir":      opts.sipmoddir,
         "default_bin_dir":  plat_bin_dir,
         "default_mod_dir":  plat_py_site_dir,
         "default_sip_dir":  opts.sipsipdir,
-        "py_version":       py_version,
-        "py_inc_dir":       plat_py_inc_dir,
-        "py_conf_inc_dir":  plat_py_conf_inc_dir,
-        "py_lib_dir":       plat_py_lib_dir,
+        "py_version":       opts.pyversion,
+        "py_inc_dir":       opts.pyincdir,
+        "py_conf_inc_dir":  opts.pyconfincdir,
+        "py_lib_dir":       opts.pylibdir,
         "universal":        opts.universal,
         "arch":             opts.arch,
         "deployment_target":    opts.deployment_target,
@@ -353,6 +364,9 @@
     def store_abspath(option, opt_str, value, parser):
         setattr(parser.values, option.dest, os.path.abspath(value))
 
+    def store_version(option, opt_str, value, parser):
+        setattr(parser.values, option.dest, int(value, 16))
+        
     p = optparse.OptionParser(usage="python %prog [opts] [macro=value] "
             "[macro+=value]", version=sip_version_str)
 
@@ -396,6 +410,32 @@
                         "binaries [default: %s]" % default_sdk)
         p.add_option_group(g)
 
+    # Python.
+    g = optparse.OptionGroup(p, title="Python")
+    #g.add_option("--pybindir", action="callback",
+    #        default=default_pybindir, type="string", metavar="DIR",
+    #        dest="--pybindir", callback=store_abspath, help="where the PYTHON "
+    #        "interpreter can be found [default: %s]" %
+    #        default_pybindir)
+    g.add_option("--pyversion", action="callback",
+            default=default_pyversion, type="string", metavar="DIR",
+            dest="pyversion", callback=store_version, help="target PYTHON "
+            "version [default: %s]" % hex(py_version))
+    g.add_option("--pylibdir", action="callback",
+            default=default_pylibdir, type="string", metavar="DIR",
+            dest="pylibdir", callback=store_abspath, help="where the PYTHON "
+            "library can be found [default: %s]" % default_pylibdir)
+    g.add_option("--pyincdir", action="callback",
+            default=default_pyincdir, type="string", metavar="DIR",
+            dest="pyincdir", callback=store_abspath, help="where PYTHON "
+            "headers can be found [default: %s]" % default_pyincdir)
+    g.add_option("--pyconfincdir", action="callback",
+            default=default_pyconfincdir, type="string", metavar="DIR",
+            dest="pyconfincdir", callback=store_abspath, help="where PYTHON "
+            "configuration headers can be found [default: %s]" 
+            % default_pyconfincdir)
+    p.add_option_group(g)
+
     # Querying.
     g = optparse.OptionGroup(p, title="Query")
     g.add_option("--show-platforms", action="store_true", default=False,

EOF
        patch -f -N -i sip-${PYTHON_SIP_VERSION}.patch -p0

        ${PYTHON_HOST_COMMAND} configure.py \
                    -p win32-g++ \
                    -b ${PYTHON_INSTALL_PREFIX} \
                    -d ${PYTHON_INSTALL_PREFIX}/Lib/site-packages \
                    -e ${PYTHON_INSTALL_PREFIX}/include \
                    -v ${PYTHON_INSTALL_PREFIX}/sip \
                    --pyversion "${PYTHON_VERSION_HEX}" \
                    --pyincdir ${PYTHON_INSTALL_PREFIX}/include \
                    --pyconfincdir ${PYTHON_INSTALL_PREFIX}/include \
                    --pylibdir ${PYTHON_INSTALL_PREFIX}/DLLs \
                    CROSS_COMPILE=${__toolchain}- \
                    CC=$CC \
                    CFLAGS="$CFLAGS $PYTHON_CFLAGS" \
                    CXX=$CXX \
                    CXXFLAGS="$CPPFLAGS $PYTHON_CPPFLAGS" \
                    AR=$AR \
                    LINK=$CXX \
                    LFLAGS="${PYTHON_LDFLAGS}" \
                    LIB=$AR \
                    EXTENSION_SHLIB="pyd" \
                    EXE_SUFFIX=".exe" \
        || exit 1

        make -j${__build_proc_num} install || exit 1
        pushd ${CROSSBUILD_INSTALL_PREFIX}
        pushd bin;ln -fs ../python/sip.exe ./;popd
        pushd include;ln -fs ../python/include/sip.h ./;popd
        popd
        popd
    fi
fi

PYTHON_PYQT_VERSION=4.10.4
PYTHON_PYQT_INSTALL_PREFIX=${CROSSBUILD_INSTALL_PREFIX}/pyqt-${PYTHON_PYQT_VERSION}
PYTHON_PYQT_SOURCE_URL=http://sourceforge.mirrorservice.org/p/py/pyqt/PyQt4/PyQt-${PYTHON_PYQT_VERSION}/PyQt-x11-gpl-${PYTHON_PYQT_VERSION}.tar.gz

if [ "${PYTHON_PYQT}" == "1" ]; then
    echo "================================ PYTHON_PYQT ================================"
    if [ "${__download}" == "1" ]; then
        download ${PYTHON_PYQT_SOURCE_URL}
    fi

    if [ "${__remove_before_install}" == "1"  ]; then
        \rm -f ${PYTHON_INSTALL_PREFIX}/pylupdate4.exe \
               ${PYTHON_INSTALL_PREFIX}/pyrcc4.exe \
               ${PYTHON_INSTALL_PREFIX}/pyuic4.exe
        \rm -rf ${PYTHON_INSTALL_PREFIX}/Lib/site-packages/PyQt4
        \rm -rf ${PYTHON_INSTALL_PREFIX}/sip/phonon \
                ${PYTHON_INSTALL_PREFIX}/sip/Qt*
    fi

    if [ "${__install}" == "1" ]; then
        tar xvf ${__download_dir}/PyQt-x11-gpl-${PYTHON_PYQT_VERSION}.tar.gz
        pushd ${__build_dir}/PyQt-x11-gpl-${PYTHON_PYQT_VERSION}

        cat << EOF > pyqt-${PYTHON_PYQT_VERSION}.patch
diff -NurwB --strip-trailing-cr --suppress-common-lines configure.py configure.py
--- configure.py	2017-07-24 08:57:30.000000000 +0000
+++ configure.py	2017-07-24 08:56:48.000000000 +0000
@@ -70,6 +70,10 @@
 dbuslibdirs = []
 dbuslibs = []
 
+# Command prefix can be used to run target os (wine for instance)
+# in cross compilation cases
+cmd_prefix = os.environ.get('COMMAND_PREFIX')
+
 
 # Under Windows qmake and the Qt DLLs must be on the system PATH otherwise the
 # dynamic linker won't be able to resolve the symbols.  On other systems we
@@ -662,7 +666,7 @@
         """
         qpy_dir = os.path.join("qpy", mname)
 
-        if sys.platform == 'win32':
+        if 'win32' in (sys.platform, target_platform):
             if opts.debug:
                 qpy_lib_dir = os.path.join(qpy_dir, "debug")
             else:
@@ -957,7 +961,7 @@
 
             abi = getattr(sys, 'abiflags', '')
 
-            if sys.platform == 'win32':
+            if 'win32' in (sys.platform, target_platform):
                 # Use abiflags in case it is supported in a future version.
                 lib_dir_flag = quote("-L%s" % sipcfg.py_lib_dir)
                 link = "%s -lpython%d%d%s" % (lib_dir_flag, py_major, py_minor, abi)
@@ -1511,7 +1515,7 @@
         sip_flags.append("PyQt_Deprecated_5_0")
 
     # Handle the platform tag.
-    if sys.platform == 'win32':
+    if 'win32' in (sys.platform, target_platform):
         plattag = "WS_WIN"
     elif sys.platform == "darwin":
         if "__USE_WS_X11__" in sipcfg.build_macros()["DEFINES"]:
@@ -1530,7 +1534,7 @@
     # Handle any feature flags.
     for xf in qt_xfeatures:
         sip_flags.append("-x")
-        sip_flags.append(xf)
+        sip_flags.append(xf.strip())
 
     if verstag:
         sip_flags.append("-t")
@@ -1656,6 +1660,8 @@
 
     # Build the SIP command line.
     argv = ['"' + sipcfg.sip_bin + '"', '-w']
+    if cmd_prefix:
+        argv = [cmd_prefix] + argv
 
     if opts.no_timestamp:
         argv.append("-T")
@@ -2024,7 +2030,7 @@
     out_file = app + ".out"
     qmake_args = fix_qmake_args("-o " + make_file)
 
-    if sys.platform == 'win32':
+    if 'win32' in (sys.platform, target_platform):
         if opts.debug:
             exe_file = os.path.join("debug", app + ".exe")
             make_target = " debug"
@@ -2187,7 +2193,7 @@
         make = "nmake"
     elif sipcfg.platform == "win32-borland":
         make = "bmake"
-    elif sipcfg.platform == "win32-g++":
+    elif sipcfg.platform == "win32-g++" and not sys.platform.startswith('linux'):
         make = "mingw32-make"
     else:
         make = "make"
@@ -2201,7 +2207,10 @@
 
     # Create the output file, first making sure it doesn't exist.
     remove_file(out_file)
-    run_command(exe_file)
+    cmd = [exe_file]
+    if cmd_prefix:
+        cmd = [cmd_prefix] + cmd
+    run_command(' '.join(cmd))
 
     if not os.access(out_file, os.F_OK):
         sipconfig.error("%s failed to create %s. Make sure your Qt installation is correct." % (exe_file, out_file))
@@ -2215,24 +2224,24 @@
     global qt_pluginsdir
     global qt_version, qt_edition, qt_licensee, qt_shared, qt_xfeatures
 
-    qt_dir = lines[0]
-    qt_incdir = lines[1]
-    qt_libdir = lines[2]
-    qt_bindir = lines[3]
-    qt_datadir = lines[4]
-    qt_archdatadir = lines[5]
-    qt_pluginsdir = lines[6]
-    qt_version = lines[7]
-    qt_edition = lines[8]
-    qt_licensee = lines[9]
-    qt_shared = lines[10]
-    qt_xfeatures = lines[11:]
+    qt_dir = lines[0].strip()
+    qt_incdir = lines[1].strip()
+    qt_libdir = lines[2].strip()
+    qt_bindir = lines[3].strip()
+    qt_datadir = lines[4].strip()
+    qt_archdatadir = lines[5].strip()
+    qt_pluginsdir = lines[6].strip()
+    qt_version = lines[7].strip()
+    qt_edition = lines[8].strip()
+    qt_licensee = lines[9].strip()
+    qt_shared = lines[10].strip()
+    qt_xfeatures = [l.strip() for l in lines[11:]]
 
     if opts.assume_shared:
         qt_shared = "shared"
 
     # 'Nokia' is the value that is used by Maemo's version of Qt.
-    if qt_licensee in ('Open Source', 'Nokia'):
+    if qt_licensee.strip() in ('Open Source', 'Nokia'):
         qt_licensee = None
 
     try:
@@ -2281,12 +2290,15 @@
     if sipcfg.sip_version < sip_min_version:
         sipconfig.error("This version of PyQt requires SIP v%s or later" % sipconfig.version_to_string(sip_min_version))
 
-    global opts
+    global opts, target_platform
 
     # Parse the command line.
     p = create_optparser()
     opts, args = p.parse_args()
 
+    if 'win32' in os.environ.get('QMAKESPEC', ''):
+        target_platform = 'win32'
+
     # Provide defaults for platform-specific options.
     if sys.platform == 'win32':
         opts.qmake = find_default_qmake()
EOF
        patch -f -N -i pyqt-${PYTHON_PYQT_VERSION}.patch -p0

        export PYTHONPATH="${PYTHON_INSTALL_PREFIX}/Lib/site-packages:${PYTHONPATH}"
        export QTDIR=${QT_INSTALL_PREFIX}
        export QMAKESPEC=${QT_INSTALL_PREFIX}/mkspecs/win32-g++
        COMMAND_PREFIX=${__wine_cmd} \
        ${PYTHON_HOST_COMMAND} configure.py \
                    --confirm-license \
                    -b ${PYTHON_INSTALL_PREFIX} \
                    -d ${PYTHON_INSTALL_PREFIX}/Lib/site-packages \
                    -v ${PYTHON_INSTALL_PREFIX}/sip \
                    -q ${QT_INSTALL_PREFIX}/bin/qmake \
                    --verbose \
                    CC=$CC \
                    CFLAGS="$CFLAGS $PYTHON_CFLAGS -DQT_SHAREDMEMORY -DQT_SYSTEMSEMAPHORE" \
                    CXX=$CXX \
                    CXXFLAGS="$CPPFLAGS $PYTHON_CPPFLAGS -DQT_SHAREDMEMORY -DQT_SYSTEMSEMAPHORE" \
                    AR=$AR \
                    LINK=$CXX \
                    LFLAGS="${PYTHON_LDFLAGS}" \
                    LIB=$AR \
                    EXTENSION_SHLIB="pyd" \
                    CROSS_COMPILE="${__toolchain}-" \
        || exit 1
        
        # First we need to build qpy, because dependencies
        # are not set between sip modules and qpy modules
        # doing so allows us to use multiple processors
        make -j${__build_proc_num} -C qpy || exit 1
        make -j${__build_proc_num} install || exit 1
        pushd ${CROSSBUILD_INSTALL_PREFIX}
        pushd bin;ln -fs ../python/pylupdate4.exe \
                         ../python/pyrcc4.exe \
                         ../python/pyuic4.exe \
                         ./;popd
        popd
        popd
    fi
fi

PYTHON_LFD_UCI_REPO_ID=g7ckv9dk

PYTHON_PIP_VERSION=8.1.2
PYTHON_PIP_INSTALL_SCRIPT_SOURCE_URL=https://bootstrap.pypa.io/get-pip.py
PYTHON_PIP_SOURCE_URL=http://www.lfd.uci.edu/~gohlke/pythonlibs/${PYTHON_LFD_UCI_REPO_ID}/pip-${PYTHON_PIP_VERSION}-py2.py3-none-any.whl
PYTHON_WHEEL_VERSION=0.29.0
PYTHON_WHEEL_SOURCE_URL=http://www.lfd.uci.edu/~gohlke/pythonlibs/${PYTHON_LFD_UCI_REPO_ID}/wheel-${PYTHON_WHEEL_VERSION}-py2.py3-none-any.whl
if [ "${PYTHON_PIP}" == "1" ] || [  "${PYTHON_WHEEL}" == "1" ] ; then
    echo "================================ PYTHON_PIP ================================"
    if [ "${__download}" == "1" ]; then
        download ${PYTHON_PIP_INSTALL_SCRIPT_SOURCE_URL}
        download ${PYTHON_PIP_SOURCE_URL}
        download ${PYTHON_WHEEL_SOURCE_URL}
    fi

    if [ "${__remove_before_install}" == "1"  ]; then
        if [ "$(${__wine_cmd} ${PYTHON_INSTALL_PREFIX}/python.exe \
                -c "import pip" 2>/dev/null;echo $?)" == "0" ]; then
            # Uninstall using target python
            PYTHONHOME=${PYTHON_INSTALL_PREFIX} \
            ${__wine_cmd} ${PYTHON_INSTALL_PREFIX}/python.exe \
                                        -m pip uninstall -y pip wheel
        fi
    fi

    if [ "${__install}" == "1" ]; then
        PYTHONHOME=${PYTHON_INSTALL_PREFIX} \
        ${__wine_cmd} ${PYTHON_INSTALL_PREFIX}/python.exe \
                    ${__download_dir}/get-pip.py \
                    ${__download_dir}/pip-${PYTHON_PIP_VERSION}-py2.py3-none-any.whl \
                    ${__download_dir}/wheel-${PYTHON_WHEEL_VERSION}-py2.py3-none-any.whl \
        || exit 1

        # Add links to python scripts
        pushd ${CROSSBUILD_INSTALL_PREFIX}/bin
        ln -fs ../python/Scripts/wheel.exe \
               ../python/Scripts/pip.exe \
               ../python/Scripts/pip2.exe \
               ../python/Scripts/pip2.7.exe \
               ./
        popd
    fi

    if [ "${__fix_python_scripts}" == "1" ]; then
        for __script in wheel.exe pip.exe pip2.exe pip2.7.exe; do
            fix_python_script ${PYTHON_INSTALL_PREFIX}/Scripts/${__script}
        done
    fi
fi

PYTHON_SIX_VERSION=1.10.0
PYTHON_SIX_SOURCE_URL=https://pypi.python.org/packages/c8/0a/b6723e1bc4c516cb687841499455a8505b44607ab535be01091c0f24f079/six-${PYTHON_SIX_VERSION}-py2.py3-none-any.whl
if [ "${PYTHON_SIX}" == "1" ]; then
    echo "================================ PYTHON_SIX ================================"
    if [ "${__download}" == "1" ]; then
        download ${PYTHON_SIX_SOURCE_URL}
    fi

    if [ "${__remove_before_install}" == "1"  ]; then
        # Uninstall using target python
        PYTHONHOME=${PYTHON_INSTALL_PREFIX} \
        ${__wine_cmd} ${PYTHON_INSTALL_PREFIX}/python.exe \
                                    -m pip uninstall -y six
    fi

    if [ "${__install}" == "1" ]; then
        PYTHONHOME=${PYTHON_INSTALL_PREFIX} \
        ${__wine_cmd} ${PYTHON_INSTALL_PREFIX}/python.exe \
                    -m pip install ${__download_dir}/six-${PYTHON_SIX_VERSION}-py2.py3-none-any.whl \
        || exit 1
    fi
fi

PYTHON_NUMPY_VERSION=1.11.3
PYTHON_NUMPY_SOURCE_URL=http://www.lfd.uci.edu/~gohlke/pythonlibs/${PYTHON_LFD_UCI_REPO_ID}/numpy-${PYTHON_NUMPY_VERSION}+mkl-cp27-cp27m-${PYTHON_WIN_ARCH_SUFFIX}.whl
if [ "${PYTHON_NUMPY}" == "1" ]; then
    echo "================================ PYTHON_NUMPY ================================"
    if [ "${__download}" == "1" ]; then
        download "${__arch}" ${PYTHON_NUMPY_SOURCE_URL}
    fi

    if [ "${__remove_before_install}" == "1"  ]; then
        # Uninstall using target python
        PYTHONHOME=${PYTHON_INSTALL_PREFIX} \
        ${__wine_cmd} ${PYTHON_INSTALL_PREFIX}/python.exe \
                                    -m pip uninstall -y numpy
    fi

    if [ "${__install}" == "1" ]; then
        PYTHONHOME=${PYTHON_INSTALL_PREFIX} \
        ${__wine_cmd} ${PYTHON_INSTALL_PREFIX}/python.exe \
                    -m pip install ${__download_dir}/numpy-${PYTHON_NUMPY_VERSION}+mkl-cp27-cp27m-${PYTHON_WIN_ARCH_SUFFIX}.whl \
        || exit 1

        # Add links to python scripts
        pushd ${CROSSBUILD_INSTALL_PREFIX}/bin
        ln -fs ../python/Scripts/f2py.py \
               ./
        popd
    fi

    if [ "${__fix_python_scripts}" == "1" ]; then
        for __script in f2py.py; do
            fix_python_script ${PYTHON_INSTALL_PREFIX}/Scripts/${__script}
        done
    fi
fi

PYTHON_SCIPY_VERSION=0.19.1
PYTHON_SCIPY_SOURCE_URL=http://www.lfd.uci.edu/~gohlke/pythonlibs/${PYTHON_LFD_UCI_REPO_ID}/scipy-${PYTHON_SCIPY_VERSION}-cp27-cp27m-${PYTHON_WIN_ARCH_SUFFIX}.whl
if [ "${PYTHON_SCIPY}" == "1" ]; then
    echo "================================ PYTHON_SCIPY ================================"
    if [ "${__download}" == "1" ]; then
        download "${__arch}" ${PYTHON_SCIPY_SOURCE_URL}
    fi

    if [ "${__remove_before_install}" == "1"  ]; then
        # Uninstall using target python
        PYTHONHOME=${PYTHON_INSTALL_PREFIX} \
        ${__wine_cmd} ${PYTHON_INSTALL_PREFIX}/python.exe \
                                    -m pip uninstall -y scipy
    fi

    if [ "${__install}" == "1" ]; then
        PYTHONHOME=${PYTHON_INSTALL_PREFIX} \
        ${__wine_cmd} ${PYTHON_INSTALL_PREFIX}/python.exe \
                    -m pip install ${__download_dir}/scipy-${PYTHON_SCIPY_VERSION}-cp27-cp27m-${PYTHON_WIN_ARCH_SUFFIX}.whl \
        || exit 1
    fi
fi

# ------------------------------------------------------------------------------
# traits
# ------------------------------------------------------------------------------
PYTHON_TRAITS_VERSION=4.1.0
PYTHON_TRAITS_SOURCE_URL=https://github.com/enthought/traits/archive/${PYTHON_TRAITS_VERSION}.tar.gz

if [ "${PYTHON_TRAITS}" == "1" ]; then
    echo "============================ PYTHON_TRAITS ==========================="
    if [ "${__download}" == "1" ]; then
        if [ "$__use_cea_mirror" = "1" ]; then
            # It was necessary to rename the original file because its name did
            # not contain anything to know that it provides traits. It is
            # necessary to have particular case where cea mirror file name 
            # is not the same as original file name.
            download "${__mirror_url}/sources/traits-${PYTHON_TRAITS_VERSION}.tar.gz"
        else
            download ${PYTHON_TRAITS_SOURCE_URL} traits-${PYTHON_TRAITS_VERSION}.tar.gz
        fi
    fi

    if [ "${__remove_before_install}" == "1"  ]; then
        # Uninstall using target python
        PYTHONHOME=${PYTHON_INSTALL_PREFIX} \
        ${__wine_cmd} ${PYTHON_INSTALL_PREFIX}/python.exe \
                                    -m pip uninstall -y traits
    fi

    if [ "${__install}" == "1" ]; then
        tar xvf ${__download_dir}/traits-${PYTHON_TRAITS_VERSION}.tar.gz
        pushd ${__build_dir}/traits-${PYTHON_TRAITS_VERSION}

        # Generate patch to build shared library
        cat << EOF > traits-${PYTHON_TRAITS_VERSION}.patch
diff -NurB --strip-trailing-cr --suppress-common-lines setup.py setup.py
--- setup.py    2016-10-30 00:57:32.946567170 +0200
+++ setup.py    2016-10-30 01:11:05.733426423 +0200
@@ -3,7 +3,24 @@
 
 from os.path import join
 from setuptools import setup, Extension, find_packages
+try:
+    from wheel import pep425tags
+except ImportError:
+    pass
+else:
+    pep425tags.get_abi_tag = lambda: 'none'
 
+from distutils import sysconfig
+def _init_posix():
+    """Initialize the module as appropriate for POSIX systems."""
+    # _sysconfigdata is generated at build time, see the sysconfig module
+    from _sysconfigdata import build_time_vars
+    sysconfig._config_vars = {}
+    sysconfig._config_vars.update(build_time_vars)
+    sysconfig._config_vars['SO'] = '.pyd'
+    sysconfig._config_vars['EXE'] = '.exe'
+
+sysconfig._init_posix = _init_posix
 
 d = {}
 execfile(join('traits', '__init__.py'), d)

EOF
        patch -f -N -i traits-${PYTHON_TRAITS_VERSION}.patch -p0 

        PYTHONXCPREFIX=${PYTHON_INSTALL_PREFIX} \
        CROSS_COMPILE="${__toolchain}-" \
        CPPFLAGS="${CPPFLAGS} ${PYTHON_CPPFLAGS}" \
        CFLAGS="${CFLAGS} ${PYTHON_CFLAGS}" \
        LDFLAGS="${LDFLAGS} ${PYTHON_LDFLAGS}" \
        LDSHARED="${CC} -shared" \
        ${PYTHON_HOST_COMMAND} setup.py build -x bdist_wheel --plat-name ${PYTHON_WIN_ARCH_SUFFIX}

        popd

        # Install using target python
        PYTHONHOME=${PYTHON_INSTALL_PREFIX} \
        ${__wine_cmd} ${PYTHON_INSTALL_PREFIX}/python.exe \
                    -m pip install "$(winepath -w ${__build_dir}/traits-${PYTHON_TRAITS_VERSION}/dist/traits-${PYTHON_TRAITS_VERSION}-cp27-none-${PYTHON_WIN_ARCH_SUFFIX}.whl)" \
        || exit 1
    fi
fi

# ------------------------------------------------------------------------------
# dateutil (matplolib dependency)
# ------------------------------------------------------------------------------
PYTHON_DATEUTIL_VERSION=1.5
PYTHON_DATEUTIL_SOURCE_URL=https://pypi.python.org/packages/b4/7c/df59c89a753eb33c7c44e1dd42de0e9bc2ccdd5a4d576e0bfad97cc280cb/python-dateutil-1.5.tar.gz

if [ "${PYTHON_DATEUTIL}" == "1" ]; then
    echo "============================== PYTHON_DATEUTIL =============================="
    if [ "${__download}" == "1" ]; then
        download ${PYTHON_DATEUTIL_SOURCE_URL}
    fi

    if [ "${__remove_before_install}" == "1"  ]; then
        # Uninstall using target python
        PYTHONHOME=${PYTHON_INSTALL_PREFIX} \
        ${__wine_cmd} ${PYTHON_INSTALL_PREFIX}/python.exe \
                                    -m pip uninstall -y python_dateutil
    fi

    if [ "${__install}" == "1" ]; then
        tar xvf ${__download_dir}/python-dateutil-${PYTHON_DATEUTIL_VERSION}.tar.gz
        pushd ${__build_dir}/python-dateutil-${PYTHON_DATEUTIL_VERSION}

        PYTHONXCPREFIX=${PYTHON_INSTALL_PREFIX} \
        CROSS_COMPILE="${__toolchain}-" \
        CPPFLAGS="${CPPFLAGS} ${PYTHON_CPPFLAGS}" \
        CFLAGS="${CFLAGS} ${PYTHON_CFLAGS}" \
        LDFLAGS="${LDFLAGS} ${PYTHON_LDFLAGS}" \
        LDSHARED="${CC} -shared" \
        ${PYTHON_HOST_COMMAND} setup.py build -x bdist_wheel

        popd

        # Install using target python
        PYTHONHOME=${PYTHON_INSTALL_PREFIX} \
        ${__wine_cmd} ${PYTHON_INSTALL_PREFIX}/python.exe \
                    -m pip install "$(winepath -w ${__build_dir}/python-dateutil-${PYTHON_DATEUTIL_VERSION}/dist/python_dateutil-${PYTHON_DATEUTIL_VERSION}-py2-none-any.whl)" \
        || exit 1
    fi
fi

# ------------------------------------------------------------------------------
# pytz (matplolib dependency)
# ------------------------------------------------------------------------------
PYTHON_PYTZ_VERSION=2012c
PYTHON_PYTZ_SOURCE_URL=https://pypi.python.org/packages/83/df/e8cc8255bcb44802202d6b3cd8acd1bdf36dea2e313837944bc72b896064/pytz-${PYTHON_PYTZ_VERSION}.tar.gz

if [ "${PYTHON_PYTZ}" == "1" ]; then
    echo "============================ PYTHON_PYTZ ============================="
    if [ "${__download}" == "1" ]; then
        download ${PYTHON_PYTZ_SOURCE_URL}
    fi

    if [ "${__remove_before_install}" == "1"  ]; then
        # Uninstall using target python
        PYTHONHOME=${PYTHON_INSTALL_PREFIX} \
        ${__wine_cmd} ${PYTHON_INSTALL_PREFIX}/python.exe \
                                    -m pip uninstall -y pytz
    fi

    if [ "${__install}" == "1" ]; then
        tar xvf ${__download_dir}/pytz-${PYTHON_PYTZ_VERSION}.tar.gz
        pushd ${__build_dir}/pytz-${PYTHON_PYTZ_VERSION}

        PYTHONXCPREFIX=${PYTHON_INSTALL_PREFIX} \
        CROSS_COMPILE="${__toolchain}-" \
        CPPFLAGS="${CPPFLAGS} ${PYTHON_CPPFLAGS}" \
        CFLAGS="${CFLAGS} ${PYTHON_CFLAGS}" \
        LDFLAGS="${LDFLAGS} ${PYTHON_LDFLAGS}" \
        LDSHARED="${CC} -shared" \
        ${PYTHON_HOST_COMMAND} setup.py build -x bdist_wheel

        popd

        # Install using target python
        PYTHONHOME=${PYTHON_INSTALL_PREFIX} \
        ${__wine_cmd} ${PYTHON_INSTALL_PREFIX}/python.exe \
                    -m pip install "$(winepath -w ${__build_dir}/pytz-${PYTHON_PYTZ_VERSION}/dist/pytz-2012rc0-py2-none-any.whl)" \
        || exit 1

    fi
fi

# ------------------------------------------------------------------------------
# pyparsing (matplolib dependency)
# ------------------------------------------------------------------------------
PYTHON_PYPARSING_VERSION=2.0.1
PYTHON_PYPARSING_SOURCE_URL=https://pypi.python.org/packages/44/c7/e2bc51c8aa50b1f5ced031310e2272e883ef2d64f070f882ef1e4301063e/pyparsing-${PYTHON_PYPARSING_VERSION}.tar.gz

if [ "${PYTHON_PYPARSING}" == "1" ]; then
    echo "=========================== PYTHON_PYPARSING ========================="
    if [ "${__download}" == "1" ]; then
        download ${PYTHON_PYPARSING_SOURCE_URL}
    fi

    if [ "${__remove_before_install}" == "1"  ]; then
        # Uninstall using target python
        PYTHONHOME=${PYTHON_INSTALL_PREFIX} \
        ${__wine_cmd} ${PYTHON_INSTALL_PREFIX}/python.exe \
                                    -m pip uninstall -y pyparsing
    fi

    if [ "${__install}" == "1" ]; then
        tar xvf ${__download_dir}/pyparsing-${PYTHON_PYPARSING_VERSION}.tar.gz
        pushd ${__build_dir}/pyparsing-${PYTHON_PYPARSING_VERSION}

        dos2unix setup.py
        # Generate patch to build shared library
        cat << EOF > pyparsing-${PYTHON_PYPARSING_VERSION}.patch
diff -NurwB --strip-trailing-cr --suppress-common-lines setup.py setup.py
--- setup.py    2016-11-10 16:37:17.521122592 +0100
+++ setup.py    2016-11-10 16:37:29.541112684 +0100
@@ -1,6 +1,16 @@
 #!/usr/bin/env python
 
 """Setup script for the pyparsing module distribution."""
+try:
+    from wheel import pep425tags
+except ImportError:
+    pass
+else:
+    pep425tags.get_abi_tag = lambda: 'none'
+
+try:
+    from setuptools import setup
+except ImportError:
-from distutils.core import setup
+    from distutils.core import setup
 
 import sys

EOF
        patch -f -N -i pyparsing-${PYTHON_PYPARSING_VERSION}.patch -p0 

        PYTHONXCPREFIX=${PYTHON_INSTALL_PREFIX} \
        CROSS_COMPILE="${__toolchain}-" \
        CPPFLAGS="${CPPFLAGS} ${PYTHON_CPPFLAGS}" \
        CFLAGS="${CFLAGS} ${PYTHON_CFLAGS}" \
        LDFLAGS="${LDFLAGS} ${PYTHON_LDFLAGS}" \
        LDSHARED="${CC} -shared" \
        ${PYTHON_HOST_COMMAND} setup.py build -x bdist_wheel

        popd

        # Install using target python
        PYTHONHOME=${PYTHON_INSTALL_PREFIX} \
        ${__wine_cmd} ${PYTHON_INSTALL_PREFIX}/python.exe \
                    -m pip install "$(winepath -w ${__build_dir}/pyparsing-${PYTHON_PYPARSING_VERSION}/dist/pyparsing-${PYTHON_PYPARSING_VERSION}-py2-none-any.whl)" \
        || exit 1

    fi
fi

# ------------------------------------------------------------------------------
# cycler (matplolib dependency)
# ------------------------------------------------------------------------------
PYTHON_CYCLER_VERSION=0.10.0
PYTHON_CYCLER_SOURCE_URL=https://pypi.python.org/packages/f7/d2/e07d3ebb2bd7af696440ce7e754c59dd546ffe1bbe732c8ab68b9c834e61/cycler-${PYTHON_CYCLER_VERSION}-py2.py3-none-any.whl

if [ "${PYTHON_CYCLER}" == "1" ]; then
    echo "============================== PYTHON_CYCLER =============================="
    if [ "${__download}" == "1" ]; then
        download ${PYTHON_CYCLER_SOURCE_URL}
    fi

    if [ "${__remove_before_install}" == "1"  ]; then
        # Uninstall using target python
        PYTHONHOME=${PYTHON_INSTALL_PREFIX} \
        ${__wine_cmd} ${PYTHON_INSTALL_PREFIX}/python.exe \
                                    -m pip uninstall -y cycler
    fi

    if [ "${__install}" == "1" ]; then

        # Install using target python
        PYTHONHOME=${PYTHON_INSTALL_PREFIX} \
        ${__wine_cmd} ${PYTHON_INSTALL_PREFIX}/python.exe \
                    -m pip install "$(winepath -w ${__download_dir}/cycler-${PYTHON_CYCLER_VERSION}-py2.py3-none-any.whl)" \
        || exit 1
    fi
fi

# ------------------------------------------------------------------------------
# singledispatch (matplolib dependency)
# ------------------------------------------------------------------------------
PYTHON_SINGLEDISPATCH_VERSION=3.4.0.2
PYTHON_SINGLEDISPATCH_SOURCE_URL=https://pypi.python.org/packages/40/47/f4e53374f4a1d1f4aa0f88c9d57ac3483510ba319a108b9cf59a5267fec6/singledispatch-${PYTHON_SINGLEDISPATCH_VERSION}.tar.gz

if [ "${PYTHON_SINGLEDISPATCH}" == "1" ]; then
    echo "============================== PYTHON_SINGLEDISPATCH =============================="
    if [ "${__download}" == "1" ]; then
        download ${PYTHON_SINGLEDISPATCH_SOURCE_URL}
    fi

    if [ "${__remove_before_install}" == "1"  ]; then
        # Uninstall using target python
        PYTHONHOME=${PYTHON_INSTALL_PREFIX} \
        ${__wine_cmd} ${PYTHON_INSTALL_PREFIX}/python.exe \
                                    -m pip uninstall -y singledispatch
    fi

    if [ "${__install}" == "1" ]; then
        tar xvf ${__download_dir}/singledispatch-${PYTHON_SINGLEDISPATCH_VERSION}.tar.gz
        pushd ${__build_dir}/singledispatch-${PYTHON_SINGLEDISPATCH_VERSION}

        PYTHONXCPREFIX=${PYTHON_INSTALL_PREFIX} \
        CROSS_COMPILE="${__toolchain}-" \
        CPPFLAGS="${CPPFLAGS} ${PYTHON_CPPFLAGS}" \
        CFLAGS="${CFLAGS} ${PYTHON_CFLAGS}" \
        LDFLAGS="${LDFLAGS} ${PYTHON_LDFLAGS}" \
        LDSHARED="${CC} -shared" \
        ${PYTHON_HOST_COMMAND} setup.py build -x bdist_wheel

        popd

        # Install using target python
        PYTHONHOME=${PYTHON_INSTALL_PREFIX} \
        ${__wine_cmd} ${PYTHON_INSTALL_PREFIX}/python.exe \
                    -m pip install "$(winepath -w ${__build_dir}/singledispatch-${PYTHON_SINGLEDISPATCH_VERSION}/dist/singledispatch-${PYTHON_SINGLEDISPATCH_VERSION}-py2-none-any.whl)" \
        || exit 1

    fi
fi

# ------------------------------------------------------------------------------
# tornado (matplolib dependency)
# ------------------------------------------------------------------------------
PYTHON_TORNADO_VERSION=3.1.1
PYTHON_TORNADO_SOURCE_URL=https://pypi.python.org/packages/c9/52/90892c57793f1fb13eeb745adfa32a325ee59875eac46719c641e96f54ec/tornado-${PYTHON_TORNADO_VERSION}.tar.gz

if [ "${PYTHON_TORNADO}" == "1" ]; then
    echo "============================== PYTHON_TORNADO =============================="
    if [ "${__download}" == "1" ]; then
        download ${PYTHON_TORNADO_SOURCE_URL}
    fi

    if [ "${__remove_before_install}" == "1"  ]; then
        # Uninstall using target python
        PYTHONHOME=${PYTHON_INSTALL_PREFIX} \
        ${__wine_cmd} ${PYTHON_INSTALL_PREFIX}/python.exe \
                                    -m pip uninstall -y tornado
    fi

    if [ "${__install}" == "1" ]; then
        tar xvf ${__download_dir}/tornado-${PYTHON_TORNADO_VERSION}.tar.gz
        pushd ${__build_dir}/tornado-${PYTHON_TORNADO_VERSION}

        PYTHONXCPREFIX=${PYTHON_INSTALL_PREFIX} \
        CROSS_COMPILE="${__toolchain}-" \
        CPPFLAGS="${CPPFLAGS} ${PYTHON_CPPFLAGS}" \
        CFLAGS="${CFLAGS} ${PYTHON_CFLAGS}" \
        LDFLAGS="${LDFLAGS} ${PYTHON_LDFLAGS}" \
        LDSHARED="${CC} -shared" \
        ${PYTHON_HOST_COMMAND} setup.py build -x bdist_wheel

        popd

        # Install using target python
        PYTHONHOME=${PYTHON_INSTALL_PREFIX} \
        ${__wine_cmd} ${PYTHON_INSTALL_PREFIX}/python.exe \
                    -m pip install "$(winepath -w ${__build_dir}/tornado-${PYTHON_TORNADO_VERSION}/dist/tornado-${PYTHON_TORNADO_VERSION}-py2-none-any.whl)" \
        || exit 1

    fi
fi

# ------------------------------------------------------------------------------
# certifi (matplolib dependency)
# ------------------------------------------------------------------------------
PYTHON_CERTIFI_VERSION=2016.9.26
PYTHON_CERTIFI_SOURCE_URL=https://pypi.python.org/packages/a2/35/b7b457c95fdd661d4c179201e9e58a2181934695943b08ccfcba09284b4e/certifi-${PYTHON_CERTIFI_VERSION}-py2.py3-none-any.whl

if [ "${PYTHON_CERTIFI}" == "1" ]; then
    echo "============================== PYTHON_CERTIFI =============================="
    if [ "${__download}" == "1" ]; then
        download ${PYTHON_CERTIFI_SOURCE_URL}
    fi

    if [ "${__remove_before_install}" == "1"  ]; then
        # Uninstall using target python
        PYTHONHOME=${PYTHON_INSTALL_PREFIX} \
        ${__wine_cmd} ${PYTHON_INSTALL_PREFIX}/python.exe \
                                    -m pip uninstall -y certifi
    fi

    if [ "${__install}" == "1" ]; then
        # Install using target python
        PYTHONHOME=${PYTHON_INSTALL_PREFIX} \
        ${__wine_cmd} ${PYTHON_INSTALL_PREFIX}/python.exe \
                    -m pip install "$(winepath -w ${__download_dir}/certifi-${PYTHON_CERTIFI_VERSION}-py2.py3-none-any.whl)" \
        || exit 1

    fi
fi

# ------------------------------------------------------------------------------
# backports_abc (matplolib dependency)
# ------------------------------------------------------------------------------
PYTHON_BACKPORTS_ABC_VERSION=0.5
PYTHON_BACKPORTS_ABC_SOURCE_URL=https://pypi.python.org/packages/7d/56/6f3ac1b816d0cd8994e83d0c4e55bc64567532f7dc543378bd87f81cebc7/backports_abc-${PYTHON_BACKPORTS_ABC_VERSION}-py2.py3-none-any.whl

if [ "${PYTHON_BACKPORTS_ABC}" == "1" ]; then
    echo "============================== PYTHON_BACKPORTS_ABC =============================="
    if [ "${__download}" == "1" ]; then
        download ${PYTHON_BACKPORTS_ABC_SOURCE_URL}
    fi

    if [ "${__remove_before_install}" == "1"  ]; then
        # Uninstall using target python
        PYTHONHOME=${PYTHON_INSTALL_PREFIX} \
        ${__wine_cmd} ${PYTHON_INSTALL_PREFIX}/python.exe \
                                    -m pip uninstall -y backports_abc
    fi

    if [ "${__install}" == "1" ]; then
        # Install using target python
        PYTHONHOME=${PYTHON_INSTALL_PREFIX} \
        ${__wine_cmd} ${PYTHON_INSTALL_PREFIX}/python.exe \
                    -m pip install "$(winepath -w ${__download_dir}/backports_abc-${PYTHON_BACKPORTS_ABC_VERSION}-py2.py3-none-any.whl)" \
        || exit 1

    fi
fi

# ------------------------------------------------------------------------------
# nose (matplolib dependency)
# ------------------------------------------------------------------------------
PYTHON_NOSE_VERSION=1.3.1
PYTHON_NOSE_SOURCE_URL=https://pypi.python.org/packages/1d/a3/6df9d0d59cf0b20c505359ddef33d7ce4fe4388dba0948aadf3e75722f33/nose-${PYTHON_NOSE_VERSION}.tar.gz

if [ "${PYTHON_NOSE}" == "1" ]; then
    echo "============================== PYTHON_NOSE =============================="
    if [ "${__download}" == "1" ]; then
        download ${PYTHON_NOSE_SOURCE_URL}
    fi

    if [ "${__remove_before_install}" == "1"  ]; then
        # Uninstall using target python
        PYTHONHOME=${PYTHON_INSTALL_PREFIX} \
        ${__wine_cmd} ${PYTHON_INSTALL_PREFIX}/python.exe \
                                    -m pip uninstall -y nose
    fi

    if [ "${__install}" == "1" ]; then
        tar xvf ${__download_dir}/nose-${PYTHON_NOSE_VERSION}.tar.gz
        pushd ${__build_dir}/nose-${PYTHON_NOSE_VERSION}

        PYTHONXCPREFIX=${PYTHON_INSTALL_PREFIX} \
        CROSS_COMPILE="${__toolchain}-" \
        CPPFLAGS="${CPPFLAGS} ${PYTHON_CPPFLAGS}" \
        CFLAGS="${CFLAGS} ${PYTHON_CFLAGS}" \
        LDFLAGS="${LDFLAGS} ${PYTHON_LDFLAGS}" \
        LDSHARED="${CC} -shared" \
        ${PYTHON_HOST_COMMAND} setup.py build -x bdist_wheel

        popd

        # Install using target python
        PYTHONHOME=${PYTHON_INSTALL_PREFIX} \
        ${__wine_cmd} ${PYTHON_INSTALL_PREFIX}/python.exe \
                    -m pip install "$(winepath -w ${__build_dir}/nose-${PYTHON_NOSE_VERSION}/dist/nose-${PYTHON_NOSE_VERSION}-py2-none-any.whl)" \
        || exit 1

        # Add links to python scripts
        pushd ${CROSSBUILD_INSTALL_PREFIX}/bin
        ln -fs ../python/Scripts/nosetests.exe \
               ../python/Scripts/nosetests-2.7.exe \
               ./
        popd
    fi

    if [ "${__fix_python_scripts}" == "1" ]; then
        for __script in nosetests.exe nosetests-2.7.exe; do
            fix_python_script ${PYTHON_INSTALL_PREFIX}/Scripts/${__script}
        done
    fi
fi

# ------------------------------------------------------------------------------
# pycairo (matplolib dependency)
# ------------------------------------------------------------------------------
PYTHON_CAIRO_VERSION=1.8.8
PYTHON_CAIRO_SOURCE_URL=https://cairographics.org/releases/pycairo-${PYTHON_CAIRO_VERSION}.tar.gz

if [ "${PYTHON_CAIRO}" == "1" ]; then
    echo "============================== PYTHON_CAIRO =============================="
    if [ "${__download}" == "1" ]; then
        download ${PYTHON_CAIRO_SOURCE_URL}
    fi

    if [ "${__remove_before_install}" == "1"  ]; then
        # Uninstall using target python
        PYTHONHOME=${PYTHON_INSTALL_PREFIX} \
        ${__wine_cmd} ${PYTHON_INSTALL_PREFIX}/python.exe \
                                    -m pip uninstall -y pycairo
    fi

    if [ "${__install}" == "1" ]; then
        tar xvf ${__download_dir}/pycairo-${PYTHON_CAIRO_VERSION}.tar.gz
        pushd ${__build_dir}/pycairo-${PYTHON_CAIRO_VERSION}
        # Generate patch to build shared library
        cat << EOF > pycairo-${PYTHON_CAIRO_VERSION}.patch
diff -NurwB --strip-trailing-cr --suppress-common-lines src/surface.c src/surface.c
--- src/surface.c	2016-12-02 15:54:33.785364544 +0100
+++ src/surface.c	2016-12-02 15:54:48.277330491 +0100
@@ -365,7 +365,7 @@
   surface_methods,                    /* tp_methods */
   0,                                  /* tp_members */
   0,                                  /* tp_getset */
-  &PyBaseObject_Type,                 /* tp_base */
+  0,                                  /* tp_base */
   0,                                  /* tp_dict */
   0,                                  /* tp_descr_get */
   0,                                  /* tp_descr_set */
diff -NurwB --strip-trailing-cr --suppress-common-lines src/matrix.c src/matrix.c
--- src/matrix.c	2016-12-02 15:52:26.605666323 +0100
+++ src/matrix.c	2016-12-02 15:53:18.941541492 +0100
@@ -332,7 +332,7 @@
   matrix_methods,                     /* tp_methods */
   0,                                  /* tp_members */
   0,                                  /* tp_getset */
-  &PyBaseObject_Type,                 /* tp_base */
+  0,                                  /* tp_base */
   0,                                  /* tp_dict */
   0,                                  /* tp_descr_get */
   0,                                  /* tp_descr_set */
diff -NurwB --strip-trailing-cr --suppress-common-lines src/cairomodule.c src/cairomodule.c
--- src/cairomodule.c	2016-12-02 15:47:09.718442142 +0100
+++ src/cairomodule.c	2016-12-02 15:49:21.322115699 +0100
@@ -178,7 +178,8 @@
   if (PyType_Ready(&PycairoPath_Type) < 0)
     return;
   PycairoPathiter_Type.tp_iter=&PyObject_SelfIter;
-
+  if (PyType_Ready(&PycairoPathiter_Type) < 0)
+    return;
   if (PyType_Ready(&PycairoPattern_Type) < 0)
     return;
   if (PyType_Ready(&PycairoSolidPattern_Type) < 0)
diff -NurwB --strip-trailing-cr --suppress-common-lines src/path.c src/path.c
--- src/path.c	2016-12-02 15:53:29.073517430 +0100
+++ src/path.c	2016-12-02 15:53:50.941465611 +0100
@@ -206,7 +206,7 @@
   0,			        	/* tp_methods */
   0,					/* tp_members */
   0,					/* tp_getset */
-  &PyBaseObject_Type,                   /* tp_base */
+  0,					/* tp_base */
   0,					/* tp_dict */
   0,					/* tp_descr_get */
   0,					/* tp_descr_set */
diff -NurwB --strip-trailing-cr --suppress-common-lines src/pattern.c src/pattern.c
--- src/pattern.c	2016-12-02 15:54:03.153436744 +0100
+++ src/pattern.c	2016-12-02 15:54:25.133384906 +0100
@@ -194,7 +194,7 @@
   pattern_methods,                    /* tp_methods */
   0,                                  /* tp_members */
   0,                                  /* tp_getset */
-  &PyBaseObject_Type,                 /* tp_base */
+  0,                                  /* tp_base */
   0,                                  /* tp_dict */
   0,                                  /* tp_descr_get */
   0,                                  /* tp_descr_set */
diff -NurwB --strip-trailing-cr --suppress-common-lines src/font.c src/font.c
--- src/font.c	2016-12-02 15:51:00.541873600 +0100
+++ src/font.c	2016-12-02 15:52:06.741713943 +0100
@@ -131,7 +131,7 @@
   0,                                  /* tp_methods */
   0,                                  /* tp_members */
   0,                                  /* tp_getset */
-  &PyBaseObject_Type,                 /* tp_base */
+  0,                                  /* tp_base */
   0,                                  /* tp_dict */
   0,                                  /* tp_descr_get */
   0,                                  /* tp_descr_set */
@@ -410,7 +410,7 @@
   scaled_font_methods,                /* tp_methods */
   0,                                  /* tp_members */
   0,                                  /* tp_getset */
-  &PyBaseObject_Type,                 /* tp_base */
+  0,                                  /* tp_base */
   0,                                  /* tp_dict */
   0,                                  /* tp_descr_get */
   0,                                  /* tp_descr_set */
@@ -595,7 +595,7 @@
   font_options_methods,               /* tp_methods */
   0,                                  /* tp_members */
   0,                                  /* tp_getset */
-  &PyBaseObject_Type,                 /* tp_base */
+  0,                                  /* tp_base */
   0,                                  /* tp_dict */
   0,                                  /* tp_descr_get */
   0,                                  /* tp_descr_set */
diff -NurwB --strip-trailing-cr --suppress-common-lines src/context.c src/context.c
--- src/context.c	2016-12-02 15:49:42.614063459 +0100
+++ src/context.c	2016-12-02 15:50:02.542014708 +0100
@@ -1430,7 +1430,7 @@
   pycairo_methods,                    /* tp_methods */
   0,                                  /* tp_members */
   0,                                  /* tp_getset */
-  &PyBaseObject_Type,                 /* tp_base */
+  0,                                  /* tp_base */
   0,                                  /* tp_dict */
   0,                                  /* tp_descr_get */
   0,                                  /* tp_descr_set */
diff -NurwB --strip-trailing-cr --suppress-common-lines setup.py setup.py
--- setup.py	2016-12-02 16:07:36.486868525 +0100
+++ setup.py	2016-12-02 16:07:39.286860050 +0100
@@ -1,11 +1,34 @@
 #!/usr/bin/env python
 
-import distutils.core      as dic
+try:
+    from wheel import pep425tags
+except ImportError:
+    pass
+else:
+    pep425tags.get_abi_tag = lambda: 'none'
+
+try:
+    import setuptools      as dic
+except ImportError:
+    import distutils.core      as dic
+    
 import distutils.dir_util  as dut
 import distutils.file_util as fut
 import io
 import subprocess
 import sys
+ 
+from distutils import sysconfig
+def _init_posix():
+    """Initialize the module as appropriate for POSIX systems."""
+    # _sysconfigdata is generated at build time, see the sysconfig module
+    from _sysconfigdata import build_time_vars
+    sysconfig._config_vars = {}
+    sysconfig._config_vars.update(build_time_vars)
+    sysconfig._config_vars['SO'] = '.pyd'
+    sysconfig._config_vars['EXE'] = '.exe'
+
+sysconfig._init_posix = _init_posix
 
 pycairo_version        = '1.8.8'
 cairo_version_required = '1.8.8'
@@ -105,6 +128,8 @@
   version = pycairo_version,
   description = "python interface for cairo",
   ext_modules = [cairo],
-  data_files=[('include/pycairo',['src/pycairo.h']),
-              ('lib/pkgconfig',[pkgconfig_file])],
+  packages = ['cairo'],
+  package_dir = {'cairo': 'src'},
+  data_files=[('cairo/include/pycairo',['src/pycairo.h']),
+              ('cairo/lib/pkgconfig',[pkgconfig_file])],
   )

EOF
        patch -f -N -i pycairo-${PYTHON_CAIRO_VERSION}.patch -p0 

        PYTHONXCPREFIX=${PYTHON_INSTALL_PREFIX} \
        CROSS_COMPILE="${__toolchain}-" \
        CPPFLAGS="${CPPFLAGS} ${PYTHON_CPPFLAGS}" \
        CFLAGS="${CFLAGS} ${PYTHON_CFLAGS}" \
        LDFLAGS="${LDFLAGS} ${PYTHON_LDFLAGS}" \
        LDSHARED="${CC} -shared" \
        ${PYTHON_HOST_COMMAND} setup.py build -x bdist_wheel --plat-name ${PYTHON_WIN_ARCH_SUFFIX}

        popd

        # Install using target python
        PYTHONHOME=${PYTHON_INSTALL_PREFIX} \
        ${__wine_cmd} ${PYTHON_INSTALL_PREFIX}/python.exe \
                    -m pip install "$(winepath -w ${__build_dir}/pycairo-${PYTHON_CAIRO_VERSION}/dist/pycairo-${PYTHON_CAIRO_VERSION}-cp27-none-${PYTHON_WIN_ARCH_SUFFIX}.whl)" \
        || exit 1

    fi
fi

# ------------------------------------------------------------------------------
# pyconfigobj (matplolib dependency)
# ------------------------------------------------------------------------------
PYTHON_CONFIGOBJ_VERSION=4.7.2
PYTHON_CONFIGOBJ_SOURCE_URL=https://pypi.python.org/packages/49/9c/4a97c36ba82e60b390614f050cd1d3e8652f1b38d1e6fde6e1ff4f16bc3e/configobj-${PYTHON_CONFIGOBJ_VERSION}.tar.gz

if [ "${PYTHON_CONFIGOBJ}" == "1" ]; then
    echo "============================== PYTHON_CONFIGOBJ =============================="
    if [ "${__download}" == "1" ]; then
        download ${PYTHON_CONFIGOBJ_SOURCE_URL}
    fi

    if [ "${__remove_before_install}" == "1"  ]; then
        # Uninstall using target python
        PYTHONHOME=${PYTHON_INSTALL_PREFIX} \
        ${__wine_cmd} ${PYTHON_INSTALL_PREFIX}/python.exe \
                                    -m pip uninstall -y configobj
    fi

    if [ "${__install}" == "1" ]; then
        tar xvf ${__download_dir}/configobj-${PYTHON_CONFIGOBJ_VERSION}.tar.gz
        pushd ${__build_dir}/configobj-${PYTHON_CONFIGOBJ_VERSION}
        # Generate patch to build shared library
        cat << EOF > configobj-${PYTHON_CONFIGOBJ_VERSION}.patch
diff -NurwB --strip-trailing-cr --suppress-common-lines setup.py setup.py
--- setup.py    2016-12-02 23:34:23.484589059 +0100
+++ setup.py    2016-12-02 23:38:12.884985593 +0100
@@ -9,7 +9,18 @@
 # http://www.voidspace.org.uk/python/license.shtml
 
 import sys
+try:
+    from wheel import pep425tags
+except ImportError:
+    pass
+else:
+    pep425tags.get_abi_tag = lambda: 'none'
+
+try:
+    from setuptools      import setup
+except ImportError:
-from distutils.core import setup
+    from distutils.core import setup
+
 from configobj import __version__ as VERSION
 
 NAME = 'configobj'

EOF
        patch -f -N -i configobj-${PYTHON_CONFIGOBJ_VERSION}.patch -p0 

        PYTHONXCPREFIX=${PYTHON_INSTALL_PREFIX} \
        CROSS_COMPILE="${__toolchain}-" \
        CPPFLAGS="${CPPFLAGS} ${PYTHON_CPPFLAGS}" \
        CFLAGS="${CFLAGS} ${PYTHON_CFLAGS}" \
        LDFLAGS="${LDFLAGS} ${PYTHON_LDFLAGS}" \
        LDSHARED="${CC} -shared" \
        ${PYTHON_HOST_COMMAND} setup.py build -x bdist_wheel

        popd

        # Install using target python
        PYTHONHOME=${PYTHON_INSTALL_PREFIX} \
        ${__wine_cmd} ${PYTHON_INSTALL_PREFIX}/python.exe \
                    -m pip install "$(winepath -w ${__build_dir}/configobj-${PYTHON_CONFIGOBJ_VERSION}/dist/configobj-${PYTHON_CONFIGOBJ_VERSION}-py2-none-any.whl)" \
        || exit 1

    fi
fi

# ------------------------------------------------------------------------------
# matplotlib
# ------------------------------------------------------------------------------
PYTHON_MATPLOTLIB_VERSION=1.3.1
PYTHON_MATPLOTLIB_INSTALL_PREFIX=${CROSSBUILD_INSTALL_PREFIX}/matplotlib-${PYTHON_MATPLOTLIB_VERSION}
PYTHON_MATPLOTLIB_SOURCE_URL=https://pypi.python.org/packages/d4/d0/17f17792a4d50994397052220dbe3ac9850ecbde0297b7572933fa4a5c98/matplotlib-${PYTHON_MATPLOTLIB_VERSION}.tar.gz
PYTHON_MATPLOTLIB_DEPENDENCIES="freetype2"

if [ "${PYTHON_MATPLOTLIB}" == "1" ]; then
    echo "============================== PYTHON_MATPLOTLIB =============================="
    if [ "${__download}" == "1" ]; then
        download ${PYTHON_MATPLOTLIB_SOURCE_URL}
    fi

    if [ "${__remove_before_install}" == "1"  ]; then
        # Uninstall using target python
        PYTHONHOME=${PYTHON_INSTALL_PREFIX} \
        ${__wine_cmd} ${PYTHON_INSTALL_PREFIX}/python.exe \
                                    -m pip uninstall -y matplotlib
    fi

    if [ "${__install}" == "1" ]; then
        tar xvf ${__download_dir}/matplotlib-${PYTHON_MATPLOTLIB_VERSION}.tar.gz
        pushd ${__build_dir}/matplotlib-${PYTHON_MATPLOTLIB_VERSION}

        # Generate patch to build shared library
        cat << EOF > matplotlib-${PYTHON_MATPLOTLIB_VERSION}.patch
diff -NurwB --strip-trailing-cr --suppress-common-lines setupext.py setupext.py
--- setupext.py 2016-12-06 12:26:09.281730613 +0100
+++ setupext.py 2016-12-06 12:26:17.353734338 +0100
@@ -711,29 +711,42 @@
 
     @staticmethod
     def include_dirs_hook():
-        if sys.version_info[0] >= 3:
-            import builtins
-            if hasattr(builtins, '__NUMPY_SETUP__'):
-                del builtins.__NUMPY_SETUP__
-            import imp
-            import numpy
-            imp.reload(numpy)
-        else:
-            import __builtin__
-            if hasattr(__builtin__, '__NUMPY_SETUP__'):
-                del __builtin__.__NUMPY_SETUP__
-            import numpy
-            reload(numpy)
+        numpy_include_dir = os.environ.get('NUMPY_INCLUDE_DIR')
+        if numpy_include_dir is None :
+            if sys.version_info[0] >= 3:
+                import builtins
+                if hasattr(builtins, '__NUMPY_SETUP__'):
+                    del builtins.__NUMPY_SETUP__
+                import imp
+                import numpy
+                imp.reload(numpy)
+            else:
+                import __builtin__
+                if hasattr(__builtin__, '__NUMPY_SETUP__'):
+                    del __builtin__.__NUMPY_SETUP__
+                import numpy
+                reload(numpy)
+
+            ext = Extension('test', [])
+            ext.include_dirs.append(numpy.get_include())
+            if not has_include_file(
+                    ext.include_dirs, os.path.join("numpy", "arrayobject.h")):
+                warnings.warn(
+                    "The C headers for numpy could not be found. "
+                    "You may need to install the development package")
 
-        ext = Extension('test', [])
-        ext.include_dirs.append(numpy.get_include())
-        if not has_include_file(
-                ext.include_dirs, os.path.join("numpy", "arrayobject.h")):
-            warnings.warn(
-                "The C headers for numpy could not be found. "
-                "You may need to install the development package")
+            return [numpy.get_include()]
+        
+        else:
+            ext = Extension('test', [])
+            ext.include_dirs.append(numpy_include_dir)
+            if not has_include_file(
+                    ext.include_dirs, os.path.join("numpy", "arrayobject.h")):
+                warnings.warn(
+                    "The C headers for numpy could not be found. "
+                    "You may need to install the development package")
 
-        return [numpy.get_include()]
+            return [numpy_include_dir]
 
     def check(self):
         min_version = extract_versions()['__version__numpy__']

diff -NurwB --strip-trailing-cr --suppress-common-lines src/_backend_agg.cpp src/_backend_agg.cpp
--- src/_backend_agg.cpp    2016-12-06 15:48:57.495036429 +0100
+++ src/_backend_agg.cpp    2016-12-06 15:53:09.566918368 +0100
@@ -2124,13 +2124,14 @@
     args.verify_length(1);
 
     FILE *fp = NULL;
+    mpl_off_t offset;
     Py::Object py_fileobj = Py::Object(args[0]);
     PyObject* py_file = NULL;
     bool close_file = false;
 
     if (py_fileobj.isString())
     {
-        if ((py_file = npy_PyFile_OpenFile(py_fileobj.ptr(), (char *)"wb")) == NULL) {
+        if ((py_file = mpl_PyFile_OpenFile(py_fileobj.ptr(), (char *)"wb")) == NULL) {
             throw Py::Exception();
         }
     }
@@ -2139,28 +2140,28 @@
         py_file = py_fileobj.ptr();
     }
 
-    if ((fp = npy_PyFile_Dup(py_file, (char *)"wb")))
+    if ((fp = mpl_PyFile_Dup(py_file, (char *)"wb", &offset)))
     {
         if (fwrite(pixBuffer, 1, NUMBYTES, fp) != NUMBYTES)
         {
-            if (npy_PyFile_DupClose(py_file, fp)) {
+            if (mpl_PyFile_DupClose(py_file, fp, offset)) {
               throw Py::RuntimeError("Error closing dupe file handle");
             }
 
             if (close_file) {
-                npy_PyFile_CloseFile(py_file);
+                mpl_PyFile_CloseFile(py_file);
                 Py_DECREF(py_file);
             }
 
             throw Py::RuntimeError("Error writing to file");
         }
 
-        if (npy_PyFile_DupClose(py_file, fp)) {
+        if (mpl_PyFile_DupClose(py_file, fp, offset)) {
           throw Py::RuntimeError("Error closing dupe file handle");
         }
 
         if (close_file) {
-            npy_PyFile_CloseFile(py_file);
+            mpl_PyFile_CloseFile(py_file);
             Py_DECREF(py_file);
         }
     }
diff -NurwB --strip-trailing-cr --suppress-common-lines src/file_compat.h src/file_compat.h
--- src/file_compat.h   2016-12-06 15:50:09.243003839 +0100
+++ src/file_compat.h   2016-12-06 16:00:04.706712794 +0100
@@ -1,24 +1,67 @@
 #ifndef __FILE_COMPAT_H__
 #define __FILE_COMPAT_H__
 
-#include "numpy/npy_3kcompat.h"
+#include <Python.h>
+#include <stdio.h>
+#include "numpy/npy_common.h"
+#include "numpy/ndarrayobject.h"
+#include "mplutils.h"
+
+#ifdef __cplusplus
+extern "C" {
+#endif
+
+#if defined(_MSC_VER) && defined(_WIN64) && (_MSC_VER > 1400)
+    #include <io.h>
+    #define npy_fseek _fseeki64
+    #define npy_ftell _ftelli64
+    #define npy_lseek _lseeki64
+    #define mpl_off_t npy_int64
+
+    #if NPY_SIZEOF_INT == 8
+        #define MPL_OFF_T_PYFMT "i"
+    #elif NPY_SIZEOF_LONG == 8
+        #define MPL_OFF_T_PYFMT "l"
+    #elif NPY_SIZEOF_LONGLONG == 8
+        #define MPL_OFF_T_PYFMT "L"
+    #else
+        #error Unsupported size for type off_t
+    #endif
+#else
+    #define npy_fseek fseek
+    #define npy_ftell ftell
+    #define npy_lseek lseek
+    #define mpl_off_t off_t
+
+    #if NPY_SIZEOF_INT == NPY_SIZEOF_SHORT
+        #define MPL_OFF_T_PYFMT "h"
+    #elif NPY_SIZEOF_INT == NPY_SIZEOF_INT
+        #define MPL_OFF_T_PYFMT "i"
+    #elif NPY_SIZEOF_INT == NPY_SIZEOF_LONG
+        #define MPL_OFF_T_PYFMT "l"
+    #elif NPY_SIZEOF_INT == NPY_SIZEOF_LONGLONG
+        #define MPL_OFF_T_PYFMT "L"
+    #else
+        #error Unsupported size for type off_t
+    #endif
+#endif
 
-#if NPY_API_VERSION < 0x4 /* corresponds to Numpy 1.5 */
 /*
  * PyFile_* compatibility
  */
-#if defined(NPY_PY3K)
+#if PY3K
 
 /*
  * Get a FILE* handle to the file represented by the Python object
  */
 static NPY_INLINE FILE*
-npy_PyFile_Dup(PyObject *file, char *mode)
+mpl_PyFile_Dup(PyObject *file, char *mode, mpl_off_t *orig_pos)
 {
     int fd, fd2;
     PyObject *ret, *os;
-    Py_ssize_t pos;
+    mpl_off_t pos;
     FILE *handle;
+
     /* Flush first to ensure things end up in the file in the correct order */
     ret = PyObject_CallMethod(file, "flush", "");
     if (ret == NULL) {
@@ -29,6 +72,9 @@
     if (fd == -1) {
         return NULL;
     }
+
+    /* The handle needs to be dup'd because we have to call fclose
+       at the end */
     os = PyImport_ImportModule("os");
     if (os == NULL) {
         return NULL;
@@ -40,6 +86,8 @@
     }
     fd2 = PyNumber_AsSsize_t(ret, NULL);
     Py_DECREF(ret);
+
+    /* Convert to FILE* handle */
 #ifdef _WIN32
     handle = _fdopen(fd2, mode);
 #else
@@ -49,6 +97,15 @@
         PyErr_SetString(PyExc_IOError,
                         "Getting a FILE* from a Python file object failed");
     }
+
+    /* Record the original raw file handle position */
+    *orig_pos = npy_ftell(handle);
+    if (*orig_pos == -1) {
+        PyErr_SetString(PyExc_IOError, "obtaining file position failed");
+        return NULL;
+    }
+
+    /* Seek raw handle to the Python-side position */
     ret = PyObject_CallMethod(file, "tell", "");
     if (ret == NULL) {
         fclose(handle);
@@ -60,7 +117,10 @@
         fclose(handle);
         return NULL;
     }
-    npy_fseek(handle, pos, SEEK_SET);
+    if (npy_fseek(handle, pos, SEEK_SET) == -1) {
+        PyErr_SetString(PyExc_IOError, "seeking file failed");
+        return NULL;
+    }
     return handle;
 }
 
@@ -68,14 +128,35 @@
  * Close the dup-ed file handle, and seek the Python one to the current position
  */
 static NPY_INLINE int
-npy_PyFile_DupClose(PyObject *file, FILE* handle)
+mpl_PyFile_DupClose(PyObject *file, FILE* handle, mpl_off_t orig_pos)
 {
+    int fd;
     PyObject *ret;
-    Py_ssize_t position;
+    mpl_off_t position;
+
     position = npy_ftell(handle);
+
+    /* Close the FILE* handle */
     fclose(handle);
 
-    ret = PyObject_CallMethod(file, "seek", NPY_SSIZE_T_PYFMT "i", position, 0);
+    /* Restore original file handle position, in order to not confuse
+       Python-side data structures */
+    fd = PyObject_AsFileDescriptor(file);
+    if (fd == -1) {
+        return -1;
+    }
+    if (npy_lseek(fd, orig_pos, SEEK_SET) == -1) {
+        PyErr_SetString(PyExc_IOError, "seeking file failed");
+        return -1;
+    }
+
+    if (position == -1) {
+        PyErr_SetString(PyExc_IOError, "obtaining file position failed");
+        return -1;
+    }
+
+    /* Seek Python-side handle to the FILE* handle position */
+    ret = PyObject_CallMethod(file, "seek", MPL_OFF_T_PYFMT "i", position, 0);
     if (ret == NULL) {
         return -1;
     }
@@ -84,7 +165,7 @@
 }
 
 static NPY_INLINE int
-npy_PyFile_Check(PyObject *file)
+mpl_PyFile_Check(PyObject *file)
 {
     int fd;
     fd = PyObject_AsFileDescriptor(file);
@@ -97,13 +178,14 @@
 
 #else
 
-#define npy_PyFile_Dup(file, mode) PyFile_AsFile(file)
-#define npy_PyFile_DupClose(file, handle) (0)
+#define mpl_PyFile_Dup(file, mode, orig_pos_p) PyFile_AsFile(file)
+#define mpl_PyFile_DupClose(file, handle, orig_pos) (0)
+#define mpl_PyFile_Check PyFile_Check
 
 #endif
 
 static NPY_INLINE PyObject*
-npy_PyFile_OpenFile(PyObject *filename, const char *mode)
+mpl_PyFile_OpenFile(PyObject *filename, const char *mode)
 {
     PyObject *open;
     open = PyDict_GetItemString(PyEval_GetBuiltins(), "open");
@@ -113,12 +195,8 @@
     return PyObject_CallFunction(open, "Os", filename, mode);
 }
 
-#endif /* NPY_API_VERSION < 0x4 */
-
-#if NPY_API_VERSION < 0x7 /* corresponds to Numpy 1.7 */
-
 static NPY_INLINE int
-npy_PyFile_CloseFile(PyObject *file)
+mpl_PyFile_CloseFile(PyObject *file)
 {
     PyObject *ret;
 
@@ -130,6 +208,8 @@
     return 0;
 }
 
-#endif /* NPY_API_VERSION < 0x7 */
+#ifdef __cplusplus
+}
+#endif
 
 #endif /* ifndef __FILE_COMPAT_H__ */
diff -NurwB --strip-trailing-cr --suppress-common-lines src/_png.cpp src/_png.cpp
--- src/_png.cpp    2016-12-06 15:29:14.187583475 +0100
+++ src/_png.cpp    2016-12-06 15:53:09.566918368 +0100
@@ -105,6 +105,7 @@
     args.verify_length(4, 5);
 
     FILE *fp = NULL;
+    mpl_off_t offset;
     bool close_file = false;
     bool close_dup_file = false;
     Py::Object buffer_obj = Py::Object(args[0]);
@@ -134,7 +135,7 @@
     PyObject* py_file = NULL;
     if (py_fileobj.isString())
     {
-        if ((py_file = npy_PyFile_OpenFile(py_fileobj.ptr(), (char *)"wb")) == NULL) {
+        if ((py_file = mpl_PyFile_OpenFile(py_fileobj.ptr(), (char *)"wb")) == NULL) {
             throw Py::Exception();
         }
         close_file = true;
@@ -144,7 +145,7 @@
         py_file = py_fileobj.ptr();
     }
 
-    if ((fp = npy_PyFile_Dup(py_file, (char *)"wb")))
+    if ((fp = mpl_PyFile_Dup(py_file, (char *)"wb", &offset)))
     {
         close_dup_file = true;
     }
@@ -240,14 +241,14 @@
 
         if (close_dup_file)
         {
-            if (npy_PyFile_DupClose(py_file, fp)) {
+            if (mpl_PyFile_DupClose(py_file, fp, offset)) {
               throw Py::RuntimeError("Error closing dupe file handle");
             }
         }
 
         if (close_file)
         {
-            npy_PyFile_CloseFile(py_file);
+            mpl_PyFile_CloseFile(py_file);
             Py_DECREF(py_file);
         }
         /* Changed calls to png_destroy_write_struct to follow
@@ -261,14 +262,14 @@
     delete [] row_pointers;
     if (close_dup_file)
     {
-        if (npy_PyFile_DupClose(py_file, fp)) {
+        if (mpl_PyFile_DupClose(py_file, fp, offset)) {
           throw Py::RuntimeError("Error closing dupe file handle");
         }
     }
 
     if (close_file)
     {
-        npy_PyFile_CloseFile(py_file);
+        mpl_PyFile_CloseFile(py_file);
         Py_DECREF(py_file);
     }
 
@@ -312,13 +313,14 @@
 {
     png_byte header[8];   // 8 is the maximum size that can be checked
     FILE* fp = NULL;
+    mpl_off_t offset;
     bool close_file = false;
     bool close_dup_file = false;
     PyObject *py_file = NULL;
 
     if (py_fileobj.isString())
     {
-        if ((py_file = npy_PyFile_OpenFile(py_fileobj.ptr(), (char *)"rb")) == NULL) {
+        if ((py_file = mpl_PyFile_OpenFile(py_fileobj.ptr(), (char *)"rb")) == NULL) {
             throw Py::Exception();
         }
         close_file = true;
@@ -326,7 +328,7 @@
         py_file = py_fileobj.ptr();
     }
 
-    if ((fp = npy_PyFile_Dup(py_file, "rb")))
+    if ((fp = mpl_PyFile_Dup(py_file, "rb", &offset)))
     {
         close_dup_file = true;
     }
@@ -574,14 +576,14 @@
 #endif
     if (close_dup_file)
     {
-        if (npy_PyFile_DupClose(py_file, fp)) {
+        if (mpl_PyFile_DupClose(py_file, fp, offset)) {
           throw Py::RuntimeError("Error closing dupe file handle");
         }
     }
 
     if (close_file)
     {
-        npy_PyFile_CloseFile(py_file);
+        mpl_PyFile_CloseFile(py_file);
         Py_DECREF(py_file);
     }
 
diff -NurwB --strip-trailing-cr --suppress-common-lines src/ft2font.cpp src/ft2font.cpp
diff -NurwB --strip-trailing-cr --suppress-common-lines setup.py setup.py
--- setup.py    2016-12-06 11:52:07.984818935 +0100
+++ setup.py    2016-12-06 16:06:57.074521622 +0100
@@ -8,6 +8,24 @@
 # This needs to be the very first thing to use distribute
 from distribute_setup import use_setuptools
 use_setuptools()
+try:
+    from wheel import pep425tags
+except ImportError:
+    pass
+else:
+    pep425tags.get_abi_tag = lambda: 'none'
+
+from distutils import sysconfig
+def _init_posix():
+    """Initialize the module as appropriate for POSIX systems."""
+    # _sysconfigdata is generated at build time, see the sysconfig module
+    from _sysconfigdata import build_time_vars
+    sysconfig._config_vars = {}
+    sysconfig._config_vars.update(build_time_vars)
+    sysconfig._config_vars['SO'] = '.pyd'
+    sysconfig._config_vars['EXE'] = '.exe'
+
+sysconfig._init_posix = _init_posix
 
 import sys
 

 # distutils is breaking our sdists for files in symlinked dirs.
diff -NurwB --strip-trailing-cr --suppress-common-lines setup.cfg setup.cfg
--- setup.cfg   2016-12-06 11:27:29.488198563 +0100
+++ setup.cfg   2016-12-06 16:53:41.173473189 +0100
@@ -0,0 +1,82 @@
+# Rename this file to setup.cfg to modify matplotlib's
+# build options.
+
+[egg_info]
+
+[directories]
+# Uncomment to override the default basedir in setupext.py.
+# This can be a single directory or a comma-delimited list of directories.
+basedirlist = ${CROSSBUILD_INSTALL_PREFIX}
+
+[status]
+# To suppress display of the dependencies and their versions
+# at the top of the build log, uncomment the following line:
+#suppress = False
+
+[packages]
+# There are a number of subpackages of matplotlib that are considered
+# optional.  They are all installed by default, but they may be turned
+# off here.
+#
+#tests = True
+#sample_data = True
+#toolkits = True
+
+[gui_support]
+# Matplotlib supports multiple GUI toolkits, including Cocoa,
+# GTK, Fltk, MacOSX, Qt, Qt4, Tk, and WX. Support for many of
+# these toolkits requires AGG, the Anti-Grain Geometry library,
+# which is provided by matplotlib and built by default.
+#
+# Some backends are written in pure Python, and others require
+# extension code to be compiled. By default, matplotlib checks for
+# these GUI toolkits during installation and, if present, compiles the
+# required extensions to support the toolkit.
+#
+# - GTK 2.x support of any kind requires the GTK runtime environment
+#   headers and PyGTK.
+# - Tk support requires Tk development headers and Tkinter.
+# - Mac OSX backend requires the Cocoa headers included with XCode.
+# - Windowing is MS-Windows specific, and requires the "windows.h"
+#   header.
+#
+# The other GUI toolkits do not require any extension code, and can be
+# used as long as the libraries are installed on your system --
+# therefore they are installed unconditionally.
+#
+# You can uncomment any the following lines to change this
+# behavior. Acceptible values are:
+#
+#     True: build the extension. Exits with a warning if the
+#           required dependencies are not available
+#     False: do not build the extension
+#     auto: build if the required dependencies are available,
+#           otherwise skip silently. This is the default
+#           behavior
+#
+#agg = auto
+#cairo = auto
+gtk = False
+gtk3agg = False
+gtk3cairo = False
+gtkagg = False
+#macosx = auto
+pyside = False
+#qt4agg = auto
+tkagg = False
+#windowing = auto
+#wxagg = auto
+
+[rc_options]
+# User-configurable options
+#
+# Default backend, one of: Agg, Cairo, CocoaAgg, GTK, GTKAgg, GTKCairo,
+# FltkAgg, MacOSX, Pdf, Ps, QtAgg, Qt4Agg, SVG, TkAgg, WX, WXAgg.
+#
+# The Agg, Ps, Pdf and SVG backends do not require external
+# dependencies. Do not choose GTK, GTKAgg, GTKCairo, MacOSX, or TkAgg
+# if you have disabled the relevent extension modules.  Agg will be used
+# by default.
+#
+#backend = Agg
+#

EOF
        patch -f -N -i matplotlib-${PYTHON_MATPLOTLIB_VERSION}.patch -p0 

        PYTHONXCPREFIX=${PYTHON_INSTALL_PREFIX} \
        CROSS_COMPILE="${__toolchain}-" \
        NUMPY_INCLUDE_DIR="${PYTHON_INSTALL_PREFIX}/Lib/site-packages/numpy/core/include" \
        CPPFLAGS="${CPPFLAGS} ${PYTHON_CPPFLAGS} $(get_c_flags ${PYTHON_MATPLOTLIB_DEPENDENCIES})" \
        LDFLAGS="${LDFLAGS} ${PYTHON_LDFLAGS} $(get_link_flags ${PYTHON_MATPLOTLIB_DEPENDENCIES})" \
        LDSHARED="${CC} -shared" \
        ${PYTHON_HOST_COMMAND} setup.py build -x bdist_wheel --plat-name ${PYTHON_WIN_ARCH_SUFFIX}

        popd

        # Install using target python
        PYTHONHOME=${PYTHON_INSTALL_PREFIX} \
        ${__wine_cmd} ${PYTHON_INSTALL_PREFIX}/python.exe \
                    -m pip install "$(winepath -w ${__build_dir}/matplotlib-${PYTHON_MATPLOTLIB_VERSION}/dist/matplotlib-${PYTHON_MATPLOTLIB_VERSION}-cp27-none-${PYTHON_WIN_ARCH_SUFFIX}.whl)" \
        || exit 1
    fi
fi

# ------------------------------------------------------------------------------
# pycrypto (paramiko dependency)
# ------------------------------------------------------------------------------
PYTHON_CRYPTO_VERSION=2.6.1
PYTHON_CRYPTO_SOURCE_URL=https://pypi.python.org/packages/60/db/645aa9af249f059cc3a368b118de33889219e0362141e75d4eaf6f80f163/pycrypto-${PYTHON_CRYPTO_VERSION}.tar.gz

if [ "${PYTHON_CRYPTO}" == "1" ]; then
    echo "============================== PYTHON_CRYPTO =============================="
    if [ "${__download}" == "1" ]; then
        download ${PYTHON_CRYPTO_SOURCE_URL}
    fi

    if [ "${__remove_before_install}" == "1"  ]; then
        # Uninstall using target python
        PYTHONHOME=${PYTHON_INSTALL_PREFIX} \
        ${__wine_cmd} ${PYTHON_INSTALL_PREFIX}/python.exe \
                                    -m pip uninstall -y pycrypto
    fi

    if [ "${__install}" == "1" ]; then
        tar xvf ${__download_dir}/pycrypto-${PYTHON_CRYPTO_VERSION}.tar.gz
        pushd ${__build_dir}/pycrypto-${PYTHON_CRYPTO_VERSION}
        # Generate patch to build shared library
        cat << EOF > pycrypto-${PYTHON_CRYPTO_VERSION}.patch
diff -NurB --strip-trailing-cr --suppress-common-lines setup.py setup.py
--- setup.py	2017-07-24 09:37:13.000000000 +0000
+++ setup.py	2017-07-24 09:39:06.000000000 +0000
@@ -36,7 +36,18 @@
 
 __revision__ = "\$Id\$"
 
-from distutils import core
+try:
+    from wheel import pep425tags
+except ImportError:
+    pass
+else:
+    pep425tags.get_abi_tag = lambda: 'none'
+
+try:
+    import setuptools as core
+except ImportError:
+    from distutils import core
+    
 from distutils.ccompiler import new_compiler
 from distutils.core import Extension, Command
 from distutils.command.build import build
@@ -43,6 +54,19 @@
 from distutils.command.build_ext import build_ext
 import os, sys, re
 import struct
+import sys
+ 
+from distutils import sysconfig
+def _init_posix():
+    """Initialize the module as appropriate for POSIX systems."""
+    # _sysconfigdata is generated at build time, see the sysconfig module
+    from _sysconfigdata import build_time_vars
+    sysconfig._config_vars = {}
+    sysconfig._config_vars.update(build_time_vars)
+    sysconfig._config_vars['SO'] = '.pyd'
+    sysconfig._config_vars['EXE'] = '.exe'
+
+sysconfig._init_posix = _init_posix
 
 if sys.version[0:1] == '1':
     raise RuntimeError ("The Python Cryptography Toolkit requires "
@@ -271,7 +295,12 @@
         if not os.path.exists("config.status"):
             if os.system("chmod 0755 configure") != 0:
                 raise RuntimeError("chmod error")
+
             cmd = "sh configure"    # we use "sh" here so that it'll work on mingw32 with standard python.org binaries
+            cross_compile = os.environ.get('CROSS_COMPILE')
+            if cross_compile.endswith('-'):
+                cmd += " --host %s" % cross_compile[:-1]
+
             if self.verbose < 1:
                 cmd += " -q"
             if os.system(cmd) != 0:

diff -NurB --strip-trailing-cr --suppress-common-lines src/block_template.c src/block_template.c
--- src/block_template.c	2017-07-24 10:05:25.000000000 +0000
+++ src/block_template.c	2017-07-24 10:07:02.000000000 +0000
@@ -28,6 +28,21 @@
 #ifdef HAVE_CONFIG_H
 #include "config.h"
 #endif
+#undef malloc
+     
+#include <sys/types.h>
+
+void *malloc ();
+
+/* Allocate an N-byte block of memory from the heap.
+   If N is zero, allocate a 1-byte block.  */
+    
+void* rpl_malloc (size_t n)
+{
+  if (n == 0)
+    n = 1;
+  return malloc (n);
+}
 
 #ifdef _HAVE_STDC_HEADERS
 #include <string.h>

diff -NurB --strip-trailing-cr --suppress-common-lines src/stream_template.c src/stream_template.c
--- src/stream_template.c	2017-07-24 10:05:05.000000000 +0000
+++ src/stream_template.c	2017-07-24 10:06:46.000000000 +0000
@@ -28,6 +28,21 @@
 #ifdef HAVE_CONFIG_H
 #include "config.h"
 #endif
+#undef malloc
+     
+#include <sys/types.h>
+
+void *malloc ();
+
+/* Allocate an N-byte block of memory from the heap.
+   If N is zero, allocate a 1-byte block.  */
+    
+void* rpl_malloc (size_t n)
+{
+  if (n == 0)
+    n = 1;
+  return malloc (n);
+}
 
 #ifdef _HAVE_STDC_HEADERS
 #include <string.h>
 
EOF
        patch -f -N -i pycrypto-${PYTHON_CRYPTO_VERSION}.patch -p0 

        PYTHONXCPREFIX=${PYTHON_INSTALL_PREFIX} \
        CROSS_COMPILE="${__toolchain}-" \
        CPPFLAGS="${CPPFLAGS} ${PYTHON_CPPFLAGS}" \
        CFLAGS="${CFLAGS} ${PYTHON_CFLAGS}" \
        LDFLAGS="${LDFLAGS} ${PYTHON_LDFLAGS}" \
        LDSHARED="${CC} -shared" \
        ${PYTHON_HOST_COMMAND} setup.py build -x bdist_wheel --plat-name ${PYTHON_WIN_ARCH_SUFFIX}

        popd

        # Install using target python
        PYTHONHOME=${PYTHON_INSTALL_PREFIX} \
        ${__wine_cmd} ${PYTHON_INSTALL_PREFIX}/python.exe \
                    -m pip install "$(winepath -w ${__build_dir}/pycrypto-${PYTHON_CRYPTO_VERSION}/dist/pycrypto-${PYTHON_CRYPTO_VERSION}-cp27-none-${PYTHON_WIN_ARCH_SUFFIX}.whl)" \
        || exit 1

    fi
fi

# ------------------------------------------------------------------------------
# paramiko (paramiko dependency)
# ------------------------------------------------------------------------------
PYTHON_PARAMIKO_VERSION=1.10.1
PYTHON_PARAMIKO_SOURCE_URL=https://pypi.python.org/packages/bc/f0/204504e800922bbfb6fdc8013d07f52bb8b1f84e611e2877806a43d5d129/paramiko-${PYTHON_PARAMIKO_VERSION}.tar.gz

if [ "${PYTHON_PARAMIKO}" == "1" ]; then
    echo "============================== PYTHON_PARAMIKO =============================="
    if [ "${__download}" == "1" ]; then
        download ${PYTHON_PARAMIKO_SOURCE_URL}
    fi

    if [ "${__remove_before_install}" == "1"  ]; then
        # Uninstall using target python
        PYTHONHOME=${PYTHON_INSTALL_PREFIX} \
        ${__wine_cmd} ${PYTHON_INSTALL_PREFIX}/python.exe \
                                    -m pip uninstall -y paramiko
    fi

    if [ "${__install}" == "1" ]; then
        tar xvf ${__download_dir}/paramiko-${PYTHON_PARAMIKO_VERSION}.tar.gz
        pushd ${__build_dir}/paramiko-${PYTHON_PARAMIKO_VERSION}

        PYTHONXCPREFIX=${PYTHON_INSTALL_PREFIX} \
        CROSS_COMPILE="${__toolchain}-" \
        CPPFLAGS="${CPPFLAGS} ${PYTHON_CPPFLAGS}" \
        CFLAGS="${CFLAGS} ${PYTHON_CFLAGS}" \
        LDFLAGS="${LDFLAGS} ${PYTHON_LDFLAGS}" \
        LDSHARED="${CC} -shared" \
        ${PYTHON_HOST_COMMAND} setup.py build -x bdist_wheel

        popd

        # Install using target python
        PYTHONHOME=${PYTHON_INSTALL_PREFIX} \
        ${__wine_cmd} ${PYTHON_INSTALL_PREFIX}/python.exe \
                    -m pip install "$(winepath -w ${__build_dir}/paramiko-${PYTHON_PARAMIKO_VERSION}/dist/paramiko-${PYTHON_PARAMIKO_VERSION}-py2-none-any.whl)" \
        || exit 1

    fi
fi

# ------------------------------------------------------------------------------
# pyro (pyro dependency)
# ------------------------------------------------------------------------------
PYTHON_PYRO_VERSION=3.14
PYTHON_PYRO_SOURCE_URL=https://pypi.python.org/packages/a1/af/50ca721bc031329be3ffda0a26d4079bf705437c0ec8d6b312acf3146396/Pyro-${PYTHON_PYRO_VERSION}.tar.gz

if [ "${PYTHON_PYRO}" == "1" ]; then
    echo "============================== PYTHON_PYRO =============================="
    if [ "${__download}" == "1" ]; then
        download ${PYTHON_PYRO_SOURCE_URL}
    fi

    if [ "${__remove_before_install}" == "1"  ]; then
        # Uninstall using target python
        PYTHONHOME=${PYTHON_INSTALL_PREFIX} \
        ${__wine_cmd} ${PYTHON_INSTALL_PREFIX}/python.exe \
                                    -m pip uninstall -y pyro
    fi

    if [ "${__install}" == "1" ]; then
        tar xvf ${__download_dir}/Pyro-${PYTHON_PYRO_VERSION}.tar.gz
        pushd ${__build_dir}/Pyro-${PYTHON_PYRO_VERSION}

        # Generate patch to build shared library
        cat << EOF > pyro-${PYTHON_PYRO_VERSION}.patch
diff -NurB --strip-trailing-cr --suppress-common-lines setup.py setup.py
--- setup.py	2016-12-07 11:37:12.494680476 +0100
+++ setup.py	2016-12-07 11:39:03.698729172 +0100
@@ -3,7 +3,19 @@
 # Pyro setup script
 #
 
-from distutils.core import setup
+try:
+    from wheel import pep425tags
+except ImportError:
+    pass
+else:
+    pep425tags.get_abi_tag = lambda: 'none'
+
+try:
+	from setuptools import setup
+	
+except ImportError:
+	from distutils.core import setup
+    
 import sys,os,glob
 import sets

EOF
        patch -f -N -i pyro-${PYTHON_PYRO_VERSION}.patch -p0 

        PYTHONXCPREFIX=${PYTHON_INSTALL_PREFIX} \
        CROSS_COMPILE="${__toolchain}-" \
        CPPFLAGS="${CPPFLAGS} ${PYTHON_CPPFLAGS}" \
        CFLAGS="${CFLAGS} ${PYTHON_CFLAGS}" \
        LDFLAGS="${LDFLAGS} ${PYTHON_LDFLAGS}" \
        LDSHARED="${CC} -shared" \
        ${PYTHON_HOST_COMMAND} setup.py build -x bdist_wheel

        popd

        # Install using target python
        PYTHONHOME=${PYTHON_INSTALL_PREFIX} \
        ${__wine_cmd} ${PYTHON_INSTALL_PREFIX}/python.exe \
                    -m pip install "$(winepath -w ${__build_dir}/Pyro-${PYTHON_PYRO_VERSION}/dist/pyro-${PYTHON_PYRO_VERSION}-py2-none-any.whl)" \
        || exit 1

        # Add links to python scripts
        pushd ${CROSSBUILD_INSTALL_PREFIX}/bin
        ln -fs ../python/Scripts/pyro-* \
               ./
        popd
    fi
fi

# ------------------------------------------------------------------------------
# pil (pil dependency)
# ------------------------------------------------------------------------------
PYTHON_PIL_VERSION=2.3.0
PYTHON_PIL_SOURCE_URL=https://pypi.python.org/packages/e2/20/f847c81607349a0e4451dc9f854c3b7f09cb4dce70edd366985bedc13208/Pillow-${PYTHON_PIL_VERSION}-cp27-none-${PYTHON_WIN_ARCH_SUFFIX}.whl

if [ "${PYTHON_PIL}" == "1" ]; then
    echo "============================== PYTHON_PIL =============================="
    if [ "${__download}" == "1" ]; then
        download "${__arch}" ${PYTHON_PIL_SOURCE_URL}
    fi

    if [ "${__remove_before_install}" == "1"  ]; then
        # Uninstall using target python
        PYTHONHOME=${PYTHON_INSTALL_PREFIX} \
        ${__wine_cmd} ${PYTHON_INSTALL_PREFIX}/python.exe \
                                    -m pip uninstall -y Pillow
    fi

    if [ "${__install}" == "1" ]; then
 
        # Install using target python
        PYTHONHOME=${PYTHON_INSTALL_PREFIX} \
        ${__wine_cmd} ${PYTHON_INSTALL_PREFIX}/python.exe \
                    -m pip install "$(winepath -w ${__download_dir}/Pillow-${PYTHON_PIL_VERSION}-cp27-none-${PYTHON_WIN_ARCH_SUFFIX}.whl)" \
        || exit 1

        # Add links to python scripts
        pushd ${CROSSBUILD_INSTALL_PREFIX}/bin
        ln -fs ../python/Scripts/pilconvert.py \
               ../python/Scripts/pildriver.py \
               ../python/Scripts/pilfile.py \
               ../python/Scripts/pilfont.py \
               ../python/Scripts/pilprint.py \
               ./
        popd
    fi

    if [ "${__fix_python_scripts}" == "1" ]; then
        for __script in pilconvert.py pildriver.py pilfile.py pilfont.py pilprint.py; do
            fix_python_script ${PYTHON_INSTALL_PREFIX}/Scripts/${__script}
        done
    fi
fi

# ------------------------------------------------------------------------------
# pydicom (pydicom dependency)
# ------------------------------------------------------------------------------
PYTHON_DICOM_VERSION=0.9.9
PYTHON_DICOM_SOURCE_URL=https://pypi.python.org/packages/5d/1d/dd9716ef3a0ac60c23035a9b333818e34dec2e853733d03f502533af9b84/pydicom-${PYTHON_DICOM_VERSION}.tar.gz

if [ "${PYTHON_DICOM}" == "1" ]; then
    echo "============================== PYTHON_DICOM =============================="
    if [ "${__download}" == "1" ]; then
        download ${PYTHON_DICOM_SOURCE_URL}
    fi

    if [ "${__remove_before_install}" == "1"  ]; then
        # Uninstall using target python
        PYTHONHOME=${PYTHON_INSTALL_PREFIX} \
        ${__wine_cmd} ${PYTHON_INSTALL_PREFIX}/python.exe \
                                    -m pip uninstall -y pydicom
    fi

    if [ "${__install}" == "1" ]; then
        tar xvf ${__download_dir}/pydicom-${PYTHON_DICOM_VERSION}.tar.gz
        pushd ${__build_dir}/pydicom-${PYTHON_DICOM_VERSION}

        PYTHONXCPREFIX=${PYTHON_INSTALL_PREFIX} \
        CROSS_COMPILE="${__toolchain}-" \
        CPPFLAGS="${CPPFLAGS} ${PYTHON_CPPFLAGS}" \
        CFLAGS="${CFLAGS} ${PYTHON_CFLAGS}" \
        LDFLAGS="${LDFLAGS} ${PYTHON_LDFLAGS}" \
        LDSHARED="${CC} -shared" \
        ${PYTHON_HOST_COMMAND} setup.py build -x bdist_wheel

        popd

        # Install using target python
        PYTHONHOME=${PYTHON_INSTALL_PREFIX} \
        ${__wine_cmd} ${PYTHON_INSTALL_PREFIX}/python.exe \
                    -m pip install "$(winepath -w ${__build_dir}/pydicom-${PYTHON_DICOM_VERSION}/dist/pydicom-${PYTHON_DICOM_VERSION}-py2-none-any.whl)" \
        || exit 1

    fi
fi

# ------------------------------------------------------------------------------
# pyyaml (pyyaml dependency)
# ------------------------------------------------------------------------------
PYTHON_YAML_VERSION=3.10
PYTHON_YAML_SOURCE_URL=https://pypi.python.org/packages/00/17/3b822893a1789a025d3f676a381338516a8f65e686d915b0834ecc9b4979/PyYAML-${PYTHON_YAML_VERSION}.tar.gz
PYTHON_YAML_DEPENDENCIES="yaml"
if [ "${PYTHON_YAML}" == "1" ]; then
    echo "============================== PYTHON_YAML =============================="
    if [ "${__download}" == "1" ]; then
        download ${PYTHON_YAML_SOURCE_URL}
    fi

    if [ "${__remove_before_install}" == "1"  ]; then
        # Uninstall using target python
        PYTHONHOME=${PYTHON_INSTALL_PREFIX} \
        ${__wine_cmd} ${PYTHON_INSTALL_PREFIX}/python.exe \
                                    -m pip uninstall -y pyyaml
    fi

    if [ "${__install}" == "1" ]; then
        tar xvf ${__download_dir}/PyYAML-${PYTHON_YAML_VERSION}.tar.gz
        pushd ${__build_dir}/PyYAML-${PYTHON_YAML_VERSION}

        # Generate patch to build shared library
        cat << EOF > python-yaml-${PYTHON_YAML_VERSION}.patch
diff -NurB --strip-trailing-cr --suppress-common-lines setup.py setup.py
--- setup.py    2017-01-23 17:40:41.267444147 +0100
+++ setup.py    2017-01-23 17:42:30.255593067 +0100
@@ -60,9 +60,34 @@
 
 
 import sys, os.path
+    
 
 from distutils import log
-from distutils.core import setup, Command
+
+try:
+    from wheel import pep425tags
+except ImportError:
+    pass
+else:
+    pep425tags.get_abi_tag = lambda: 'none'
+
+try:
+   from setuptools import setup, Command
+   
+except ImportError:
+   from distutils.core import setup, Command
+   
+from distutils import sysconfig
+def _init_posix():
+    """Initialize the module as appropriate for POSIX systems."""
+    # _sysconfigdata is generated at build time, see the sysconfig module
+    from _sysconfigdata import build_time_vars
+    sysconfig._config_vars = {}
+    sysconfig._config_vars.update(build_time_vars)
+    sysconfig._config_vars['SO'] = '.pyd'
+    sysconfig._config_vars['EXE'] = '.exe'
+
+sysconfig._init_posix = _init_posix
 from distutils.core import Distribution as _Distribution
 from distutils.core import Extension as _Extension
 from distutils.dir_util import mkpath

diff -NurB --strip-trailing-cr --suppress-common-lines setup.cfg setup.cfg
--- setup.cfg   2017-01-25 12:00:03.489964830 +0100
+++ setup.cfg   2017-01-25 12:01:02.393979263 +0100
@@ -4,10 +4,10 @@
 [build_ext]
 
 # List of directories to search for 'yaml.h' (separated by ':').
-#include_dirs=/usr/local/include:../../include
+include_dirs=${YAML_INSTALL_PREFIX}/include
 
 # List of directories to search for 'libyaml.a' (separated by ':').
-#library_dirs=/usr/local/lib:../../lib
+library_dirs=${YAML_INSTALL_PREFIX}/lib
 
 # An alternative compiler to build the extention.
 #compiler=mingw32

EOF

        patch -f -N -i python-yaml-${PYTHON_YAML_VERSION}.patch -p0 
        
        PYTHONXCPREFIX=${PYTHON_INSTALL_PREFIX} \
        CROSS_COMPILE="${__toolchain}-" \
        CPPFLAGS="${CPPFLAGS} ${PYTHON_CPPFLAGS} $(get_c_flags ${PYTHON_YAML_DEPENDENCIES})" \
        CFLAGS="${CFLAGS} ${PYTHON_CFLAGS} $(get_c_flags ${PYTHON_YAML_DEPENDENCIES})" \
        LDFLAGS="${LDFLAGS} ${PYTHON_LDFLAGS} $(get_link_flags ${PYTHON_YAML_DEPENDENCIES})" \
        LDSHARED="${CC} -shared" \
        ${PYTHON_HOST_COMMAND} setup.py build -x bdist_wheel --plat-name ${PYTHON_WIN_ARCH_SUFFIX}

        popd

        # Install using target python
        PYTHONHOME=${PYTHON_INSTALL_PREFIX} \
        ${__wine_cmd} ${PYTHON_INSTALL_PREFIX}/python.exe \
                    -m pip install "$(winepath -w ${__build_dir}/pyyaml-${PYTHON_YAML_VERSION}/dist/pyyaml-${PYTHON_YAML_VERSION}-cp27-none-${PYTHON_WIN_ARCH_SUFFIX}.whl)" \
        || exit 1

    fi
fi


# ------------------------------------------------------------------------------
# xmltodict
# ------------------------------------------------------------------------------
PYTHON_XMLTODICT_VERSION=0.9.2
PYTHON_XMLTODICT_SOURCE_URL=https://pypi.python.org/packages/source/x/xmltodict/xmltodict-${PYTHON_XMLTODICT_VERSION}.tar.gz
if [ "${PYTHON_XMLTODICT}" == "1" ]; then
    echo "============================== PYTHON_XMLTODICT =============================="
    if [ "${__download}" == "1" ]; then
        download ${PYTHON_XMLTODICT_SOURCE_URL}
    fi

    if [ "${__remove_before_install}" == "1"  ]; then
        # Uninstall using target python
        PYTHONHOME=${PYTHON_INSTALL_PREFIX} \
        ${__wine_cmd} ${PYTHON_INSTALL_PREFIX}/python.exe \
                                    -m pip uninstall -y xmltodict
    fi

    if [ "${__install}" == "1" ]; then
        tar xvf ${__download_dir}/xmltodict-${PYTHON_XMLTODICT_VERSION}.tar.gz
        pushd ${__build_dir}/xmltodict-${PYTHON_XMLTODICT_VERSION}
        
        PYTHONXCPREFIX=${PYTHON_INSTALL_PREFIX} \
        CROSS_COMPILE="${__toolchain}-" \
        CPPFLAGS="${CPPFLAGS} ${PYTHON_CPPFLAGS}" \
        CFLAGS="${CFLAGS} ${PYTHON_CFLAGS}" \
        LDFLAGS="${LDFLAGS} ${PYTHON_LDFLAGS}" \
        LDSHARED="${CC} -shared" \
        ${PYTHON_HOST_COMMAND} setup.py build -x bdist_wheel
        
        popd

        # Install using target python
        PYTHONHOME=${PYTHON_INSTALL_PREFIX} \
        ${__wine_cmd} ${PYTHON_INSTALL_PREFIX}/python.exe \
                    -m pip install "$(winepath -w ${__build_dir}/xmltodict-${PYTHON_XMLTODICT_VERSION}/dist/xmltodict-${PYTHON_XMLTODICT_VERSION}-py2-none-any.whl)" \
        || exit 1

    fi
fi

# ------------------------------------------------------------------------------
# markupsafe
# ------------------------------------------------------------------------------
PYTHON_MARKUPSAFE_VERSION=0.18
PYTHON_MARKUPSAFE_SOURCE_URL=https://pypi.python.org/packages/98/cf/197c3b0f73224b84eb419a967f87565bcc0b0c1147012397e6bd2d45e253/MarkupSafe-${PYTHON_MARKUPSAFE_VERSION}.tar.gz

if [ "${PYTHON_MARKUPSAFE}" == "1" ]; then
    echo "============================== PYTHON_MARKUPSAFE =============================="
    if [ "${__download}" == "1" ]; then
        download ${PYTHON_MARKUPSAFE_SOURCE_URL}
    fi

    if [ "${__remove_before_install}" == "1"  ]; then
        # Uninstall using target python
        PYTHONHOME=${PYTHON_INSTALL_PREFIX} \
        ${__wine_cmd} ${PYTHON_INSTALL_PREFIX}/python.exe \
                                    -m pip uninstall -y markupsafe
    fi

    if [ "${__install}" == "1" ]; then
        tar xvf ${__download_dir}/MarkupSafe-${PYTHON_MARKUPSAFE_VERSION}.tar.gz
        pushd ${__build_dir}/MarkupSafe-${PYTHON_MARKUPSAFE_VERSION}

        # Generate patch to build shared library
        cat << EOF > python-markupsafe-${PYTHON_MARKUPSAFE_VERSION}.patch
diff -NurB --strip-trailing-cr --suppress-common-lines setup.py setup.py
--- setup.py    2017-05-10 16:14:50.787989247 +0200
+++ setup.py    2017-05-10 16:16:51.703932394 +0200
@@ -1,6 +1,27 @@
 import os
 import sys
+
+try:
+    from wheel import pep425tags
+except ImportError:
+    pass
+else:
+    pep425tags.get_abi_tag = lambda: 'none'
+
 from setuptools import setup, Extension, Feature
+   
+from distutils import sysconfig
+def _init_posix():
+    """Initialize the module as appropriate for POSIX systems."""
+    # _sysconfigdata is generated at build time, see the sysconfig module
+    from _sysconfigdata import build_time_vars
+    sysconfig._config_vars = {}
+    sysconfig._config_vars.update(build_time_vars)
+    sysconfig._config_vars['SO'] = '.pyd'
+    sysconfig._config_vars['EXE'] = '.exe'
+
+sysconfig._init_posix = _init_posix
+
 from distutils.command.build_ext import build_ext
 from distutils.errors import CCompilerError, DistutilsExecError, \\
     DistutilsPlatformError

EOF

        patch -f -N -i python-markupsafe-${PYTHON_MARKUPSAFE_VERSION}.patch -p0 

        
        PYTHONXCPREFIX=${PYTHON_INSTALL_PREFIX} \
        CROSS_COMPILE="${__toolchain}-" \
        CPPFLAGS="${CPPFLAGS} ${PYTHON_CPPFLAGS}" \
        CFLAGS="${CFLAGS} ${PYTHON_CFLAGS}" \
        LDFLAGS="${LDFLAGS} ${PYTHON_LDFLAGS}" \
        LDSHARED="${CC} -shared" \
        ${PYTHON_HOST_COMMAND} setup.py build -x bdist_wheel --plat-name ${PYTHON_WIN_ARCH_SUFFIX}
        
        popd

        # Install using target python
        PYTHONHOME=${PYTHON_INSTALL_PREFIX} \
        ${__wine_cmd} ${PYTHON_INSTALL_PREFIX}/python.exe \
                    -m pip install "$(winepath -w ${__build_dir}/markupsafe-${PYTHON_MARKUPSAFE_VERSION}/dist/markupsafe-${PYTHON_MARKUPSAFE_VERSION}-cp27-none-${PYTHON_WIN_ARCH_SUFFIX}.whl)" \
        || exit 1

    fi
fi

# ------------------------------------------------------------------------------
# jinja2
# ------------------------------------------------------------------------------
PYTHON_JINJA2_VERSION=2.7.2
PYTHON_JINJA2_SOURCE_URL=https://pypi.python.org/packages/23/94/ca42176bf7a252ce1f5d165953013573dffdbe4b5dac07f57146146ea432/Jinja2-${PYTHON_JINJA2_VERSION}.tar.gz

if [ "${PYTHON_JINJA2}" == "1" ]; then
    echo "============================== PYTHON_JINJA2 =============================="
    if [ "${__download}" == "1" ]; then
        download ${PYTHON_JINJA2_SOURCE_URL}
    fi

    if [ "${__remove_before_install}" == "1"  ]; then
        # Uninstall using target python
        PYTHONHOME=${PYTHON_INSTALL_PREFIX} \
        ${__wine_cmd} ${PYTHON_INSTALL_PREFIX}/python.exe \
                                    -m pip uninstall -y jinja2
    fi

    if [ "${__install}" == "1" ]; then
        tar xvf ${__download_dir}/Jinja2-${PYTHON_JINJA2_VERSION}.tar.gz
        pushd ${__build_dir}/Jinja2-${PYTHON_JINJA2_VERSION}

        PYTHONXCPREFIX=${PYTHON_INSTALL_PREFIX} \
        CROSS_COMPILE="${__toolchain}-" \
        CPPFLAGS="${CPPFLAGS} ${PYTHON_CPPFLAGS}" \
        CFLAGS="${CFLAGS} ${PYTHON_CFLAGS}" \
        LDFLAGS="${LDFLAGS} ${PYTHON_LDFLAGS}" \
        LDSHARED="${CC} -shared" \
        ${PYTHON_HOST_COMMAND} setup.py build -x bdist_wheel
        
        popd

        # Install using target python
        PYTHONHOME=${PYTHON_INSTALL_PREFIX} \
        ${__wine_cmd} ${PYTHON_INSTALL_PREFIX}/python.exe \
                    -m pip install "$(winepath -w ${__build_dir}/jinja2-${PYTHON_JINJA2_VERSION}/dist/jinja2-${PYTHON_JINJA2_VERSION}-py2-none-any.whl)" \
        || exit 1

    fi
fi

# ------------------------------------------------------------------------------
# pygments
# ------------------------------------------------------------------------------
PYTHON_PYGMENTS_VERSION=1.6
PYTHON_PYGMENTS_SOURCE_URL=https://pypi.python.org/packages/e8/90/992eb125901873d81440480a7cf40a40aa5f8b2e41a67fbc568db6c21595/Pygments-${PYTHON_PYGMENTS_VERSION}.tar.gz

if [ "${PYTHON_PYGMENTS}" == "1" ]; then
    echo "============================== PYTHON_PYGMENTS =============================="
    if [ "${__download}" == "1" ]; then
        download ${PYTHON_PYGMENTS_SOURCE_URL}
    fi

    if [ "${__remove_before_install}" == "1"  ]; then
        # Uninstall using target python
        PYTHONHOME=${PYTHON_INSTALL_PREFIX} \
        ${__wine_cmd} ${PYTHON_INSTALL_PREFIX}/python.exe \
                                    -m pip uninstall -y pygments
    fi

    if [ "${__install}" == "1" ]; then
        tar xvf ${__download_dir}/Pygments-${PYTHON_PYGMENTS_VERSION}.tar.gz
        pushd ${__build_dir}/Pygments-${PYTHON_PYGMENTS_VERSION}
        
        PYTHONXCPREFIX=${PYTHON_INSTALL_PREFIX} \
        CROSS_COMPILE="${__toolchain}-" \
        CPPFLAGS="${CPPFLAGS} ${PYTHON_CPPFLAGS}" \
        CFLAGS="${CFLAGS} ${PYTHON_CFLAGS}" \
        LDFLAGS="${LDFLAGS} ${PYTHON_LDFLAGS}" \
        LDSHARED="${CC} -shared" \
        ${PYTHON_HOST_COMMAND} setup.py build -x bdist_wheel
        
        popd

        # Install using target python
        PYTHONHOME=${PYTHON_INSTALL_PREFIX} \
        ${__wine_cmd} ${PYTHON_INSTALL_PREFIX}/python.exe \
                    -m pip install "$(winepath -w ${__build_dir}/pygments-${PYTHON_PYGMENTS_VERSION}/dist/pygments-${PYTHON_PYGMENTS_VERSION}-py2-none-any.whl)" \
        || exit 1

        # Add links to python scripts
        pushd ${CROSSBUILD_INSTALL_PREFIX}/bin
        ln -fs ../python/Scripts/pygmentize.exe \
               ./
        popd
    fi

    if [ "${__fix_python_scripts}" == "1" ]; then
        for __script in pygmentize.exe; do
            fix_python_script ${PYTHON_INSTALL_PREFIX}/Scripts/${__script}
        done
    fi
fi

# ------------------------------------------------------------------------------
# docutils
# ------------------------------------------------------------------------------
PYTHON_DOCUTILS_VERSION=0.11
PYTHON_DOCUTILS_SOURCE_URL=https://pypi.python.org/packages/7f/49/3ff69dcb212900199462a291886e2f30f57ab3a69dc88e31eda6404a17c0/docutils-${PYTHON_DOCUTILS_VERSION}.tar.gz

if [ "${PYTHON_DOCUTILS}" == "1" ]; then
    echo "============================== PYTHON_DOCUTILS =============================="
    if [ "${__download}" == "1" ]; then
        download ${PYTHON_DOCUTILS_SOURCE_URL}
    fi

    if [ "${__remove_before_install}" == "1"  ]; then
        # Uninstall using target python
        PYTHONHOME=${PYTHON_INSTALL_PREFIX} \
        ${__wine_cmd} ${PYTHON_INSTALL_PREFIX}/python.exe \
                                    -m pip uninstall -y docutils
    fi

    if [ "${__install}" == "1" ]; then
        tar xvf ${__download_dir}/docutils-${PYTHON_DOCUTILS_VERSION}.tar.gz
        pushd ${__build_dir}/docutils-${PYTHON_DOCUTILS_VERSION}

        # Generate patch to build shared library
        cat << EOF > python-docutils-${PYTHON_DOCUTILS_VERSION}.patch
diff -NurB --strip-trailing-cr --suppress-common-lines setup.py setup.py
--- setup.py    2017-05-10 16:53:44.599132351 +0200
+++ setup.py    2017-05-10 16:57:59.155051362 +0200
@@ -5,8 +5,33 @@
 import sys
 import os
 import glob
+
 try:
+    from wheel import pep425tags
+except ImportError:
+    pass
+else:
+    pep425tags.get_abi_tag = lambda: 'none'
+
+try:
+    from setuptools import setup, Command
+
+except ImportError:
     from distutils.core import setup, Command
+    
+from distutils import sysconfig
+def _init_posix():
+    """Initialize the module as appropriate for POSIX systems."""
+    # _sysconfigdata is generated at build time, see the sysconfig module
+    from _sysconfigdata import build_time_vars
+    sysconfig._config_vars = {}
+    sysconfig._config_vars.update(build_time_vars)
+    sysconfig._config_vars['SO'] = '.pyd'
+    sysconfig._config_vars['EXE'] = '.exe'
+
+sysconfig._init_posix = _init_posix
+
+try:
     from distutils.command.build import build
     from distutils.command.build_py import build_py
     if sys.version_info >= (3,):

EOF

        patch -f -N -i python-docutils-${PYTHON_DOCUTILS_VERSION}.patch -p0 

        
        PYTHONXCPREFIX=${PYTHON_INSTALL_PREFIX} \
        CROSS_COMPILE="${__toolchain}-" \
        CPPFLAGS="${CPPFLAGS} ${PYTHON_CPPFLAGS}" \
        CFLAGS="${CFLAGS} ${PYTHON_CFLAGS}" \
        LDFLAGS="${LDFLAGS} ${PYTHON_LDFLAGS}" \
        LDSHARED="${CC} -shared" \
        ${PYTHON_HOST_COMMAND} setup.py build -x bdist_wheel
        
        popd

        # Install using target python
        PYTHONHOME=${PYTHON_INSTALL_PREFIX} \
        ${__wine_cmd} ${PYTHON_INSTALL_PREFIX}/python.exe \
                    -m pip install "$(winepath -w ${__build_dir}/docutils-${PYTHON_DOCUTILS_VERSION}/dist/docutils-${PYTHON_DOCUTILS_VERSION}-py2-none-any.whl)" \
        || exit 1

        # Add links to python scripts
        pushd ${CROSSBUILD_INSTALL_PREFIX}/bin
        ln -fs ../python/Scripts/rst2-*.py \
               ./
        popd
    fi
fi

# ------------------------------------------------------------------------------
# sphinx
# ------------------------------------------------------------------------------
PYTHON_SPHINX_VERSION=1.2.2
PYTHON_SPHINX_SOURCE_URL=https://pypi.python.org/packages/ff/91/edcbcd8126333cf69493fc2a0f1663ffef26d267024125ffd7bd50137bdb/Sphinx-${PYTHON_SPHINX_VERSION}-py27-none-any.whl

if [ "${PYTHON_SPHINX}" == "1" ]; then
    echo "============================== PYTHON_SPHINX =============================="
    if [ "${__download}" == "1" ]; then
        download ${PYTHON_SPHINX_SOURCE_URL}
    fi

    if [ "${__remove_before_install}" == "1"  ]; then
        # Uninstall using target python
        PYTHONHOME=${PYTHON_INSTALL_PREFIX} \
        ${__wine_cmd} ${PYTHON_INSTALL_PREFIX}/python.exe \
                                    -m pip uninstall -y sphinx
    fi

    if [ "${__install}" == "1" ]; then
        # Install using target python
        PYTHONHOME=${PYTHON_INSTALL_PREFIX} \
        ${__wine_cmd} ${PYTHON_INSTALL_PREFIX}/python.exe \
                    -m pip install "$(winepath -w ${__download_dir}/sphinx-${PYTHON_SPHINX_VERSION}-py27-none-any.whl)" \
        || exit 1

        # Add links to python scripts
        pushd ${CROSSBUILD_INSTALL_PREFIX}/bin
        ln -fs ../python/Scripts/sphinx-apidoc.exe \
               ../python/Scripts/sphinx-autogen.exe \
               ../python/Scripts/sphinx-build.exe \
               ../python/Scripts/sphinx-quickstart.exe \
               ./
        popd
    fi

    if [ "${__fix_python_scripts}" == "1" ]; then
        for __script in sphinx-apidoc.exe sphinx-autogen.exe sphinx-build.exe sphinx-quickstart.exe; do
            fix_python_script ${PYTHON_INSTALL_PREFIX}/Scripts/${__script}
        done
    fi
fi

popd

# ------------------------------------------------------------------------------
# Unset local variables
# ------------------------------------------------------------------------------
unset __arch
unset __toolchain
unset __buildtype
unset __build_proc_num
unset __download
unset __remove_before_install
unset __install
unset __mirror_url
unset __use_cea_mirror
unset __cea_mirror_version
unset __tmp_dir
unset __build_dir
unset __download_dir
