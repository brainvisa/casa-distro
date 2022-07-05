# -*- coding: utf-8 -*-

'''
This GUI should run inside the container. It is typically started by the
`bv`command on host side, which runs it inside the container.
'''

from __future__ import print_function

import sys
import json
import subprocess
import os
import collections
import glob
import os.path as osp
import shutil
import tempfile

try:
    from soma.qt_gui.qt_backend import Qt
    from soma.qt_gui.qt_backend.QtCore import Signal
    try:
        from soma.qt_gui.qt_backend import QtWebEngineWidgets
    except Exception:
        print('QtWebEngineWidgets cannot be imported.')
except ImportError:
    try:
        from PyQt5 import Qt
        from PyQt5.QtCore import pyqtSignal as Signal
    except ImportError:
        from PyQt4 import Qt
        from PyQt4.QtCore import pyqtSignal as Signal
    if not Qt.QApplication.instance():
        app = Qt.QApplication(sys.argv)
    Qt.QMessageBox.warning(
        None, 'Problem',
        'soma-base is not installed.\n'
        'Either you are running this program outside of a Casa-Distro '
        'container, which is not the way it is designed to run, or soma-base '
        'is not properly built / installed in the container. This may happen '
        'in a developer container before its first build.\n\n'
        'As a result, some configuration edition capabilities will not be '
        'available.\n\n'
        'You normally just run the "bv" script from the host.')

from casa_distro.container_environment import (is_writable,
                                               user_config_filename)
from casa_distro.environment import update_config


