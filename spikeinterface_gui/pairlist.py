from .myqt import QT
import pyqtgraph as pg

import numpy as np
import itertools

from .base import WidgetBase
from .tools import ParamDialog, get_dict_from_group_param, CustomItem


class PairListView(WidgetBase):
    """
    """
    _automerge_params = [
        # {'name': 'threshold_similarity', 'type': 'float', 'value' :.9, 'step' : 0.01},
        # {'name': 'threshold_ratio_similarity', 'type': 'float', 'value' :.8, 'step' : 0.01},

        {'name': 'minimum_spikes', 'type': 'int', 'value': 1000},
        {'name': 'maximum_distance_um', 'type': 'float', 'value': 150.},
        {'name': 'peak_sign', 'type': 'list', 'values': ['neg', 'pos', 'both']},
        {'name': 'bin_ms', 'type': 'float', 'value': 0.25, 'step': 0.05},
        {'name': 'window_ms', 'type': 'float', 'value': 100., 'step': 1.},
        {'name': 'corr_diff_thresh', 'type': 'float', 'value': .16, 'step': 0.01},
        {'name': 'template_diff_thresh', 'type': 'float', 'value': .25, 'step': 0.01},
        {'name': 'censored_period_ms', 'type': 'float', 'value': .3, 'step': 0.01},
        {'name': 'refractory_period_ms', 'type': 'float', 'value': 1.0, 'step': 0.1},
        {'name': 'sigma_smooth_ms', 'type': 'float', 'value': 0.6, 'step': 0.1},
        {'name': 'contamination_threshold', 'type': 'float', 'value': .2, 'step': 0.01},
        {'name': 'adaptative_window_threshold', 'type': 'float', 'value': .5, 'step': 0.01},
        {'name': 'censor_correlograms_ms', 'type': 'float', 'value': .15, 'step': 0.01},
        {'name': 'num_channels', 'type': 'int', 'value': 5},
        {'name': 'num_shift', 'type': 'int', 'value': 5},
        {'name': 'firing_contamination_balance', 'type': 'float', 'value': 1.5, 'step': 0.1},
    ]

    _similarity_params = [
        {'name': 'threshold_similarity', 'type': 'float', 'value': .9, 'step': 0.01},
        {'name': 'method', 'type': 'list', 'limits': ['cosine_similarity']},
    ]

    _need_compute = True

    def __init__(self, controller=None, parent=None):
        WidgetBase.__init__(self, parent=parent, controller=controller)

        self.merge_info = {}
        self.layout = QT.QVBoxLayout()
        self.setLayout(self.layout)
        # ~ h = QT.QHBoxLayout()
        # ~ self.layout.addLayout(h)
        self.combo_select = QT.QComboBox()
        # ~ h.addWidget(QT.QLabel('Select'))
        # ~ h.addWidget(self.combo_select)
        self.combo_select.addItems(['all pairs', 'high similarity'])  #
        # ~ self.combo_select.currentTextChanged.connect(self.refresh)
        # ~ h.addStretch()

        # ~ but = QT.QPushButton('settings')
        # ~ self.layout.addWidget(but)
        # ~ but.clicked.connect(self.open_settings)

        self.table = QT.QTableWidget(selectionMode=QT.QAbstractItemView.SingleSelection,
                                     selectionBehavior=QT.QAbstractItemView.SelectRows)
        self.table.setContextMenuPolicy(QT.Qt.CustomContextMenu)
        self.layout.addWidget(self.table)
        self.table.itemSelectionChanged.connect(self.on_item_selection_changed)

        # ~ self.table.customContextMenuRequested.connect(self.open_context_menu)

        # ~ self.menu = QT.QMenu()
        # ~ act = self.menu.addAction('Merge')
        # ~ act.triggered.connect(self.do_merge)

        # ~ act = self.menu.addAction('Tag same cell')
        # ~ act.triggered.connect(self.do_tag_same_cell)
        self.pairs = self.controller.get_merge_list()
        self.refresh()

    def on_item_selection_changed(self):
        inds = self.table.selectedIndexes()
        if len(inds) != self.table.columnCount():
            return
        # k1, k2 = self.pairs[inds[0].row()]
        item = self.table.item(inds[0].row(), 0)
        k1, k2 = item.unit_id_pair

        for k in self.controller.unit_visible_dict:
            self.controller.unit_visible_dict[k] = False
        self.controller.unit_visible_dict[k1] = True
        self.controller.unit_visible_dict[k2] = True

        self.controller.update_visible_spikes()
        self.unit_visibility_changed.emit()

    def open_context_menu(self):
        self.menu.popup(self.cursor().pos())

    # def do_merge(self):
    #     if len(self.table.selectedIndexes())==0:
    #         return
    #     ind = self.table.selectedIndexes()[0].row()

    #     label_to_merge = list(self.pairs[ind])
    #     self.controller.merge_cluster(label_to_merge)
    #     self.refresh()
    #     self.spike_label_changed.emit()

    # def do_tag_same_cell(self):
    #     if len(self.table.selectedIndexes())==0:
    #         return
    #     ind = self.table.selectedIndexes()[0].row()

    #     label_to_merge = list(self.pairs[ind])
    #     self.controller.tag_same_cell(label_to_merge)
    #     self.refresh()
    #     self.cluster_tag_changed.emit()

    def _refresh(self):
        self.table.clear()
        self.table.setSortingEnabled(False)
        labels = ['unit_id1', 'unit_id2']
        potential_labels = {'similarity', 'correlogram_diff', 'templates_diff'}
        for lbl in self.merge_info.keys():
            if lbl in potential_labels:
                labels.append(lbl)
        self.table.setColumnCount(len(labels))
        self.table.setHorizontalHeaderLabels(labels)
        self.table.setColumnWidth(0, 100)
        self.table.setColumnWidth(1, 100)

        if self.pairs is None:
            return

            # select
        # mode = self.combo_select.currentText()
        # if mode == 'all pairs':
        #     unit_ids = self.controller.unit_ids
        #     self.pairs = list(itertools.combinations(unit_ids, 2))
        # elif mode == 'high similarity':
        #     self.pairs = self.controller.detect_high_similarity(threshold=self.params['threshold_similarity'])

        # sort
        # mode = self.combo_sort.currentText()
        # order = np.arange(len(self.pairs))
        # if mode == 'label':
        #     pass
        # elif mode == 'similarity':
        #     if self.controller.cluster_similarity is not None:
        #         order = []
        #         for r in range(len(self.pairs)):
        #             k1, k2 = self.pairs[r]
        #             ind1 = self.controller.positive_cluster_labels.tolist().index(k1)
        #             ind2 = self.controller.positive_cluster_labels.tolist().index(k2)
        #             order.append(self.controller.cluster_similarity[ind1, ind2])
        #         order = np.argsort(order)[::-1]
        # ~ elif mode == 'ratio_similarity':
        # ~ if self.controller.cluster_ratio_similarity is not None:
        # ~ order = []
        # ~ for r in range(len(self.pairs)):
        # ~ k1, k2 = self.pairs[r]
        # ~ ind1 = self.controller.positive_cluster_labels.tolist().index(k1)
        # ~ ind2 = self.controller.positive_cluster_labels.tolist().index(k2)
        # ~ order.append(self.controller.cluster_ratio_similarity[ind1, ind2])
        # ~ order = np.argsort(order)[::-1]
        # self.pairs = [self.pairs[i] for i in order ]

        self.table.setRowCount(len(self.pairs))

        for r in range(len(self.pairs)):
            unit_id1, unit_id2 = self.pairs[r]
            # ind1 = self.controller.unit_ids.tolist().index(unit_id1)
            # ind2 = self.controller.unit_ids.tolist().index(unit_id2)

            for c, unit_id in enumerate((unit_id1, unit_id2)):
                color = self.controller.qcolors.get(unit_id, QT.QColor('white'))
                pix = QT.QPixmap(16, 16)
                pix.fill(color)
                icon = QT.QIcon(pix)

                # TODO
                #  name = '{} (n={})'.format(k, self.controller.cluster_count[k])
                n = self.controller.num_spikes[unit_id]
                name = f'{unit_id} n={n}'
                item = QT.QTableWidgetItem(name)
                item.setData(QT.Qt.ItemDataRole.UserRole, unit_id)
                item.setFlags(QT.Qt.ItemIsEnabled | QT.Qt.ItemIsSelectable)
                self.table.setItem(r, c, item)
                item.setIcon(icon)
                item.unit_id_pair = (unit_id1, unit_id2)

            for c_ix, info_name in enumerate(labels[2:]):
                info = self.merge_info[info_name][unit_id1][unit_id2]
                item = CustomItem(f'{info:.2f}')
                self.table.setItem(r, c_ix + 2, item)

                # ~ cell_label = self.controller.cell_labels[self.controller.cluster_labels==k][0]
                # ~ name = '{}'.format(cell_label)
                # ~ item = QT.QTableWidgetItem(name)
                # ~ item.setFlags(QT.Qt.ItemIsEnabled|QT.Qt.ItemIsSelectable)
                # ~ self.table.setItem(r,c+2, item)

            # ~ if self.controller.cluster_similarity is not None:
            # ~ if self.controller.cluster_similarity.shape[0] == self.controller.positive_cluster_labels.size:
            # ~ name = '{}'.format(self.controller.cluster_similarity[ind1, ind2])
            # ~ item = QT.QTableWidgetItem(name)
            # ~ item.setFlags(QT.Qt.ItemIsEnabled|QT.Qt.ItemIsSelectable)
            # ~ self.table.setItem(r,4, item)

            # ~ if self.controller.cluster_ratio_similarity is not None:
            # ~ if self.controller.cluster_ratio_similarity.shape[0] == self.controller.positive_cluster_labels.size:
            # ~ name = '{}'.format(self.controller.cluster_ratio_similarity[ind1, ind2])
            # ~ item = QT.QTableWidgetItem(name)
            # ~ item.setFlags(QT.Qt.ItemIsEnabled|QT.Qt.ItemIsSelectable)
            # ~ self.table.setItem(r,5, item)
        for i in range(self.table.columnCount()):
            self.table.resizeColumnToContents(i)
        self.table.setSortingEnabled(True)

    def on_spike_selection_changed(self):
        pass

    def on_colors_changed(self):
        self.refresh()

    def on_unit_visibility_changed(self):
        pass

    def compute(self):
        # First we choose the method

        methods = {'name': 'method', 'type': 'list', 'limits': ['similarity', 'automerge']}
        ch_method_d = ParamDialog([methods], title='Choose your method').get()
        if ch_method_d is None:
            return
        ch_method = ch_method_d['method']

        params = None
        # Depending on the method we set the parameters
        if ch_method == 'automerge':
            params = ParamDialog(self._automerge_params, title='Automerge parameters').get()
            self.pairs, self.merge_info = self.controller.compute_auto_merge(**params)
        elif ch_method == 'similarity':
            params = ParamDialog(self._similarity_params, title='Similarity parameters').get()
            similarity = self.controller.compute_similarity(params['method'])
            th_sim = similarity > params['threshold_similarity']
            self.pairs = [(i, j) for i, j in zip(*np.nonzero(th_sim)) if i < j]
            self.merge_info = {'similarity': similarity}
        # params = get_dict_from_group_param(self.params)
        #
        self.refresh()


PairListView._gui_help_txt = """Auto merge list selection
Click on on row to make visible a unique pair of unit.
"""
