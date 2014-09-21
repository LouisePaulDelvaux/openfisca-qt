# -*- coding:utf-8 -*-

#
# This file is part of OpenFisca.
# OpenFisca is a socio-fiscal microsimulation software
# Copyright © 2011 Clément Schaff, Mahdi Ben Jelloul
# Licensed under the terms of the GVPLv3 or later license
# (see openfisca/__init__.py for details)


from openfisca_core import model

from ..gui.qt.QtCore import QAbstractTableModel, Qt, QString, SIGNAL, QModelIndex
from ..gui.qt.compat import to_qvariant, from_qvariant

from ..gui.qt.QtGui import (QStyle, QApplication, QDialog, QPalette, QColor,
                         QStyledItemDelegate, QDoubleSpinBox, QSpinBox,
                         QPushButton, QStyleOptionButton, QSortFilterProxyModel,
                         QStyleOptionViewItemV4)
from ..gui.views.ui_baremedialog import Ui_BaremeDialog


class CustomDelegate(QStyledItemDelegate):
    def __init__(self,parent = None):
        super(CustomDelegate, self).__init__(parent)
        self._parent = parent
        self.delegates = {}

    def insertColumnDelegate(self, column, delegate):
#        delegate.setParent(self)
        self.delegates[column] = delegate

    def removeColumnDelegate(self, column):
        if column in self.delegates:
            del self.delegates[column]

    def sizeHint(self, option, index):
        return QStyledItemDelegate.sizeHint(self, option, index )

    def paint(self, painter, option, index):
        delegate = self.delegates.get(index.column())
        if delegate is not None:
            delegate.paint(painter, option, index)
        else:
            QStyledItemDelegate.paint(self, painter, option, index)

    def createEditor(self, parent, option, index):
        delegate = self.delegates.get(index.column())
        if delegate is not None:
            return delegate.createEditor(parent, option, index)
        else:
            return QStyledItemDelegate.createEditor(self, parent, option, index)

    def setEditorData(self, editor, index):
        delegate = self.delegates.get(index.column())
        if delegate is not None:
            delegate.setEditorData(editor, index)
        else:
            QStyledItemDelegate.setEditorData(self, editor, index)

    def setModelData(self, editor, model, index):
        delegate = self.delegates.get(index.column())
        if delegate is not None:
            delegate.setModelData(editor, model, index)
        else:
            QStyledItemDelegate.setModelData(self, editor, model, index)

#class myDelegate(QStyledItemDelegate):
#    def __init__(self, parent = None):
#        super(myDelegate, self).__init__(parent)
#
#    def paint(self, painter, option, index):
#        styleOption = QStyleOptionViewItemV4(option)
#
#        # define the text to be shown
#        styleOption.text = "mytext"
#    # paint the cell
#        self.parent().style().drawControl(QStyle.CE_ItemVi ewItem, styleOption, painter)