class InstallEditor(Qt.QDialog):
    def __init__(self, conf, conf_path, parent=None):
        super(InstallEditor, self).__init__(parent)

        self.conf = conf
        self.conf_path = conf_path
        self.url = ''

        layout = Qt.QVBoxLayout()
        self.setLayout(layout)
        self.setWindowTitle('BrainVISA Install options')

        cinstl = Qt.QHBoxLayout()
        layout.addLayout(cinstl)

        inst_type = 'None'
        if (os.path.exists('/casa/host/install/bin/bv_env')
                or (os.path.exists('/casa/install/bin/bv_env')
                    and is_writable('/casa/install'))):
            inst_type = '<font color="#008000">read-write</font>'
        elif os.path.exists('/casa/install/bin/bv_env'):
            inst_type = '<font color="#800000">read-only</font>'
        dist_text = ''
        if inst_type != 'None':
            distro = self.conf['distro']
            dist_text = ' (<b>%s</b>)' % distro

        cinst0 = Qt.QLabel('<b>Current install:</b> %s%s'
                           % (inst_type, dist_text))
        cinstl.addWidget(cinst0)

        if 'read-only' in inst_type:
            inst_rwl = Qt.QGroupBox('install read-write locally:')
            layout.addWidget(inst_rwl)
            inst_rwl_l = Qt.QVBoxLayout()
            inst_rwl.setLayout(inst_rwl_l)
            self.unpack_btn = Qt.QCheckBox('install from internal image')
            inst_rwl_l.addWidget(self.unpack_btn)

        dl_grp = Qt.QGroupBox('install toolboxes from downloads:')
        self.dl_grp = dl_grp
        layout.addWidget(dl_grp)
        dl_grp_l = Qt.QVBoxLayout()
        dl_grp.setLayout(dl_grp_l)
        if 'read-only' in inst_type:
            self.prereq_warn = Qt.QLabel(
                'Install from internal image must be checked\n'
                'before additional toolboxes can be installed')
            dl_grp_l.addWidget(self.prereq_warn)
        self.dl_wid = Qt.QWidget()
        dl_grp_l.addWidget(self.dl_wid)
        hb = Qt.QGridLayout()
        hb.setContentsMargins(0, 0, 0, 0)
        self.dl_wid.setLayout(hb)
        hb.addWidget(Qt.QLabel('url:'), 0, 0)
        self.url_edit = Qt.QLineEdit('https://brainvisa.info/download')
        hb.addWidget(self.url_edit, 0, 1)
        hb.addWidget(Qt.QLabel('distro:'), 1, 0)
        self.distros = Qt.QListWidget()
        hb.addWidget(self.distros, 1, 1)
        self.distros.setSelectionMode(self.distros.ExtendedSelection)
        self.url_edit.editingFinished.connect(self.url_changed)

        if 'read-only' in inst_type:
            self.dl_wid.hide()
            self.dl_grp.setEnabled(False)
        else:
            self.update_distros()

        layout.addStretch(1)

        validation_btns = Qt.QDialogButtonBox(
            Qt.QDialogButtonBox.Ok | Qt.QDialogButtonBox.Cancel
            | Qt.QDialogButtonBox.Help)
        layout.addWidget(validation_btns)
        validation_btns.button(Qt.QDialogButtonBox.Ok).setDefault(False)
        validation_btns.button(Qt.QDialogButtonBox.Ok).setAutoDefault(False)

        if hasattr(self, 'unpack_btn'):
            self.unpack_btn.toggled.connect(self.local_install_checked)
        validation_btns.accepted.connect(self.accept)
        validation_btns.rejected.connect(self.reject)
        validation_btns.helpRequested.connect(self.help)
        self.validation_btns = validation_btns

    def url_changed(self):
        self.update_distros()

    def local_install_checked(self, checked):
        if checked:
            self.prereq_warn.hide()
            self.dl_wid.show()
            self.dl_grp.setEnabled(True)
            self.update_distros()
        else:
            self.dl_wid.hide()
            self.prereq_warn.show()
            self.dl_grp.setEnabled(False)

    def update_distros(self):
        from casa_distro.web import url_listdir, urlopen

        url = self.url_edit.text()
        if self.url == url:
            return

        self.url = url

        sel_distros = [item.text() for item in self.distros.selectedItems()]
        self.distros.clear()

        try:
            items = url_listdir(osp.join(url, self.conf['version']))
            for distro in items:
                if distro.endswith('/'):
                    distro = distro[:-1]
                ditem = osp.join(url, self.conf['version'], distro,
                                 self.conf['system'])
                dzip = osp.join(ditem,
                                '%s-%s-%s' % (distro, self.conf['version'],
                                              self.conf['system']))
                djson = '%s.json' % dzip
                if urlopen(djson) and urlopen(dzip):
                    self.distros.addItem(distro)
                    if distro in sel_distros:
                        self.distros.item(
                            self.distros.count() - 1).setSelected(True)

        except Exception:
            pass

    def accept(self):
        from casa_distro.container_environment import setup_user
        import threading

        if not self.validation_btns.button(Qt.QDialogButtonBox.Ok).hasFocus():
            return

        super(InstallEditor, self).accept()

        if hasattr(self, 'unpack_btn') and self.unpack_btn.isChecked():
            do_it = True
            if osp.exists('/casa/host/install'):
                res = Qt.QMessageBox.question(
                    None, 'Erase install ?',
                    'An older installation exists. Erase it ?')
                # print('res:', res)
                if res != Qt.QMessageBox.Yes:
                    do_it = False
                else:
                    shutil.rmtree('/casa/host/install')

            if do_it:
                wait = Qt.QProgressDialog('Installing read-write locally...',
                                          None, 0, 1)
                wait.setWindowTitle('Install in progress')
                wait.setWindowModality(Qt.Qt.WindowModal)
                wait.show()
                wait.setValue(0)
                Qt.QApplication.instance().processEvents()
                thread = threading.Thread(
                    target=setup_user,
                    kwargs=dict(setup_dir='/casa/host', rw_install=True))
                thread.start()
                while thread.is_alive():
                    thread.join(0.1)
                    Qt.QApplication.instance().processEvents()
                wait.setValue(1)
                Qt.QApplication.instance().processEvents()
                wait.close()
                del wait

        distros = [item.text() for item in self.distros.selectedItems()]
        if distros:
            wait = Qt.QProgressDialog('Installing read-write from download...',
                                      'Cancel', 0, len(distros))
            wait.setWindowTitle('Install in progress')
            if len(distros) == 1:
                # cannot cancel inside a single install
                wait.setCancelButton(None)
            wait.setWindowModality(Qt.Qt.WindowModal)
            wait.show()
            Qt.QApplication.instance().processEvents()
            url = self.url_edit.text()
            installed = []
            cancel_done = False
            for n, distro in enumerate(distros):
                wait.setLabelText('installing distro: <b>%s</b>' % distro)
                Qt.QApplication.instance().processEvents()
                wait.setValue(n)
                Qt.QApplication.instance().processEvents()
                if wait.wasCanceled():
                    print('Cancel.')
                    break
                thread = threading.Thread(
                    target=setup_user,
                    kwargs=dict(setup_dir='/casa/host', distro=distro,
                                url=url))
                thread.start()
                while thread.is_alive():
                    if wait.wasCanceled():
                        if not cancel_done:
                            print('cancelling after the current install '
                                  '(which cannot be interrupted)...')
                            wait.setLabelText(
                                '<b>Cancelling....</b> finishing to install '
                                '<br/><b>%s</b> (not interruptible) first...'
                                % distro)
                            wait.setCancelButton(None)
                            wait.show()
                            Qt.QApplication.instance().processEvents()
                            cancel_done = True
                    thread.join(0.1)
                    Qt.QApplication.instance().processEvents()
                installed.append(distro)
            wait.setValue(n)
            Qt.QApplication.instance().processEvents()
            wait.close()
            del wait
            if self.conf['distro'] not in installed or len(installed) != 1:
                print('distro has changed.')
                self.conf['distro'] = 'custom'
                with open(self.conf_path) as f:
                    new_conf = json.load(f)
                new_conf['distro'] = 'custom'
                with open(self.conf_path, 'w') as f:
                    json.dump(new_conf, f, indent=4)

    def help(self):
        print('help')
        try:
            self.help_widget = QtWebEngineWidgets.QWebEngineView()
        except Exception:
            print('QWebEngineView failed, using QWebView')
            self.help_widget = Qt.QWebView()
        self.help_widget.setWindowTitle('Managing install')
        help_text = '''<style>
body {
    font-family: sans-serif;
    border-width: 10px;
    border-color: #8880A0;
    border-style: solid;
    border-radius: 6px;
    margin: 0px;
    padding: 10px;
    text-align: justify;
}

a {
    color: #2878A2;
    text-decoration: none;
}

a:hover {
    text-decoration: underline;
}
h1 {
    background-color: #C8D0EF;
    border-style: none;
    border-width: 0px;
    border-radius: 8px;
    padding: 10px;
    margin: -10px;
    margin-bottom: 0px;
    color: #2878A2;
}

h2 {
    background-color: #B0C0EB;
    border-style: none;
    border-width: 0px;
    border-radius: 8px;
    padding: 5px;
}

div.note {
    background-color: #f0f0ff;
    border-style: solid;
    border-width: 1px;
    border-radius: 4px;
    padding: 5px;
}

div.code {
    background-color: #f0fff0;
    border-style: solid none solid none;
    border-width: 1px;
    border-radius: 0px;
    padding: 3px;
    border-color: #d0d090;
}
</style>
<h1>Managing BrainVISA installation options</h1>

<h2>Different kinds of BrainVISA installations</h2>
<p>The default installation method is using a read-only container image. It is the most convenient, faster to install, and "safe". This is what you get when you download a BrainVisa image and perform the default setup.
</p>
<p>However this install method is not modular: you cannot install additional toolboxes, because the installed files reside inside the container image, which is read-only. Thus it is possible to install BrainVISA on the host filesystem, which will be modifiable, and will allow installing additional tools. <em>This is not needed in a VirtualBox image, where you have a read-write access to the contents.</em> There are two ways to perform the read-write install:
</p>
<p>
    <ul>
        <li>"local" install: the files already present within the already installed, read-only image, will be copied on the host filesystem. You thus get identical contents to the original image, but they will now be modifiable.
        </li>
        <li>from downloads: The BrainVISA programs files will be downloaded from the web site. This method has 2 advantages:
            <ul>
                <li>It can be used from an image which does not contain the files (a "run" system image, without the BrainVISA distribution in it), which is lighter than the full one, and may be shared between several installs.
                </li>
                <li>Downloading offers the option to download a different "distro" (set of packages and toolboxes), and may be used several times over the same install. This is thus a means of installing additional tolboxes when they are available on the web site.
                </li>
            </ul>
            However a network connection has to be active during install, with sufficient bandwidth. Installing the standard "brainvisa" distro from a full "user" image has the same result as the "local" install: it just consumes network bandwidth without any benefit.
        </li>
    </ul>
</p>

<h2>Installing distros</h2>
<p>It is possible to both install the "local" distro (normally the "brainvisa" distro) in read-write mode, then add additional downloaded ones. To do so, check the local install option, and select additional distros.
</p>
<p>Inside the container, the read-only install directory is:
<div class="code">/casa/install</div>
The read-write install location will be:
<div class="code">/casa/host/install</div>
</p>
<div class="note">It is <b>not possible</b> to use the read-only "brainvisa" core distro and install only additional toolboxes in a read-write filesystem. As some tools like the <tt>brainvisa</tt> program, or many python language modules, do not support installation split across several locations. So the main "brainvisa" distro has to be actually reinstalled in another location before toolboxes are installed.
</div>
<p>In the downloads list, the available packages for your container system and version are displayed at the given URL. It could be possible to change the URL to another server which distributes its own distros (toolboxes).
</p>
<p>Several distros can be selected. They will all be installed when "OK" is clicked. There are no dependencies checks between distros/toolboxes, and they will be processed in the order they are displayed to the user, so their installation should be independent.
</p>

'''  # noqa: E501
        self.help_widget.setHtml(help_text)
        self.help_widget.show()


