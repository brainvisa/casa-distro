#! /usr/bin/env python
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


class CasaLauncher(Qt.QDialog):

    def __init__(self, conf_path):
        super(CasaLauncher, self).__init__()
        self.conf_path = conf_path

        with open(conf_path, 'r') as conf_file:
            self.conf = json.load(conf_file)

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
        self._mount_manager = MountManager(self.conf)

        conf_line = Qt.QHBoxLayout()
        conf_line.addWidget(Qt.QLabel('<b>Configuration:</b>'))
        conf_line.addStretch(1)
        self._conf_btn = Qt.QPushButton('...')
        conf_line.addWidget(self._conf_btn)

        self._launchers = Launchers()

        self._errors_label = Qt.QLabel()

        self._validation_btns = Qt.QDialogButtonBox(
            Qt.QDialogButtonBox.Ok | Qt.QDialogButtonBox.Cancel)

        self._main_layout.addWidget(Qt.QLabel('<b>Mount points:</b>'))
        self._main_layout.addWidget(self._mount_manager)
        self._main_layout.addLayout(conf_line)
        self._main_layout.addWidget(self._launchers)
        self._main_layout.addWidget(self._errors_label)
        self._main_layout.addWidget(self._validation_btns)

    def setup_links(self):
        self._validation_btns.accepted.connect(self.save_conf)
        self._validation_btns.rejected.connect(self.close)
        self._mount_manager.valueChanged.connect(self.block_launchers)
        self._launchers.launched.connect(self.close_and_launch)
        self._conf_btn.clicked.connect(self.edit_configuration)

    def save_conf(self):
        if self._mount_manager.check_all_mounts():
            print('SAVE')
            with open(self.conf_path, 'w') as conf_file:
                json.dump(self.conf, conf_file, indent=4)
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

    # def closeEvent(self, *args, **kwargs):
    #     super(Qt.QDialog, self).closeEvent(*args, **kwargs)
    #     print('CLOSE!!!!')


class MountManager(Qt.QWidget):

    def __init__(self, conf):
        super(MountManager, self).__init__()
        self.conf = conf
        self.modified = False

        self._red = Qt.QColor(250, 130, 130)
        self._orange = Qt.QColor(250, 200, 100)

        self.setup_ui()
        self.setup_links()

    valueChanged = Signal()

    def setup_ui(self):
        self._main_layout = Qt.QVBoxLayout(self)

        self._mount_table = Qt.QTableWidget()
        self._mount_table.setColumnCount(2)
        self._mount_table.setRowCount(len(self.conf.get('mounts', {})))
        self._mount_table.setHorizontalHeaderLabels(['Host', 'Container'])
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
        for idx, (container, host) in enumerate(
                self.conf.get('mounts', {}).items()):
            self._mount_table.setItem(idx, 0, Qt.QTableWidgetItem(host))
            self._mount_table.setItem(idx, 1, Qt.QTableWidgetItem(container))
            self._mount_table.item(idx, 0).setData(Qt.Qt.UserRole, container)

    def _add_mount_row(self):
        if '' in self.conf.get('mounts', {}):
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
            self.conf.setdefault('mounts', {})[''] = host_path
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
                del self.conf.get('mounts', {})[host_path]
                self._mount_table.removeRow(row)

    def _help_mounts(self):
        try:
            self.help_widget = QtWebEngineWidgets.QWebEngineView()
        except Exception:
            print('QWebEngineView failed, using QWebView')
            self.help_widget = Qt.QWebView()
        self.help_widget.setWindowTitle('How to configure mount points')
        help_text = '''<h1>How to configure mount points</h1>
<p>Mount points allow to see the host system directories from the container. They are needed to read and write files. Some mount points are automatically configured in <b>bv</b> / <b>Casa-Distro</b>, but additional mount points may be added by the user.
</p>

<h2>Automatically configure mount points</h2>
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
Once the host-side directory has been chosen, it is displayed as the first column in a new line of the mount table. the second column ("Container") must be edited (via a double click), and the container-side mount point must be typed here. It is not a file/directory browser since the container-side directoy does not necessarily exist and may not be found on the container filesystem.
</p>
<p>
After mount points have been edited, they must be validated (using the "OK" button in the configuration GUI), and <tt>bv</tt> must be restarted using the new mounts.
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
                           'text', None)):
            return
        host = self._mount_table.item(row, 0).text()
        cont = self._mount_table.item(row, 1).text()
        old_cont = self._mount_table.item(row, 0).data(Qt.Qt.UserRole)
        if old_cont is not None and old_cont != cont:
            del self.conf['mounts'][old_cont]
        self.conf.setdefault('mounts', {})[cont] = host
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

                other_idx = in_container.index(container)
                self._mount_table.item(
                    other_idx, 0).setBackground(self._orange)
                self._mount_table.item(
                    other_idx, 1).setBackground(self._orange)
                all_mounts_ok = False

            elif self.check_mount(host, container):
                self._mount_table.item(
                    idx, 0).setBackground(Qt.QColor('white'))
                self._mount_table.item(
                    idx, 1).setBackground(Qt.QColor('white'))

            else:
                self._mount_table.item(idx, 0).setBackground(self._red)
                self._mount_table.item(idx, 1).setBackground(self._red)
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
            "Reloading is needed to launch softwares/terminal!")


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
            ('casa_distro_compatibility', traits.Str('3')),
            ('name', traits.Str('')),
            ('distro', traits.Str('opensource')),
            ('system', traits.Str('')),
            ('branch', traits.Str('')),
            ('version', traits.Str('')),
            ('type', traits.Str('user')),
            ('image', traits.Str('')),
            ('container_type', traits.Str('singularity')),
            ('systems', traits.ListUnicode(['ubuntu-18.04'])),
            ('env', traits.Dict(traits.Str(), traits.Str(), {})),
            ('gui_env', traits.DictStrStr({})),
            ('container_options', traits.ListUnicode([])),
            ('container_gui_options', traits.ListUnicode([])),
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