class ValueColumnDelegate(QStyledItemDelegate):
    def __init__(self, parent=None):
        super(ValueColumnDelegate, self).__init__(parent)
        self._parent = parent

    def paint(self, painter, option, index):
        currency = model.CURRENCY

        year = "an"  # TODO: localization
        years = "ans"


        painter.save()
        if index.isValid():
            style = self.parent().style()
            styleOption = QStyleOptionViewItemV4(option)
            node = index.internalPointer()

            val = from_qvariant(index.model().data(index))


            if node.type_info == 'CODE':
                if node.value_format == 'percent':
                    text = '%.2f %%  ' % (val*100)
                elif node.value_format == 'bool':
                    text = '%d  ' % val
                elif node.value_format == 'integer':
                    if node.value_type == 'monetary':
                        text = '%d  %s' %( val, currency)
                    elif node.value_type == 'age':
                        if val <= 1:
                            text = '%d  %s' %( val, year)
                        else:
                            text = '%d  %s' %( val, years)
                    else:
                        text = '%d  ' % val
                elif node.value_format == 'float':
                    if node.value_type == 'monetary':
                        text = '%.2f  %s' %( val, currency)
                    else:
                        text = '%.2f  ' % val
                else:
                    if node.value_type == 'monetary':
                        text = '%.2f  %s' %( val, currency)
                    else:
                        text = '%.2f  ' % val

                styleOption.text = text
                styleOption.displayAlignment = Qt.AlignRight

                style.drawControl(QStyle.CE_ItemViewItem, styleOption, painter)

            elif node.type_info == 'BAREME' and index.column()==2:
                styleOption = QStyleOptionButton()
                styleOption.rect = option.rect
                styleOption.text = QString('Editer')
                styleOption.textVisible = True
                styleOption.state = styleOption.state | QStyle.State_Enabled
                style.drawControl(QStyle.CE_PushButton, styleOption, painter)
            else:
                QStyledItemDelegate.paint(self, painter, styleOption, index)

        else:
            QStyledItemDelegate.paint(painter, option, index)

        painter.restore()

    def createEditor(self, parent, option, index):

        currency = model.CURRENCY

        node = index.internalPointer()
        if node.type_info == 'CODE':
            if node.value_format == 'percent':
                editor = QDoubleSpinBox(parent)
                editor.setSuffix('%')
            elif node.value_format == 'integer':
                editor = QSpinBox(parent)
            else:
                editor = QDoubleSpinBox(parent)
            editor.setMaximum(100000000)
        elif node.type_info == 'BAREME':
            editor = QPushButton(parent)
            editor.setText('Editer')
            unit = None
            if node.value_type == 'monetary':
                unit = currency
            value = node._value
            value.marToMoy()
            self.baremeDialog = BaremeDialog(value, self._parent, unit = unit)
            self.connect(editor, SIGNAL('clicked()'), self.runBaremeDialog)
            self.connect(self.baremeDialog, SIGNAL('accepted()'), self.accepted)
            self.runBaremeDialog()
        else:
            editor = QStyledItemDelegate.createEditor(self, parent, option, index)
        return editor

    def accepted(self):
        self._parent.changed() # To send the signal to the parameter widget

    def setEditorData(self, editor, index):
        node = index.internalPointer()
        if node.type_info == 'BAREME':
            return
        if node.value_format == 'percent':
            editor.setValue(node.value*100)
        else:
            editor.setValue(node.value)

    def setModelData(self, editor, model, index):
        node = index.internalPointer()
        if node.type_info == 'BAREME':
            newValue = None
        elif node.value_format == 'percent':
            newValue = editor.value()*0.01
        else:
            newValue = editor.value()

        model.setData(index, to_qvariant(newValue))


    def runBaremeDialog(self):
        self.baremeDialog.exec_()

class BaremeColumnDelegate(QStyledItemDelegate):
    def __init__(self, parent = None):
        super(BaremeColumnDelegate, self).__init__(parent)

    def paint(self, painter, option, index):
        painter.save()
        palette = QApplication.palette()
        if index.isValid():
            color = palette.highlight().color() \
                if option.state & QStyle.State_Selected \
                else  QColor(Qt.white)
            painter.fillRect(option.rect, color)
            if (option.state and QStyle.State_Active):
                textColor = QPalette.HighlightedText if option.state & QStyle.State_Selected else QPalette.WindowText
            else:
                textColor = QPalette.WindowText

            col = index.column()
            val = from_qvariant(index.model().data(index))
            if col == 1:
                text = '%.2f %%  ' % (val*100)
            else:
                text = '%d ' % (val)

            QApplication.style().drawItemText(painter, option.rect, Qt.AlignRight | Qt.AlignVCenter,
                                              option.palette, True, text,
                                              textColor)
        else:
            QStyledItemDelegate.paint(painter, option, index)

        painter.restore()

    def createEditor(self, parent, option, index):
        col = index.column()
        if col == 1:
            editor = QDoubleSpinBox(parent)
            editor.setSuffix('%')
        else:
            editor = QSpinBox(parent)

        editor.setMaximum(100000000)

        return editor

    def setEditorData(self, editor, index):
        col = index.column()
        val = from_qvariant(index.model().data(index))
        if col == 1:
            editor.setValue(val*100)
        else:
            editor.setValue(val)

    def setModelData(self, editor, model, index):
        col = index.column()
        if col == 1:
            newValue = editor.value()*0.01
        else:
            newValue = editor.value()

        model.setData(index, to_qvariant(newValue))


class BaremeDialog(QDialog, Ui_BaremeDialog):
    def __init__(self, bareme, parent = None, unit = None):
        super(BaremeDialog, self).__init__(parent)
        self.setupUi(self)
        self._bareme = bareme
        self._bareme.unit = unit


        self._marModel = MarModel(self._bareme, self)
        self.marView.setModel(self._marModel)

        self._moyModel = MoyModel(self._marModel, self)
        self.moyView.setModel(self._moyModel)

        delegate = CustomDelegate(self)
        delegate.insertColumnDelegate(1, BaremeColumnDelegate(self))
        self.marView.setItemDelegate(delegate)

        delegate2 = CustomDelegate(self)
        delegate2.insertColumnDelegate(1, BaremeColumnDelegate(self))
        self.moyView.setItemDelegate(delegate2)

        self.connect(self._marModel, SIGNAL("dataChanged(QModelIndex, QModelIndex)"), self._moyModel.refresh)
        self.connect(self._moyModel, SIGNAL("dataChanged(QModelIndex, QModelIndex)"), self._marModel.refresh)
        self.connect(self.add_btn, SIGNAL('clicked()'), self.add_tranche)
        self.connect(self.rmv_btn, SIGNAL('clicked()'), self.rmv_tranche)

        if len(self._bareme.thresholds) <= 1:
            self.rmv_btn.setEnabled(False)

    def add_tranche(self):
        self._marModel.insertRows(0, 1)
        self.rmv_btn.setEnabled(True)

    def rmv_tranche(self):
        '''
        Removes last bareme tranche
        '''
        self._marModel.removeRows(0, 1)
        if len(self._bareme.thresholds) == 1:
            self.rmv_btn.setEnabled(False)