class CasaLauncher(Qt.QDialog):

    def __init__(self, conf_path):
        super(CasaLauncher, self).__init__()
        self.conf_path = conf_path

        with open(conf_path, 'r') as conf_file:
            self.conf = json.load(conf_file)
        self.global_conf = {}

        user_config_file = user_config_filename()
        globc = True  # 1st file is the global conf
        for additional_config_file in [user_config_file] \
            + [c for c in self.conf.get('config_files', [])
               if c != user_config_file]:
            if osp.exists(additional_config_file):
                with open(additional_config_file) as f:
                    added_conf = json.load(f)
                if globc:
                    self.global_conf = added_conf
                else:
                    update_config(self.conf, added_conf)
            globc = False

        self.setup_ui()
        self.setup_links()

    def setup_ui(self):
        self.setWindowTitle('CASA environment configuration')
        self._main_layout = Qt.QVBoxLayout(self)

        env_path = os.environ.get('CASA_HOST_DIR', None)
        if not env_path:
            env_path, _, _ = get_env_path()
            if not env_path:
                env_path = '&lt;none&gt;'
            else:
                env_path = os.path.dirname(env_path)
        self._main_layout.addWidget(Qt.QLabel(
            '<b>environment host path:</b> %s' % env_path))
        self.env_path = env_path
        self._mount_manager = MountManager(self.conf, self.global_conf)

        conf_line = Qt.QHBoxLayout()
        conf_line.addWidget(Qt.QLabel('<b>Configuration:</b>'))
        conf_line.addStretch(1)
        self._conf_btn = Qt.QPushButton('...')
        conf_line.addWidget(self._conf_btn)

        cont_line = None
        if self.conf['container_type'] == 'singularity':
            cont_line = Qt.QHBoxLayout()
            self.container_label = Qt.QLabel()
            self.update_container_status()
            cont_line.addWidget(self.container_label)
            cont_line.addStretch(1)
            self._container_btn = Qt.QPushButton('...')
            cont_line.addWidget(self._container_btn)

        inst_line = None
        if self.conf['type'] in ('run', 'user'):
            inst_line = Qt.QHBoxLayout()
            self.install_label = Qt.QLabel()
            self.update_install_status()
            inst_line.addWidget(self.install_label)
            inst_line.addStretch(1)
            self._inst_btn = Qt.QPushButton('...')
            inst_line.addWidget(self._inst_btn)

        self._launchers = Launchers()

        self._errors_label = Qt.QLabel()

        self._validation_btns = Qt.QDialogButtonBox(
            Qt.QDialogButtonBox.Ok | Qt.QDialogButtonBox.Cancel)

        self._main_layout.addWidget(Qt.QLabel('<b>Mount points:</b>'))
        self._main_layout.addWidget(self._mount_manager)
        self._main_layout.addLayout(conf_line)
        if cont_line:
            self._main_layout.addLayout(cont_line)
        if inst_line:
            self._main_layout.addLayout(inst_line)
        self._main_layout.addWidget(self._launchers)
        self._main_layout.addWidget(self._errors_label)
        self._main_layout.addWidget(self._validation_btns)

    def setup_links(self):
        self._validation_btns.accepted.connect(self.save_conf)
        self._validation_btns.rejected.connect(self.close)
        self._mount_manager.valueChanged.connect(self.block_launchers)
        self._launchers.launched.connect(self.close_and_launch)
        self._conf_btn.clicked.connect(self.edit_configuration)
        if hasattr(self, '_container_btn'):
            self._container_btn.clicked.connect(self.edit_container)
        if hasattr(self, '_inst_btn'):
            self._inst_btn.clicked.connect(self.edit_install)

    def save_conf(self):
        if self._mount_manager.check_all_mounts():
            # print('SAVE')
            conf_wo_mounts = dict(self.conf)
            if 'mounts' in self.conf:
                del conf_wo_mounts['mounts']

            user_config_file = user_config_filename()
            if osp.exists(user_config_file):
                with open(user_config_file) as f:
                    uconf = json.load(f)
            else:
                uconf = {}

            old_umounts = uconf.get('mounts', {})
            if 'mounts' in uconf:
                del uconf['mounts']
            mounts = self._mount_manager.mounts
            for container, hg in mounts.items():
                host, is_global = hg
                if is_global:
                    uconf.setdefault('mounts', {})[container] = host
                else:
                    conf_wo_mounts.setdefault('mounts', {})[container] = host
            try:
                with open(self.conf_path, 'w') as conf_file:
                    json.dump(conf_wo_mounts, conf_file, indent=4)
            except (IOError, OSError):
                # read-only shared environment ?
                pass
            if uconf.get('mounts', {}) != old_umounts:
                if not osp.isdir(osp.dirname(user_config_file)):
                    os.makedirs(osp.dirname(user_config_file))
                with open(user_config_file, 'w') as f:
                    json.dump(uconf, f, indent=4)

            self.accept()

        else:
            # Redondent with errors in MountManager errors
            # Could be used to regroup errors from software conf in the future
            self._errors_label.setText(
                'Mount points are not all set correctly!')

    def close_and_launch(self, command):
        self.close()
        subprocess.check_call(command)

    def block_launchers(self):
        self._launchers.disable_for_reload()

    def edit_configuration(self):
        dialog = Qt.QDialog(self)
        layout = Qt.QVBoxLayout()
        dialog.setLayout(layout)
        config_edit = ConfigEditor(self.conf)
        validation_btns = Qt.QDialogButtonBox(
            Qt.QDialogButtonBox.Ok | Qt.QDialogButtonBox.Cancel)

        layout.addWidget(config_edit)
        layout.addWidget(validation_btns)

        validation_btns.accepted.connect(dialog.accept)
        validation_btns.rejected.connect(dialog.reject)

        preserved = set(['mounts'])
        if dialog.exec_():
            for k in list(self.conf.keys()):
                if k not in preserved:
                    del self.conf[k]
            self.conf.update(config_edit.edited_config())
            self._mount_manager.update_ui()
            self.block_launchers()

    def edit_install(self):
        dialog = InstallEditor(self.conf, self.conf_path, self)
        dialog.setWindowModality(Qt.Qt.WindowModal)
        if dialog.exec_() == dialog.Accepted:
            self.update_install_status()

    def update_install_status(self):
        inst_type = 'None'
        if (os.path.exists('/casa/host/install/bin/bv_env')
                or (os.path.exists('/casa/install/bin/bv_env')
                    and is_writable('/casa/install'))):
            inst_type = '<font color="#008000">read-write</font>'
        elif os.path.exists('/casa/install/bin/bv_env'):
            inst_type = '<font color="#800000">read-only</font>'
        dist_text = ''
        if inst_type != 'None':
            distro = self.conf['distro']
            dist_text = ' (<b>%s</b>)' % distro
        self.install_label.setText(
                '<b>BrainVisa Installation:</b> %s - <b>%s</b> distro'
                % (inst_type, dist_text))

    def update_container_status(self):
        self.container_status = {'write': False,
                                 'allow_write': False,
                                 'overlay': None}
        cont_mode = '<font color="#800000">Read-only</font>'
        if not self.conf['image'].endswith('.sif') \
                and osp.isdir(self.conf['image']):
            self.container_status['write'] = True
            cont_mode = '<font color="#808000">Read-write directory</font>'
            if '-w' not in self.conf.get('container_options', []):
                self.container_status['allow_write'] = True
                cont_mode += (' (open R/O)')
        overlay = osp.join(self.env_path, 'overlay.img')
        if osp.exists(overlay):
            osize = os.stat(overlay).st_size
            self.container_status['overlay'] = osize
            size_str = self.size_string(osize)
            # print(osize)
            cont_mode += ' <font color="#008000">with overlay (%s)</font>' \
                % size_str

        self.container_label.setText('<b>Image: </b> %s' % cont_mode)

    @staticmethod
    def size_string(osize):
        units = ['PB', 'TB', 'GB', 'MB', 'KB', 'B']
        for i in range(len(units)):
            iu = 1024 ** (len(units) - i - 1)
            if osize >= iu:
                ssize = '%d %s' % (int(osize / iu), units[i])
                return ssize
        return '0'  # (strange...)

    def edit_container(self):
        dialog = ContainerImageEditor(self.conf, self.container_status,
                                      self.conf_path, self)
        dialog.setWindowModality(Qt.Qt.WindowModal)
        dialog.exec_()
        self.update_container_status()


