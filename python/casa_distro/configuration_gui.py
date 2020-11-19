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

try:
    from soma.qt_gui.qt_backend import Qt
    from soma.qt_gui.qt_backend.QtCore import Signal
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

        if dialog.exec_():
            for k in list(self.conf.keys()):
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
        self._manager_btns.addStretch(1)
        self._manager_btns.addWidget(self._add_mount)
        self._manager_btns.addWidget(self._remove_mount)

        self._main_layout.addWidget(self._mount_table)
        self._main_layout.addWidget(self._error_label)
        self._main_layout.addLayout(self._manager_btns)

    def setup_links(self):
        self._add_mount.clicked.connect(self._add_mount_row)
        self._remove_mount.clicked.connect(self._delete_mount_row)
        self._mount_table.cellChanged.connect(self._value_modified)

    def update_ui(self):
        self._mount_table.clearContents()
        for idx, (host, container) in enumerate(
                self.conf.get('mounts', {}).items()):
            self._mount_table.setItem(idx, 0, Qt.QTableWidgetItem(host))
            # First col not editable
            self._mount_table.item(idx, 0).setFlags(
                self._mount_table.item(idx, 0).flags() ^ Qt.Qt.ItemIsEditable)
            self._mount_table.setItem(idx, 1, Qt.QTableWidgetItem(container))

    def _add_mount_row(self):
        host_mount_choice = Qt.QFileDialog()
        host_mount_choice.setFileMode(Qt.QFileDialog.Directory)
        if host_mount_choice.exec_():
            self.modified = True
            self.valueChanged.emit()
            self._mount_table.setRowCount(self._mount_table.rowCount() + 1)
            host_path = host_mount_choice.selectedFiles()[0]
            self._mount_table.setItem(
                self._mount_table.rowCount() - 1, 0,
                Qt.QTableWidgetItem(host_path))
            self._mount_table.setItem(
                self._mount_table.rowCount() - 1, 1,
                Qt.QTableWidgetItem(''))
            self.conf.get('mounts', {})[host_path] = ''
            self.check_all_mounts()

    def _delete_mount_row(self):
        if self._mount_table.selectedItems():
            self.modified = True
            self.valueChanged.emit()
            rows = sorted(
                set(item.row() for item in self._mount_table.selectedItems()),
                reverse=True)
            for row in rows:
                host_path = self._mount_table.item(row, 0).text()
                del self.conf.get('mounts', {})[host_path]
                self._mount_table.removeRow(row)

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
        self.conf.setdefault('mounts', {})[host] = cont
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
        brainvisa_icon = Qt.QPixmap(
            os.path.join(build_path, 'share/doc/axon/images/brainvisa.png'))
        self._brainvisa_btn = Qt.QPushButton(
            Qt.QIcon(brainvisa_icon), 'BRAINVISA')
        self._brainvisa_btn.setIconSize(
            Qt.QSize(self.icon_size, self.icon_size))

        anatomist_icon = Qt.QPixmap(
            os.path.join(build_path,
                         'share/doc/anatomist/html/images/anaLogo.png'))
        self._anatomist_btn = Qt.QPushButton(
            Qt.QIcon(anatomist_icon), 'ANATOMIST')
        self._anatomist_btn.setIconSize(
            Qt.QSize(self.icon_size, self.icon_size))

        self._terminal_btn = Qt.QPushButton(Qt.QIcon(), 'TERMINAL')

        self._launchers_layout.addWidget(self._brainvisa_btn)
        self._launchers_layout.addWidget(self._anatomist_btn)
        self._launchers_layout.addWidget(self._terminal_btn)

        self._main_layout.addWidget(self._reload_msg)
        self._main_layout.addWidget(self._launchers_container)
        self._launchers_container.setLayout(self._launchers_layout)

    def setup_links(self):
        self._brainvisa_btn.clicked.connect(self._launch_brainvisa)
        self._anatomist_btn.clicked.connect(self._launch_anatomist)
        self._terminal_btn.clicked.connect(self._launch_terminal)

    def _launch_brainvisa(self):
        self.launch('brainvisa')

    def _launch_anatomist(self):
        self.launch('anatomist')

    def _launch_terminal(self):
        self.launch('xterm')

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
        for key, value in conf.items():
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
    build_path = None
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
    # try direct install case (unlinkely)
    env_path = casa_path
    if os.path.exists(os.path.join(env_path, 'conf', 'casa_distro.json')):
        build_path = os.path.dirname(python_path)
    else:
        # install [/ build] case
        env_path = os.path.dirname(env_path)
        if os.path.exists(os.path.join(env_path, 'conf', 'casa_distro.json')):
            build_path = os.path.dirname(python_path)
        else:
            # source case
            env_path = os.path.dirname(os.path.dirname(
                os.path.dirname(env_path)))
            build_path = os.path.join(env_path, 'build')
    return env_path, python_path, build_path


if __name__ == "__main__":
    if not Qt.QApplication.instance():
        app = Qt.QApplication(sys.argv)

    casa_path, _, _ = get_env_path()
    conf_path = os.path.join(casa_path, 'conf/casa_distro.json')
    dialog = CasaLauncher(conf_path)
    dialog.show()

    app.exec_()