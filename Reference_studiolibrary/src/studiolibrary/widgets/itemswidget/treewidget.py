# Copyright 2020 by Kurt Rathjen. All Rights Reserved.
#
# This library is free software: you can redistribute it and/or modify it 
# under the terms of the GNU Lesser General Public License as published by 
# the Free Software Foundation, either version 3 of the License, or 
# (at your option) any later version. This library is distributed in the 
# hope that it will be useful, but WITHOUT ANY WARRANTY; without even the 
# implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. 
# See the GNU Lesser General Public License for more details.
# You should have received a copy of the GNU Lesser General Public
# License along with this library. If not, see <http://www.gnu.org/licenses/>.

import logging
from functools import partial

from studiovendor.Qt import QtGui
from studiovendor.Qt import QtCore
from studiovendor.Qt import QtWidgets
from studiovendor import six

import studioqt

from .groupitem import GroupItem
from .itemviewmixin import ItemViewMixin


logger = logging.getLogger(__name__)


class TreeWidget(ItemViewMixin, QtWidgets.QTreeWidget):

    itemMoved = QtCore.Signal(object)
    itemDropped = QtCore.Signal(object)
    itemClicked = QtCore.Signal(object)
    itemDoubleClicked = QtCore.Signal(object)

    DEFAULT_DRAG_THRESHOLD = 10

    def __init__(self, *args):
        QtWidgets.QTreeWidget.__init__(self, *args)
        ItemViewMixin.__init__(self)

        self._headerLabels = []
        self._hiddenColumns = {}

        self._rubberBand = None
        self._rubberBandStartPos = None
        self._rubberBandColor = QtGui.QColor(QtCore.Qt.white)
        self._customSortOrder = []

        self._drag = None
        self._dragStartPos = None
        self._dragStartIndex = None
        self._dropEnabled = True

        self.setAutoScroll(False)
        self.setMouseTracking(True)
        self.setSortingEnabled(False)
        self.setSelectionMode(QtWidgets.QListWidget.ExtendedSelection)
        self.setVerticalScrollMode(QtWidgets.QAbstractItemView.ScrollPerPixel)

        header = self.header()
        header.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        header.customContextMenuRequested.connect(self.showHeaderMenu)

        self.setAcceptDrops(True)
        self.setDragEnabled(True)
        self.setDragDropMode(QtWidgets.QAbstractItemView.DragDrop)

        self.itemClicked.connect(self._itemClicked)
        self.itemDoubleClicked.connect(self._itemDoubleClicked)

    def drawRow(self, painter, options, index):
        item = self.itemFromIndex(index)
        item.paintRow(painter, options, index)

    def settings(self):
        """
        Return the current state of the widget.

        :rtype: dict
        """
        settings = {}

        # settings["headerState"] = self.header().saveState()

        settings["columnSettings"] = self.columnSettings()

        return settings

    def setSettings(self, settings):
        """
        Set the current state of the widget.

        :type settings: dict
        :rtype: None
        """
        columnSettings = settings.get("columnSettings", {})
        self.setColumnSettings(columnSettings)

        return settings

    def _itemClicked(self, item):
        """
        Triggered when the user clicks on an item.

        :type item: QtWidgets.QTreeWidgetItem
        :rtype: None
        """
        item.clicked()

    def _itemDoubleClicked(self, item):
        """
        Triggered when the user double clicks on an item.

        :type item: QtWidgets.QTreeWidgetItem
        :rtype: None
        """
        item.doubleClicked()

    def clear(self, *args):
        """
        Reimplementing so that all dirty objects can be removed.

        :param args:
        :rtype: None
        """
        QtWidgets.QTreeWidget.clear(self, *args)
        self.cleanDirtyObjects()

    def setItems(self, items):
        selectedItems = self.selectedItems()
        self.takeTopLevelItems()
        self.addTopLevelItems(items)
        self.setItemsSelected(selectedItems, True)

    def setItemsSelected(self, items, value, scrollTo=True):
        """
        Select the given items.

        :type items: list[studioqt.ItemsWidget]
        :type value: bool
        :type scrollTo: bool

        :rtype: None
        """
        for item in items:
            item.setSelected(value)

        if scrollTo:
            self.itemsWidget().scrollToSelectedItem()

    def selectedItem(self):
        """
        Return the last selected non-hidden item.

        :rtype: studioqt.Item
        """
        items = self.selectedItems()

        if items:
            return items[-1]

        return None

    def selectedItems(self):
        """
        Return all the selected items.

        :rtype: list[studioqt.Item]
        """
        items = []
        items_ = QtWidgets.QTreeWidget.selectedItems(self)

        for item in items_:
            if not isinstance(item, GroupItem):
                items.append(item)

        return items

    def rowAt(self, pos):
        """
        Return the row for the given pos.

        :type pos: QtCore.QPoint
        :rtype: int
        """
        item = self.itemAt(pos)
        return self.itemRow(item)

    def itemRow(self, item):
        """
        Return the row for the given item.

        :type item: studioqt.TreeWidgetItem
        :rtype: int
        """
        index = self.indexFromItem(item)
        return index.row()

    def items(self):
        """
        Return a list of all the items in the tree widget.

        :rtype: lsit[studioqt.TreeWidgetItem]
        """
        items = []

        for item in self._items():
            if not isinstance(item, GroupItem):
                items.append(item)

        return items

    def _items(self):
        """
        Return a list of all the items in the tree widget.

        :rtype: lsit[studioqt.TreeWidgetItem]
        """
        return self.findItems(
            "*",
            QtCore.Qt.MatchWildcard | QtCore.Qt.MatchRecursive
        )

    def takeTopLevelItems(self):
        """
        Take all items from the tree widget.

        :rtype: list[QtWidgets.QTreeWidgetItem]
        """
        items = []
        for item in self._items():
            # For some reason its faster to take from index 1.
            items.append(self.takeTopLevelItem(1))
        items.append(self.takeTopLevelItem(0))
        return items

    def textFromColumn(self, column, split=None, duplicates=False):
        """
        Return all the data for the given column

        :type column: int or str
        :type split: str
        :type duplicates: bool
        :rtype: list[str]
        """
        items = self.items()
        results = self.textFromItems(
            items,
            column,
            split=split,
            duplicates=duplicates,
        )
        return results

    def textFromItems(self, items, column, split=None, duplicates=False):
        """
        Return all the text data for the given items and given column

        :type items: list[Item]
        :type column: int or str
        :type split: str
        :type duplicates: bool
        :rtype: list[str]
        """
        results = []

        for item in items:
            text = item.text(column)

            if text and split:
                results.extend(text.split(split))
            elif text:
                results.append(text)

        if not duplicates:
            results = list(set(results))

        return results

    def columnLabels(self):
        """
        Return all header labels for the tree widget.

        :rtype: list[str]
        """
        return self.headerLabels()

    def labelFromColumn(self, column):
        """
        Return the column label for the given column.

        :type column: int
        :rtype: str
        """
        if column is not None:
            return self.headerItem().text(column)

    def headerLabels(self):
        """
        Return all the header labels.

        :rtype: str
        """
        return self._headerLabels

    def isHeaderLabel(self, label):
        """
        Return True if the given label is a valid header label.
        
        :type label: str
        :rtype: None 
        """
        return label in self._headerLabels

    def _removeDuplicates(self, labels):
        """
        Removes duplicates from a list in Python, whilst preserving order.

        :type labels: list[str]
        :rtype: list[str]
        """
        s = set()
        sadd = s.add
        return [x for x in labels if x.strip() and not (x in s or sadd(x))]

    def setHeaderLabels(self, labels):
        """
        Set the header for each item in the given label list.

        :type labels: list[str]
        :rtype: None
        """
        labels = self._removeDuplicates(labels)

        if "Custom Order" not in labels:
            labels.append("Custom Order")

        self.setColumnHidden("Custom Order", True)

        columnSettings = self.columnSettings()

        QtWidgets.QTreeWidget.setHeaderLabels(self, labels)

        self._headerLabels = labels
        self.updateColumnHidden()

        self.setColumnSettings(columnSettings)

    def columnFromLabel(self, label):
        """
        Return the column for the given label.

        :type label: str
        :rtype: int
        """
        try:
            return self._headerLabels.index(label)
        except ValueError:
            return -1

    def showAllColumns(self):
        """
        Show all available columns.

        :rtype: None
        """
        for column in range(self.columnCount()):
            self.setColumnHidden(column, False)

    def hideAllColumns(self):
        """
        Hide all available columns.

        :rtype: None
        """
        oneShown = False
        for column in range(0, self.columnCount()):
            label = self.labelFromColumn(column)
            if not oneShown and not self._hiddenColumns[label]:
                oneShown = True
                continue
            self.setColumnHidden(column, True)

    def updateColumnHidden(self):
        """
        Update the hidden state for all the current columns.
        
        :rtype: None 
        """
        self.showAllColumns()
        columnLabels = self._hiddenColumns.keys()

        for columnLabel in columnLabels:
            self.setColumnHidden(columnLabel, self._hiddenColumns[columnLabel])

    def setColumnHidden(self, column, value):
        """
        Set the give column to show or hide depending on the specified value.

        :type column: int or str
        :type value: bool
        :rtype: None
        """
        if isinstance(column, six.string_types):
            column = self.columnFromLabel(column)

        label = self.labelFromColumn(column)
        self._hiddenColumns[label] = value

        QtWidgets.QTreeWidget.setColumnHidden(self, column, value)

        # Make sure the column is not collapsed
        width = self.columnWidth(column)
        if width < 5:
            width = 100
            self.setColumnWidth(column, width)

    def resizeColumnToContents(self, column):
        """
        Resize the given column to the data of that column.

        :type column: int or text
        :rtype: None
        """
        width = 0
        for item in self.items():
            text = item.text(column)
            font = item.font(column)
            metrics = QtGui.QFontMetricsF(font)
            textWidth = metrics.width(text) + item.padding()
            width = max(width, textWidth)

        self.setColumnWidth(column, width)

    # ----------------------------------------------------------------------
    # Support for custom orders
    # ----------------------------------------------------------------------

    def isSortByCustomOrder(self):
        """
        Return true if items are currently sorted by custom order.

        :rtype: bool
        """
        return "Custom Order" in str(self.itemsWidget().dataset().sortBy())

    def setItemsCustomOrder(self, items, row=1, padding=5):
        """
        Set the custom order for the given items by their list order.

        :rtype: None
        """
        for item in items:
            item.itemData()["Custom Order"] = str(row).zfill(padding)
            row += 1

    # def updateCustomOrder(self):
    #     """
    #     Update any empty custom orders.
    #
    #     :rtype: None
    #     """
    #     row = 1
    #     padding = 5
    #
    #     items = self.items()
    #     columnLabel = "Custom Order"
    #
    #     for item in items:
    #         customOrder = item.text(columnLabel)
    #
    #         if not customOrder:
    #             item.setText(columnLabel, str(row).zfill(padding))
    #         row += 1

    def itemsCustomOrder(self):
        """
        Return the items sorted by the custom order data.

        :rtype: list[studioqt.Item]
        """
        items = self.items()

        def sortKey(item):
            return item.itemData().get("Custom Order", 0)

        customOrder = sorted(items, key=sortKey)

        return customOrder

    def moveItems(self, items, itemAt):
        """
        Move the given items to the position of the destination row.

        :type items: list[studioqt.Item]
        :type itemAt: studioqt.Item
        :rtype: None
        """
        row = 0
        orderedItems = self.itemsCustomOrder()

        if itemAt:
            row = orderedItems.index(itemAt)

        removedItems = []
        for item in items:
            index = orderedItems.index(item)
            removedItems.append(orderedItems.pop(index))

        for item in removedItems:
            orderedItems.insert(row, item)

        self.setItemsCustomOrder(orderedItems)

        for item in items:
            item.setSelected(True)

        self.itemsWidget().scrollToSelectedItem()

    # ----------------------------------------------------------------------
    # Support for menus
    # ----------------------------------------------------------------------

    def showHeaderMenu(self, pos):
        """
        Creates and show the header menu at the cursor pos.

        :rtype: QtWidgets.QMenu
        """
        header = self.header()
        column = header.logicalIndexAt(pos)

        menu = self.createHeaderMenu(column)

        menu.addSeparator()

        submenu = self.createHideColumnMenu()
        menu.addMenu(submenu)

        point = QtGui.QCursor.pos()
        menu.exec_(point)

    def createHeaderMenu(self, column):
        """
        Creates a new header menu.

        :rtype: QtWidgets.QMenu
        """
        menu = QtWidgets.QMenu(self)
        label = self.labelFromColumn(column)

        shownCount = self.countShownColumn()

        action = menu.addAction("Hide '{0}'".format(label))
        callback = partial(self.setColumnHidden, column, True)
        action.setEnabled(shownCount > 1)
        action.triggered.connect(callback)

        menu.addSeparator()

        action = menu.addAction('Resize to Contents')
        callback = partial(self.resizeColumnToContents, column)
        action.triggered.connect(callback)

        return menu

    def columnSettings(self):
        """
        Return the settings for each column.

        :rtype: dict
        """
        columnSettings = {}

        for column in range(self.columnCount()):

            label = self.labelFromColumn(column)
            hidden = self.isColumnHidden(column)
            width = self.columnWidth(column)

            columnSettings[label] = {
                "hidden": hidden,
                "width": width,
                "index": column,
            }

        return columnSettings

    def setColumnSettings(self, settings):
        """
        Set the settings for each column.

        :type settings: dict
        :type: None
        """
        for label in settings:
            if self.isHeaderLabel(label):
                column = self.columnFromLabel(label)

                width = settings[label].get("width", 100)
                if width < 5:
                    width = 100
                self.setColumnWidth(column, width)

                hidden = settings[label].get("hidden", False)
                self.setColumnHidden(column, hidden)
            else:
                msg = 'Cannot set the column setting for the header label "%s"'
                logger.debug(msg, label)

    def createHideColumnMenu(self):
        """
        Create the hide column menu.

        :rtype: QtWidgets.QMenu
        """
        menu = QtWidgets.QMenu("Show/Hide Column", self)

        action = menu.addAction("Show All")
        action.triggered.connect(self.showAllColumns)

        action = menu.addAction("Hide All")
        action.triggered.connect(self.hideAllColumns)

        menu.addSeparator()

        shownCount = self.countShownColumn()

        for column in range(self.columnCount()):

            label = self.labelFromColumn(column)
            isHidden = self.isColumnHidden(column)

            action = menu.addAction(label)
            action.setCheckable(True)
            action.setChecked(not isHidden)

            callback = partial(self.setColumnHidden, column, not isHidden)
            action.setEnabled(shownCount > 1 or isHidden)
            action.triggered.connect(callback)

        return menu

    def countShownColumn(self):
        shownCount = 0
        for column in range(0, self.columnCount()):
            label = self.labelFromColumn(column)
            if not self._hiddenColumns[label]:
                shownCount += 1
        return shownCount
    # ----------------------------------------------------------------------
    # Support for copying item data to the clipboard.
    # ----------------------------------------------------------------------

    def createCopyTextMenu(self):
        """
        Create a menu to copy the selected items data to the clipboard.

        :rtype: QtWidgets.QMenu
        """
        menu = QtWidgets.QMenu("Copy Text", self)

        if self.selectedItems():

            for column in range(self.columnCount()):
                label = self.labelFromColumn(column)
                action = menu.addAction(label)
                callback = partial(self.copyText, column)
                action.triggered.connect(callback)

        else:
            action = menu.addAction("No items selected")
            action.setEnabled(False)

        return menu

    def copyText(self, column):
        """
        Copy the given column text to clipboard.

        :type column: int or text
        :rtype: None
        """
        items = self.selectedItems()
        text = "\n".join([item.text(column) for item in items])

        clipBoard = QtWidgets.QApplication.clipboard()
        clipBoard.setText(text, QtGui.QClipboard.Clipboard)

    # ----------------------------------------------------------------------
    # Override events for mixin.
    # ----------------------------------------------------------------------

    def mousePressEvent(self, event):
        """
        Triggered when the user presses the mouse button for the viewport.

        :type event: QtWidgets.QMouseEvent
        :rtype: None
        """
        item = self.itemAt(event.pos())
        if not item:
            self.clearSelection()

        ItemViewMixin.mousePressEvent(self, event)
        if event.isAccepted():
            QtWidgets.QTreeWidget.mousePressEvent(self, event)
            if item:
                item.setSelected(True)

        self.endDrag()
        self._dragStartPos = event.pos()

        isLeftButton = self.mousePressButton() == QtCore.Qt.LeftButton
        isItemDraggable = item and item.dragEnabled()
        isSelectionEmpty = not self.selectedItems()

        if isLeftButton and (isSelectionEmpty or not isItemDraggable):
            self.rubberBandStartEvent(event)

    def mouseMoveEvent(self, event):
        """
        Triggered when the user moves the mouse over the current viewport.

        :type event: QtWidgets.QMouseEvent
        :rtype: None
        """
        if not self.isDraggingItems():

            isLeftButton = self.mousePressButton() == QtCore.Qt.LeftButton

            if isLeftButton and self.rubberBand().isHidden() and self.selectedItems():
                self.startDrag(event)
            else:
                ItemViewMixin.mouseMoveEvent(self, event)
                QtWidgets.QTreeWidget.mouseMoveEvent(self, event)

            if isLeftButton:
                self.rubberBandMoveEvent(event)

    def mouseReleaseEvent(self, event):
        """
        Triggered when the user releases the mouse button on the viewport.

        :type event: QtWidgets.QMouseEvent
        :rtype: None
        """
        item = self.itemAt(event.pos())
        items = self.selectedItems()

        ItemViewMixin.mouseReleaseEvent(self, event)

        if item not in items:
            if event.button() != QtCore.Qt.MidButton:
                QtWidgets.QTreeWidget.mouseReleaseEvent(self, event)
        elif not items:
            QtWidgets.QTreeWidget.mouseReleaseEvent(self, event)

        self.endDrag()
        self.rubberBand().hide()
    
    def rubberBandStartEvent(self, event):
        """
        Triggered when the user presses an empty area.

        :type event: QtWidgets.QMouseEvent
        :rtype: None
        """
        self._rubberBandStartPos = event.pos()
        rect = QtCore.QRect(self._rubberBandStartPos, QtCore.QSize())

        rubberBand = self.rubberBand()
        rubberBand.setGeometry(rect)
        rubberBand.show()

    def rubberBandMoveEvent(self, event):
        """
        Triggered when the user moves the mouse over the current viewport.

        :type event: QtWidgets.QMouseEvent
        :rtype: None
        """
        if self.rubberBand() and self._rubberBandStartPos:
            rect = QtCore.QRect(self._rubberBandStartPos, event.pos())
            rect.adjust(0, 30, 0, 30)
            rect = rect.normalized()
            self.rubberBand().setGeometry(rect)

            selectedItems = self.selectedItems()
            for selectedItem in selectedItems:
                rect = self.visualRect(self.indexFromItem(selectedItem))
                self.repaint(rect)

    def setDropEnabled(self, value):
        """
        :type value: bool
        :rtype: None
        """
        self._dropEnabled = value

    def dropEnabled(self):
        """
        :rtype: bool
        """
        return self._dropEnabled

    def dragThreshold(self):
        """
        :rtype: int
        """
        return self.DEFAULT_DRAG_THRESHOLD

    def mimeData(self, items):
        """
        :type items: list[studioqt.Item]
        :rtype: QtCore.QMimeData
        """
        mimeData = QtCore.QMimeData()

        urls = [item.url() for item in items]
        text = "\n".join([item.mimeText() for item in items])

        mimeData.setUrls(urls)
        mimeData.setText(text)

        return mimeData

    def dropEvent(self, event):
        """
        This event handler is called when the drag is dropped on this widget.

        :type event: QtWidgets.QDropEvent
        :rtype: None
        """
        item = self.itemAt(event.pos())
        selectedItems = self.selectedItems()

        if selectedItems and item:
            if self.treeWidget().isSortByCustomOrder():
                self.moveItems(selectedItems, item)
            else:
                msg = "You can only re-order items when sorting by custom order."
                logger.info(msg)

        if item:
            item.dropEvent(event)

        self.itemDropped.emit(event)

    def dragMoveEvent(self, event):
        """
        This event handler is called if a drag is in progress.

        :type event: QtGui.QDragMoveEvent
        :rtype: None
        """
        mimeData = event.mimeData()

        if (mimeData.hasText() or mimeData.hasUrls()) and self.dropEnabled():
            event.accept()
        else:
            event.ignore()

    def dragEnterEvent(self, event):
        """
        This event handler is called when the mouse enters this widget
        while a drag is in pregress.

        :type event: QtGui.QDragEnterEvent
        :rtype: None
        """
        mimeData = event.mimeData()

        if (mimeData.hasText() or mimeData.hasUrls()) and self.dropEnabled():
            event.accept()
        else:
            event.ignore()

    def isDraggingItems(self):
        """
        Return true if the user is currently dragging items.

        :rtype: bool
        """
        return bool(self._drag)

    def startDrag(self, event):
        """
        Starts a drag using the given event.

        :type event: QtCore.QEvent
        :rtype: None
        """
        if not self.dragEnabled():
            return

        if self._dragStartPos and hasattr(event, "pos"):

            item = self.itemAt(event.pos())

            if item and item.dragEnabled():

                self._dragStartIndex = self.indexAt(event.pos())

                point = self._dragStartPos - event.pos()
                dt = self.dragThreshold()

                if point.x() > dt or point.y() > dt or point.x() < -dt or point.y() < -dt:

                    items = self.selectedItems()
                    mimeData = self.mimeData(items)

                    pixmap = self.dragPixmap(item, items)
                    hotSpot = QtCore.QPoint(pixmap.width() / 2, pixmap.height() / 2)

                    self._drag = QtGui.QDrag(self)
                    self._drag.setPixmap(pixmap)
                    self._drag.setHotSpot(hotSpot)
                    self._drag.setMimeData(mimeData)
                    self._drag.start(QtCore.Qt.MoveAction)

    def endDrag(self):
        """
        Ends the current drag.

        :rtype: None
        """
        logger.debug("End Drag")
        self._dragStartPos = None
        self._dragStartIndex = None
        if self._drag:
            del self._drag
            self._drag = None

    def dragPixmap(self, item, items):
        """
        Show the drag pixmap for the given item.

        :type item: studioqt.Item
        :type items: list[studioqt.Item]
        
        :rtype: QtGui.QPixmap
        """
        item.dragProcess(True)
        rect = self.visualRect(self.indexFromItem(item))

        pixmap = QtGui.QPixmap()
        pixmap = pixmap.grabWidget(self, rect)

        if len(items) > 1:
            cWidth = 35
            cPadding = 5
            cText = str(len(items))
            cX = pixmap.rect().center().x() - float(cWidth / 2)
            cY = pixmap.rect().top() + cPadding
            cRect = QtCore.QRect(cX, cY, cWidth, cWidth)

            painter = QtGui.QPainter(pixmap)
            painter.setRenderHint(QtGui.QPainter.Antialiasing)

            painter.setPen(QtCore.Qt.NoPen)
            painter.setBrush(self.itemsWidget().backgroundSelectedColor())
            painter.drawEllipse(cRect.center(), float(cWidth / 2),
                                float(cWidth / 2))

            font = QtGui.QFont('Serif', 12, QtGui.QFont.Light)
            painter.setFont(font)
            painter.setPen(self.itemsWidget().textSelectedColor())
            painter.drawText(cRect, QtCore.Qt.AlignCenter, str(cText))

        item.dragProcess(False)

        return pixmap

# ---------------------------------------------------------------------
    # Support for a custom colored rubber band.
    # ---------------------------------------------------------------------

    def createRubberBand(self):
        """
        Create a new instance of the selection rubber band.

        :rtype: QtWidgets.QRubberBand
        """
        rubberBand = QtWidgets.QRubberBand(QtWidgets.QRubberBand.Rectangle, self)
        palette = QtGui.QPalette()
        color = self.rubberBandColor()
        palette.setBrush(QtGui.QPalette.Highlight, QtGui.QBrush(color))
        rubberBand.setPalette(palette)
        return rubberBand

    def setRubberBandColor(self, color):
        """
        Set the color for the rubber band.

        :type color: QtGui.QColor
        :rtype: None
        """
        self._rubberBand = None
        self._rubberBandColor = color

    def rubberBandColor(self):
        """
        Return the rubber band color for this widget.

        :rtype: QtGui.QColor
        """
        return self._rubberBandColor

    def rubberBand(self):
        """
        Return the selection rubber band for this widget.

        :rtype: QtWidgets.QRubberBand
        """
        if not self._rubberBand:
            #self.setSelectionRectVisible(False)
            self._rubberBand = self.createRubberBand()

        return self._rubberBand