class MountManager(Qt.QWidget):

    def __init__(self, conf, global_conf):
        super(MountManager, self).__init__()
        self.conf = conf
        self.global_conf = global_conf
        self.modified = False
        self.mounts = {k: [v, True]
                       for k, v in self.global_conf.get('mounts', {}).items()}
        self.mounts.update(
            {k: [v, False] for k, v in self.conf.get('mounts', {}).items()})

        self._red = Qt.QColor(250, 130, 130)
        self._orange = Qt.QColor(250, 200, 100)

        self.setup_ui()
        self.setup_links()

    valueChanged = Signal()

    def setup_ui(self):
        self._main_layout = Qt.QVBoxLayout(self)

        self._mount_table = Qt.QTableWidget()
        self._mount_table.setColumnCount(3)
        self._mount_table.setRowCount(len(self.mounts))
        self._mount_table.setHorizontalHeaderLabels(['Host', 'Container',
                                                     'Global'])
        self._mount_table.horizontalHeader().setSectionResizeMode(
            0, Qt.QHeaderView.Stretch)
        self._mount_table.horizontalHeader().setSectionResizeMode(
            1, Qt.QHeaderView.Stretch)

        self.update_ui()

        self._error_label = Qt.QLabel()

        self._manager_btns = Qt.QHBoxLayout()
        self._add_mount = Qt.QPushButton('+')
        self._remove_mount = Qt.QPushButton('-')
        self._help_btn = Qt.QPushButton('?')
        self._manager_btns.addStretch(1)
        self._manager_btns.addWidget(self._add_mount)
        self._manager_btns.addWidget(self._remove_mount)
        self._manager_btns.addWidget(self._help_btn)

        self._add_mount.setToolTip('Add a mount point')
        self._remove_mount.setToolTip('Remove selected mount point(s)')
        self._help_btn.setToolTip('Help on how to configure mounts')

        self._main_layout.addWidget(self._mount_table)
        self._main_layout.addWidget(self._error_label)
        self._main_layout.addLayout(self._manager_btns)

    def setup_links(self):
        self._add_mount.clicked.connect(self._add_mount_row)
        self._remove_mount.clicked.connect(self._delete_mount_row)
        self._help_btn.clicked.connect(self._help_mounts)
        self._mount_table.cellChanged.connect(self._value_modified)

    def update_ui(self):
        self._mount_table.clearContents()
        for idx, (container, hostg) in enumerate(self.mounts.items()):
            host, is_global = hostg
            self._mount_table.setItem(idx, 0, Qt.QTableWidgetItem(host))
            self._mount_table.setItem(idx, 1, Qt.QTableWidgetItem(container))
            self._mount_table.item(idx, 0).setData(Qt.Qt.UserRole, container)
            self._mount_table.setItem(idx, 2, Qt.QTableWidgetItem(''))
            if is_global:
                checked = Qt.Qt.Checked
            else:
                checked = Qt.Qt.Unchecked
            self._mount_table.item(idx, 2).setCheckState(checked)

    def _add_mount_row(self):
        if '' in self.mounts:
            Qt.QMessageBox.critical(
                None,
                'Malformed mount point',
                'A mount point has not been assigned a container side '
                'directory. You must define it, or remove the mount point, '
                'before adding a new one')
            return
        host_mount_choice = Qt.QFileDialog(
            None, 'host side directory (in /host)', '/host')
        host_mount_choice.setFileMode(Qt.QFileDialog.Directory)
        if host_mount_choice.exec_():
            self.modified = True
            self.valueChanged.emit()
            self._mount_table.setRowCount(self._mount_table.rowCount() + 1)
            host_path = host_mount_choice.selectedFiles()[0]
            if host_path.startswith('/host/'):
                host_path = host_path[5:]
            self._mount_table.setItem(
                self._mount_table.rowCount() - 1, 0,
                Qt.QTableWidgetItem(host_path))
            self._mount_table.setItem(
                self._mount_table.rowCount() - 1, 1,
                Qt.QTableWidgetItem(''))
            self._mount_table.item(self._mount_table.rowCount() - 1,
                                   0).setData(Qt.Qt.UserRole, '')
            self._mount_table.setItem(
                self._mount_table.rowCount() - 1, 2,
                Qt.QTableWidgetItem(''))
            self._mount_table.item(
                self._mount_table.rowCount() - 1, 2).setCheckState(
                    Qt.Qt.Checked)
            self.mounts[''] = [host_path, True]
            self.check_all_mounts()

    def _delete_mount_row(self):
        if self._mount_table.selectedItems():
            self.modified = True
            self.valueChanged.emit()
            rows = sorted(
                set(item.row() for item in self._mount_table.selectedItems()),
                reverse=True)
            for row in rows:
                host_path = self._mount_table.item(row, 1).text()
                del self.mounts[host_path]
                self._mount_table.removeRow(row)

    def _help_mounts(self):
        try:
            self.help_widget = QtWebEngineWidgets.QWebEngineView()
        except Exception:
            print('QWebEngineView failed, using QWebView')
            self.help_widget = Qt.QWebView()
        self.help_widget.setWindowTitle('How to configure mount points')
        help_text = '''<style>
body {
    font-family: sans-serif;
    border-width: 10px;
    border-color: #8880A0;
    border-style: solid;
    border-radius: 6px;
    margin: 0px;
    padding: 10px;
    text-align: justify;
}

a {
    color: #2878A2;
    text-decoration: none;
}

a:hover {
    text-decoration: underline;
}
h1 {
    background-color: #C8D0EF;
    border-style: none;
    border-width: 0px;
    border-radius: 8px;
    padding: 10px;
    margin: -10px;
    margin-bottom: 0px;
    color: #2878A2;
}

h2 {
    background-color: #B0C0EB;
    border-style: none;
    border-width: 0px;
    border-radius: 8px;
    padding: 5px;
}
</style>
<h1>How to configure mount points</h1>
<p>Mount points allow to see the host system directories from the container. They are needed to read and write files. Some mount points are automatically configured in <b>bv</b> / <b>Casa-Distro</b>, but additional mount points may be added by the user.
</p>

<h2>Automatically configured mount points</h2>
<p>
<ul>
  <li>Environment directory, seen under <tt>/casa/host</tt></li>
  <li>Container-specific home directory, seen under <tt>/casa/home</tt></li>
  <li>Host home directory, normally seen under the same location as on the host machine, typically <tt>/home/johndoe</tt></li>
  <li>Host machine root filesystem (<tt>/</tt>), seen under the directory <tt>/host</tt></li>
</ul>
</p>

<h2>Adding new mount points</h2>
<p>
When a new mount point is added, the user has to choose two directories: one on the host side, and one on the container side, which is where the host directory will be visible on the container.
</p>
<p>
The user is thus first asked for the host-side directory (the one to be mounted), using a file/directory browser. <b>However</b> as the <tt>bv</tt> program is actually running on the container side, it cannot display the host-side filesystem in its native form. This is why we display the <tt>/host</tt> directory, which is where the host root filesystem is mounted. The <tt>/host</tt> prefix will be removed automatically.
</p>
<p>
Once the host-side directory has been chosen, it is displayed as the first column in a new line of the mount table. the second column ("Container") must be edited (via a double click), and the container-side mount point must be typed here. It is not a file/directory browser since the container-side directory does not necessarily exist and may not be found on the container filesystem.
</p>
<h3>Global / local mounts</h3>
<p>A <b>"global" mount point</b> is shared between all user casa-distro environments: it is saved in the host user configuration file.
</p>
<p>A <b>"local" mount point</b> is only used in the speficic environment which is currently being configured.
</p>
<p>The global or local state is displayed in the check button in the 3rd column of mount paths edition. They can be changed by clicking on the check button. <b>Be careful</b> because this will actually change the global user settings.
</p>
<h3>Validation</h3>
<p>
After mount points have been edited, they must be validated (using the "OK" button in the configuration GUI), and <tt>bv</tt> must be restarted using the new mounts.
</p>

<h2>Other configuration issues and useful mounts</h2>
<p>
See the <a href="https://brainvisa.info/configuration.html">BrainVisa configuration section</a> on the web site
</p>
'''  # noqa: E501
        self.help_widget.setHtml(help_text)
        self.help_widget.show()

    def check_mount(self, host, container):
        if host and container:
            return True

    def _value_modified(self, row, col):
        if (not getattr(self._mount_table.item(row, 0), 'text', None)
                or not getattr(self._mount_table.item(row, 1),
                               'text', None)
                or self._mount_table.item(row, 2) is None):
            return
        host = self._mount_table.item(row, 0).text()
        cont = self._mount_table.item(row, 1).text()
        checked = self._mount_table.item(row, 2).checkState()
        if checked == Qt.Qt.Checked:
            is_global = True
        else:
            is_global = False
        old_cont = self._mount_table.item(row, 0).data(Qt.Qt.UserRole)
        if old_cont is not None and old_cont != cont:
            del self.mounts[old_cont]
        self.mounts[cont] = [host, is_global]
        self._mount_table.item(row, 0).setData(Qt.Qt.UserRole, cont)
        self.valueChanged.emit()
        self.check_all_mounts()

    def check_all_mounts(self, *args):
        self._mount_table.blockSignals(True)
        self.modified = True
        all_mounts_ok = True
        in_container = []

        for idx in range(self._mount_table.rowCount()):
            if (not getattr(self._mount_table.item(idx, 0), 'text', None)
                or not getattr(self._mount_table.item(idx, 1),
                               'text', None)):
                self._mount_table.blockSignals(False)
                return None
            host = self._mount_table.item(idx, 0).text()
            container = self._mount_table.item(idx, 1).text()
            if container in in_container:
                self._mount_table.item(idx, 0).setBackground(self._orange)
                self._mount_table.item(idx, 1).setBackground(self._orange)
                self._mount_table.item(idx, 2).setBackground(self._orange)

                other_idx = in_container.index(container)
                self._mount_table.item(
                    other_idx, 0).setBackground(self._orange)
                self._mount_table.item(
                    other_idx, 1).setBackground(self._orange)
                self._mount_table.item(
                    other_idx, 2).setBackground(self._orange)
                all_mounts_ok = False

            elif self.check_mount(host, container):
                self._mount_table.item(
                    idx, 0).setBackground(Qt.QColor('white'))
                self._mount_table.item(
                    idx, 1).setBackground(Qt.QColor('white'))
                self._mount_table.item(
                    idx, 2).setBackground(Qt.QColor('white'))

            else:
                self._mount_table.item(idx, 0).setBackground(self._red)
                self._mount_table.item(idx, 1).setBackground(self._red)
                self._mount_table.item(idx, 2).setBackground(self._red)
                all_mounts_ok = False

            in_container.append(container)

        if not all_mounts_ok:
            self._error_label.setText(
                'Mount points are not all set correctly!')
        else:
            self._error_label.setText('')

        self._mount_table.blockSignals(False)
        return all_mounts_ok

    def hideEvent(self, event):
        if hasattr(self, 'help_widget') and self.help_widget:
            self.help_widget.close()
            del self.help_widget
        event.accept()