class MarModel(QAbstractTableModel):

    def __init__(self, bareme, parent = None):
        super(MarModel, self).__init__(parent)
        self._bareme = bareme

    def rowCount(self, parent):
        return len(self._bareme.thresholds)

    def columnCount(self, parent):
        return 2

    def headerData(self, section, orientation, role = Qt.DisplayRole ):
        if orientation == Qt.Horizontal:
            if role == Qt.DisplayRole:
                if   section == 0: return "Seuil"
                elif section == 1: return "Taux"

    def flags(self, index):
        return Qt.ItemIsEnabled | Qt.ItemIsSelectable |  Qt.ItemIsEditable

    def data(self, index, role = Qt.DisplayRole ):
        row = index.row()
        column = index.column()
        if role == Qt.DisplayRole or role == Qt.EditRole:
            if column == 0 :
                if (self._bareme.unit is not None) and (role == Qt.DisplayRole):

                    return to_qvariant( str(self._bareme.thresholds[row]) + ' ' + self._bareme.unit)
                else:
                    return to_qvariant(self._bareme.thresholds[row])
            if column == 1 :
                return to_qvariant(self._bareme.rates[row])


        if role == Qt.TextAlignmentRole:
            return Qt.AlignRight


    def insertRows(self, row, count, parent = QModelIndex() ):
        self.beginInsertRows(parent, row, row)
        if len(self._bareme.thresholds) == 0:
            s = 0
            t = 0
        else:
            s = self._bareme.thresholds[-1] + 1000
            t = self._bareme.rates[-1]

        self._bareme.addTranche(s ,t)
        self._bareme.marToMoy()
        self.endInsertRows()
        return True

    def removeRows(self, row, count, parent = QModelIndex() ):
        self.beginRemoveRows(parent, row, row)
        self._bareme.rmvTranche()
        self._bareme.marToMoy()
        self.endRemoveRows()
        return True

    def setData(self, index, value, role = Qt.EditRole):
        if role == Qt.EditRole:
            row = index.row()
            column = index.column()
            if column == 0 : self._bareme.setSeuil(row, from_qvariant(value))
            if column == 1 : self._bareme.setTaux(row, from_qvariant(value))
            self._bareme.marToMoy()
            self.dataChanged.emit(index, index)
            return True
        return False

    def refresh(self):
        self.beginResetModel()
        self.reset()
        self.endResetModel()

class MoyModel(QSortFilterProxyModel):
    def __init__(self, marModel, parent = None):
        super(MoyModel, self).__init__(parent)
        self.setSourceModel(marModel)
        self.source = self.sourceModel()
        self._bareme = self.source._bareme

#        self.setDynamicSortFilter(True)

    def rowCount(self, parent):
        return len(self._bareme.thresholds)

    def data(self, index, role = Qt.DisplayRole ):
        row = index.row()
        column = index.column()
        if role == Qt.DisplayRole or role == Qt.EditRole:
            if column == 0 :
                if self._bareme.unit is not None and role == Qt.DisplayRole:
                    return to_qvariant( str(self._bareme.thresholdsM[row]) + ' ' + self._bareme.unit)
                else:
                    return to_qvariant( str(self._bareme.thresholdsM[row]))
            if column == 1 : return to_qvariant(self._bareme.ratesM[row])

        if role == Qt.TextAlignmentRole:
            return Qt.AlignRight

    def setData(self, index, value, role = Qt.EditRole):
        row = index.row()
        column = index.column()
        if role == Qt.EditRole:
            if column == 0 :
                if row == self.rowCount(QModelIndex())-1:
                    return False
                self._bareme.setSeuilM(row, from_qvariant(value))
            if column == 1 :
                self._bareme.setTauxM(row, from_qvariant(value))

            self._bareme.moyToMar()
            self.dataChanged.emit(index, index)
            return True
        return False

    def refresh(self):
        self.beginResetModel()
        self.source.reset()
        self.endResetModel()