class Launchers(Qt.QWidget):

    launched = Signal(str)

    def __init__(self):
        super(Launchers, self).__init__()
        self.icon_size = 70

        self.setup_ui()
        self.setup_links()

    def setup_ui(self):
        self._main_layout = Qt.QVBoxLayout(self)
        self._launchers_container = Qt.QWidget()
        self._launchers_layout = Qt.QHBoxLayout()

        # self._frame = QFrame(self)
        # self._layout = Qt.QHBoxLayout(self._frame)
        # self._frame.setFrameShape(QFrame.StyledPanel)

        self._reload_msg = Qt.QLabel()

        env_path, python_path, build_path = get_env_path()
        if not build_path:
            build_path = ''
        icon_path = None
        axon_doc = glob.glob(os.path.join(build_path, 'share/doc/axon*'))
        if axon_doc:
            icon_path = os.path.join(axon_doc[0], 'images/brainvisa.png')
        brainvisa_icon = Qt.QPixmap(icon_path)
        self._brainvisa_btn = Qt.QPushButton(
            Qt.QIcon(brainvisa_icon), 'BRAINVISA')
        self._brainvisa_btn.setIconSize(
            Qt.QSize(self.icon_size, self.icon_size))

        icon_path = None
        ana_doc = glob.glob(os.path.join(build_path, 'share/doc/anatomist*'))
        if ana_doc:
            icon_path = os.path.join(ana_doc[0], 'images/anaLogo.png')
        anatomist_icon = Qt.QPixmap(icon_path)
        self._anatomist_btn = Qt.QPushButton(
            Qt.QIcon(anatomist_icon), 'ANATOMIST')
        self._anatomist_btn.setIconSize(
            Qt.QSize(self.icon_size, self.icon_size))

        term_icon = Qt.QPixmap(
            '/usr/share/icons/Humanity/apps/64/terminal.svg')
        self._terminal_btn = Qt.QPushButton(Qt.QIcon(term_icon), 'TERMINAL')
        self._terminal_btn.setIconSize(
            Qt.QSize(self.icon_size, self.icon_size))
        self._xterm_btn = Qt.QPushButton(Qt.QIcon(term_icon), 'XTERM')
        self._xterm_btn.setIconSize(
            Qt.QSize(self.icon_size, self.icon_size))

        self._launchers_layout.addWidget(self._brainvisa_btn)
        self._launchers_layout.addWidget(self._anatomist_btn)
        self._launchers_layout.addWidget(self._xterm_btn)
        if sys.stdout.isatty() and sys.stdin.isatty():
            self._launchers_layout.addWidget(self._terminal_btn)

        self._main_layout.addWidget(self._reload_msg)
        self._main_layout.addWidget(self._launchers_container)
        self._launchers_container.setLayout(self._launchers_layout)

    def setup_links(self):
        self._brainvisa_btn.clicked.connect(self._launch_brainvisa)
        self._anatomist_btn.clicked.connect(self._launch_anatomist)
        self._terminal_btn.clicked.connect(self._launch_terminal)
        self._xterm_btn.clicked.connect(self._launch_xterm)

    def _launch_brainvisa(self):
        self.launch('brainvisa')

    def _launch_anatomist(self):
        self.launch('anatomist')

    def _launch_xterm(self):
        import distutils.spawn
        for prog in ('x-terminal-emulator', 'lxterm', 'konsole',
                     'gnome-terminal', 'xterm'):
            if distutils.spawn.find_executable(prog):
                self.launch(prog)
                break

    def _launch_terminal(self):
        self.launch('bash')

    def launch(self, command):
        self.launched.emit(command)

    def disable_for_reload(self):
        self._launchers_container.setEnabled(False)
        self._reload_msg.setText(
            "Reloading is needed to launch software/terminal!")


class ConfigEditor(Qt.QWidget):

    def __init__(self, conf, parent=None):
        super(Qt.QWidget, self).__init__(parent)
        try:
            from soma.controller import OpenKeyController
            import traits.api as traits
        except ImportError as e:
            print(e, file=sys.stderr)
            return

        self.conf = conf
        self.controller = OpenKeyController()

        trait_types = {
            dict: traits.Dict,
            collections.OrderedDict: traits.Dict,
            str: traits.Str,
            float: traits.Float,
            int: traits.Int,
            list: traits.List,
            traits.TraitListObject: traits.List,
        }
        default_traits = [
            ('casa_distro_compatibility',
             traits.Str(
                 '3', desc='Version of casa-distro to be used with this '
                 'environment. <b>Change it with care, only if you know what '
                 'you are doing</b>.')),
            ('name', traits.Str(
                '', desc='Name of the environment. Must be unique within a '
                'base casa-distro directory, if the casa_distro command is '
                'used to manage several environments.')),
            ('distro', traits.Str(
                'core', desc='Projects set name. Normally "core", '
                '"opensource", "brainvisa", "cea", "web". Other sets may be '
                'defined. '
                'Changing it after the initial setup has no effect.')),
            ('system', traits.Str(
                '', desc='Name of the Linux system running inside the '
                'container. It should not be modified.')),
        ]
        if conf.get('type', '') == 'user':
            default_traits.append(('version', traits.Str(
                '', desc='BrainVISA release version. It should not be '
                'modified.')))
        else:
            default_traits.append(('branch', traits.Str(
                '', desc='Projects sources branch: "master", "integration", '
                '"latest_release", "release_candidate". Changing it after '
                'the initial setup has no effect.')))

        default_traits += [
            ('type', traits.Str(
                'user', desc='image type: <ul>'
                '<li>"user": user image with the BrainVISA distribution,</li> '
                '<li>"run": bare system to run programs, without BrainVISA '
                'installed in it,</li> <li>"dev": development system for '
                'developers.</li></ul><b>Do not modify this value.</b>')),
            ('image', traits.Str(
                '', desc='virtual image file. Changing it will use a '
                'different system / development image. It may be useful '
                'during development / testing but is also dangerous. It is '
                'generally pointless to modify it for user images. However it '
                'may be used to update after moving the image file.')),
            ('container_type', traits.Str(
                'singularity', desc='virtual container system. <b>Do '
                'not modify this value.</b>')),
            ('env', traits.Dict(
                traits.Str(), traits.Str(), {}, desc='environment variables '
                'passed to the container')),
            ('gui_env', traits.DictStrStr(
                {}, desc='environment variables passed to the container, only '
                'in the case of a run with graphical options enabled '
                '(gui=true)')),
            ('container_options', traits.ListUnicode(
                [], desc='options passed to the container system program. '
                'They are "native" options, specific to the container system '
                'used.')),
            ('container_gui_options', traits.ListUnicode(
                [], desc='options passed to the container system program, in '
                'the context of a graphical run (gui=true)')),
        ]
        for name, trait in default_traits:
            if not self.controller.trait(name):
                self.controller.add_trait(name, trait)

        for key, value in conf.items():
            if key == 'mounts':
                # mounts are edited in the GUI and cause problems to the
                # ControllerWidget which shows dict keys as traits, thus
                # do not support some / or . characters in traits names.
                continue
            if not self.controller.trait(key):
                trait_type = trait_types.get(type(value), traits.Any)
                self.controller.add_trait(key, trait_type())
            setattr(self.controller, key, value)

        self.setup_ui()

    def setup_ui(self):
        from soma.qt_gui.controller_widget import ScrollControllerWidget
        self.controller_widget = ScrollControllerWidget(self.controller,
                                                        live=True)
        layout = Qt.QVBoxLayout()
        self.setLayout(layout)
        layout.addWidget(self.controller_widget)

    def edited_config(self):
        new_conf = self.controller.export_to_dict()
        if 'protected_parameters' in new_conf:
            del new_conf['protected_parameters']
        return new_conf


class ContainerImageEditor(Qt.QDialog):
    def __init__(self, conf, container_status, conf_path, parent=None):
        super(ContainerImageEditor, self).__init__(parent)

        self.conf = conf
        self.container_status = container_status
        self.conf_path = conf_path
        # print(container_status)

        layout = Qt.QVBoxLayout()
        self.setLayout(layout)
        self.setWindowTitle('Container image options')

        inst_rw = Qt.QCheckBox('install read-write image directory')
        inst_rw.setChecked(container_status['write'])
        layout.addWidget(inst_rw)
        ov_hb = Qt.QHBoxLayout()
        layout.addLayout(ov_hb)
        inst_overlay = Qt.QCheckBox('add read-write overlay')
        inst_overlay.setChecked(container_status['overlay'] is not None)
        ov_hb.addWidget(inst_overlay)
        self.inst_rw_cb = inst_rw
        self.inst_overlay_cb = inst_overlay
        self.overlay_count = Qt.QSpinBox()
        self.overlay_count.setRange(1, 1023)
        self.overlay_count.setValue(500)
        ov_hb.addStretch(1)
        ov_hb.addWidget(self.overlay_count)
        self.overlay_unit = Qt.QComboBox()
        self.overlay_unit.addItems(['KB', 'MB', 'GB', 'TB', 'PB'])
        self.overlay_unit.setCurrentIndex(1)
        ov_hb.addWidget(self.overlay_unit)

        inst_rw.toggled.connect(self.install_rw)
        inst_overlay.toggled.connect(self.install_overlay)

        layout.addStretch(1)

        validation_btns = Qt.QDialogButtonBox(
            Qt.QDialogButtonBox.Ok)
        layout.addWidget(validation_btns)
        validation_btns.button(Qt.QDialogButtonBox.Ok).setDefault(True)
        validation_btns.button(Qt.QDialogButtonBox.Ok).setAutoDefault(True)

        validation_btns.accepted.connect(self.accept)
        self.validation_btns = validation_btns

    def install_rw(self, state):
        # print(state)
        if not state:
            self.remove_rw()
        else:
            self.add_rw()

    def install_overlay(self, state):
        if not state:
            self.remove_overlay()
        else:  # create overlay
            self.create_overlay()

    def remove_overlay(self):
        overlay_file = osp.join(self.parent().env_path, 'overlay.img')
        coverlay_file = osp.join('/host', overlay_file[1:])

        if not osp.exists(coverlay_file):
            return

        confirm = Qt.QMessageBox.question(
            self, 'Erase overlay file ?',
            'Removing the overlay will erase the overlay file:<br/>'
            '<b>%s</b>' % overlay_file)
        if confirm == Qt.QMessageBox.Yes:
            print('erasing')

            Qt.qApp.setOverrideCursor(Qt.Qt.WaitCursor)
            try:

                os.unlink(overlay_file)
                self.container_status['overlay'] = None

                Qt.QMessageBox.information(
                    self, 'Done', 'Overlay has been erased.')

            finally:
                Qt.qApp.restoreOverrideCursor()

        else:
            self.inst_overlay_cb.blockSignals(True)
            self.inst_overlay_cb.setChecked(True)
            self.inst_overlay_cb.blockSignals(False)

    def create_overlay(self):
        overlay_file = osp.join(self.parent().env_path, 'overlay.img')
        coverlay_file = osp.join('/host', overlay_file[1:])

        if osp.exists(coverlay_file):
            Qt.QMessageBox.critical(
                self, 'Overlay exists',
                'The overlay file <b>%s</b> already exists !'
                % overlay_file)
            return

        confirm = Qt.QMessageBox.question(
            self, 'Create overlay file ?',
            'This will create the overlay file:<br/>'
            '<b>%s</b>' % overlay_file)

        if confirm == Qt.QMessageBox.Yes:

            Qt.qApp.setOverrideCursor(Qt.Qt.WaitCursor)
            try:

                n = self.overlay_count.value()
                bs = self.overlay_unit.currentText()[:-1]
                tmpd = tempfile.mkdtemp()
                os.makedirs(osp.join(tmpd, 'overlay/upper'))
                os.makedirs(osp.join(tmpd, 'overlay/work'))
                os.chmod(osp.join(tmpd, 'overlay/upper'), 0o777)
                os.chmod(osp.join(tmpd, 'overlay/work'), 0o777)
                cmds = [
                    ['dd', 'if=/dev/zero', 'of=%s' % coverlay_file,
                        'bs=1%s' % bs, 'count=%d' % n],
                    ['mkfs.ext3', '-d', 'overlay', coverlay_file]
                ]
                for cmd in cmds:
                    subprocess.check_call(cmd, cwd=tmpd)
                shutil.rmtree(tmpd)
                self.container_status['overlay'] \
                    = os.stat(coverlay_file).st_size
                Qt.QMessageBox.information(
                    self, 'Done', 'Overlay has been setup.')

            finally:
                Qt.qApp.restoreOverrideCursor()

        else:
            self.inst_overlay_cb.blockSignals(True)
            self.inst_overlay_cb.setChecked(False)
            self.inst_overlay_cb.blockSignals(False)

    def remove_rw(self):
        image = self.conf['image']
        print('remove rw', image)
        sif_image = image + '.sif'
        if not osp.exists(sif_image):
            Qt.QMessageBox.critical(
                self, 'No singularty image',
                'Before removing an image directory, you must ensure to have '
                'a regular image file next to it. We expect to find the file '
                '<b>%s</b>, which is not present.<br/>Aborting.' % sif_image)
            return

        confirm = Qt.QMessageBox.question(
            self, 'Remove writable directory ?',
            'This will completely remove the system image direcotry:<br/>'
            '<b>%s</b>.<br>Are you sure ?' % image)

        if confirm == Qt.QMessageBox.Yes:

            Qt.qApp.setOverrideCursor(Qt.Qt.WaitCursor)
            try:

                shutil.rmtree(image)
                self.conf['image'] = sif_image
                self.container_status['write'] = False

                Qt.QMessageBox.information(
                    self, 'Done', 'Image directory has been erased.')

            finally:
                Qt.qApp.restoreOverrideCursor()

        else:
            self.inst_rw_cb.blockSignals(True)
            self.inst_rw_cb.setChecked(True)
            self.inst_rw_cb.blockSignals(False)

    def add_rw(self):
        image = self.conf['image']
        print('add rw', image)
        if not image.endswith('.sif'):
            Qt.QMessageBox.critical(
                self, 'Not a singularity image',
                'The configured image file <b>%s</b> does not end with the '
                '<tt>.sif</tt> extension !' % image)
            return

        image_dir = image[:-4]
        if osp.exists(image_dir):
            Qt.QMessageBox.critical(
                self, 'Image directory exists',
                'The image directory <b>%s</b> already exists !' % image_dir)
            return

        confirm = Qt.QMessageBox.question(
            self, 'Create writable directory ?',
            'This will create the system image direcotry:<br/>'
            '<b>%s</b>.<br>Are you sure ?' % image_dir)

        if confirm == Qt.QMessageBox.Yes:

            Qt.qApp.setOverrideCursor(Qt.Qt.WaitCursor)
            try:

                cmd = ['singularity', 'build', '--sandbox', image_dir, image]
                cmd_str = '"%s"' % '" "'.join(cmd)
                print(cmd)
                ssh_cmd = ['ssh', 'localhost', cmd_str]
                print(ssh_cmd)
                try:
                    subprocess.check_call(ssh_cmd)
                except Exception as e:
                    print(e)
                    Qt.QMessageBox.critical(
                        self,
                        'Image directory creation failed',
                        'The image directory creation has failed. Possibly '
                        'because we must run it outside of the container and '
                        'the host system could not be reached from here (we '
                        'are inside). Try running this command manually on '
                        'the host:<br><br>%s' % cmd_str)
                    return

                self.conf['image'] = image_dir
                self.container_status['write'] = True

                Qt.QMessageBox.information(
                    self, 'Done',
                    'Image directory has been setup. Note that:<br> '
                    '- image updates will not work any longer for this '
                    'image.<br>'
                    '- to actually use the image read/write, you must use '
                    'manually the command:<br>'
                    '  <tt>singularity run -w %s bash</tt><br/>'
                    'This is not done by "bv" because it would imply '
                    'incompatibe options for singularity.' % image_dir)

            finally:
                Qt.qApp.restoreOverrideCursor()

        else:
            self.inst_rw_cb.blockSignals(True)
            self.inst_rw_cb.setChecked(False)
            self.inst_rw_cb.blockSignals(False)


def get_env_path():
    env_path = '/casa/host'
    build_path = None
    python_path = None
    casa_path = os.path.dirname(os.path.dirname(os.path.dirname(
        os.path.realpath(__file__))))
    if os.path.isdir(os.path.join(casa_path, 'python')):
        python_path = os.path.join(casa_path, 'python')
    else:
        try:
            import casa_distro
            python_path = os.path.dirname(os.path.dirname(
                casa_distro.__file__))
        except ImportError:
            python_path = None
    if not python_path or not os.path.isdir(python_path):
        python_path = '/casa/casa-distro/python'

    if os.path.isdir('/casa/host/build/bin'):
        build_path = '/casa/host/build'
    elif os.path.isdir('/casa/host/install/bin'):
        build_path = '/casa/host/install'
    elif os.path.isdir('/casa/install/bin'):
        build_path = '/casa/install'
    return env_path, python_path, build_path


def main_gui():
    if not Qt.QApplication.instance():
        app = Qt.QApplication(sys.argv)
    else:
        app = Qt.QApplication.instance()

    casa_path, _, _ = get_env_path()
    conf_path = os.path.join(casa_path, 'conf/casa_distro.json')
    dialog = CasaLauncher(conf_path)
    dialog.show()

    app.exec_()


if __name__ == "__main__":
    main_gui()
