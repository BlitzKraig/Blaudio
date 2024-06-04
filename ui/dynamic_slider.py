# Form implementation generated from reading ui file 'ui/dynamic_slider.ui'
#
# Created by: PyQt6 UI code generator 6.7.0
#
# WARNING: Any manual changes made to this file will be lost when pyuic6 is
# run again.  Do not edit this file unless you know what you are doing.


from PyQt6 import QtCore, QtGui, QtWidgets


class Ui_DynamicSliderContainer(object):
    def setupUi(self, DynamicSliderContainer):
        DynamicSliderContainer.setObjectName("DynamicSliderContainer")
        DynamicSliderContainer.resize(100, 335)
        DynamicSliderContainer.setMinimumSize(QtCore.QSize(100, 0))
        DynamicSliderContainer.setMaximumSize(QtCore.QSize(100, 16777215))
        DynamicSliderContainer.setAutoFillBackground(True)
        self.horizontalLayout = QtWidgets.QHBoxLayout(DynamicSliderContainer)
        self.horizontalLayout.setContentsMargins(0, 0, 0, 0)
        self.horizontalLayout.setSpacing(0)
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.dynamicSliderVertLayout = QtWidgets.QVBoxLayout()
        self.dynamicSliderVertLayout.setSpacing(0)
        self.dynamicSliderVertLayout.setObjectName("dynamicSliderVertLayout")
        self.dynamicSliderLabel = QtWidgets.QLabel(parent=DynamicSliderContainer)
        self.dynamicSliderLabel.setMinimumSize(QtCore.QSize(100, 0))
        self.dynamicSliderLabel.setMaximumSize(QtCore.QSize(100, 16777215))
        self.dynamicSliderLabel.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.dynamicSliderLabel.setObjectName("dynamicSliderLabel")
        self.dynamicSliderVertLayout.addWidget(self.dynamicSliderLabel, 0, QtCore.Qt.AlignmentFlag.AlignHCenter)
        spacerItem = QtWidgets.QSpacerItem(20, 6, QtWidgets.QSizePolicy.Policy.Minimum, QtWidgets.QSizePolicy.Policy.Fixed)
        self.dynamicSliderVertLayout.addItem(spacerItem)
        self.dynamicSliderMainHorzLayout = QtWidgets.QHBoxLayout()
        self.dynamicSliderMainHorzLayout.setSpacing(0)
        self.dynamicSliderMainHorzLayout.setObjectName("dynamicSliderMainHorzLayout")
        self.dynamicSliderLeftButton = QtWidgets.QPushButton(parent=DynamicSliderContainer)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Policy.Minimum, QtWidgets.QSizePolicy.Policy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.dynamicSliderLeftButton.sizePolicy().hasHeightForWidth())
        self.dynamicSliderLeftButton.setSizePolicy(sizePolicy)
        self.dynamicSliderLeftButton.setMinimumSize(QtCore.QSize(20, 0))
        self.dynamicSliderLeftButton.setMaximumSize(QtCore.QSize(20, 16777215))
        self.dynamicSliderLeftButton.setFlat(True)
        self.dynamicSliderLeftButton.setObjectName("dynamicSliderLeftButton")
        self.dynamicSliderMainHorzLayout.addWidget(self.dynamicSliderLeftButton)
        self.dynamicSliderVolSlider = QtWidgets.QSlider(parent=DynamicSliderContainer)
        self.dynamicSliderVolSlider.setMaximum(100)
        self.dynamicSliderVolSlider.setOrientation(QtCore.Qt.Orientation.Vertical)
        self.dynamicSliderVolSlider.setObjectName("dynamicSliderVolSlider")
        self.dynamicSliderMainHorzLayout.addWidget(self.dynamicSliderVolSlider)
        self.dynamicSliderRightButton = QtWidgets.QPushButton(parent=DynamicSliderContainer)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Policy.Minimum, QtWidgets.QSizePolicy.Policy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.dynamicSliderRightButton.sizePolicy().hasHeightForWidth())
        self.dynamicSliderRightButton.setSizePolicy(sizePolicy)
        self.dynamicSliderRightButton.setMinimumSize(QtCore.QSize(20, 0))
        self.dynamicSliderRightButton.setMaximumSize(QtCore.QSize(20, 16777215))
        self.dynamicSliderRightButton.setFlat(True)
        self.dynamicSliderRightButton.setObjectName("dynamicSliderRightButton")
        self.dynamicSliderMainHorzLayout.addWidget(self.dynamicSliderRightButton)
        self.dynamicSliderVertLayout.addLayout(self.dynamicSliderMainHorzLayout)
        spacerItem1 = QtWidgets.QSpacerItem(20, 6, QtWidgets.QSizePolicy.Policy.Minimum, QtWidgets.QSizePolicy.Policy.Fixed)
        self.dynamicSliderVertLayout.addItem(spacerItem1)
        self.dynamicSliderTopButtonHorzLayout = QtWidgets.QHBoxLayout()
        self.dynamicSliderTopButtonHorzLayout.setSpacing(0)
        self.dynamicSliderTopButtonHorzLayout.setObjectName("dynamicSliderTopButtonHorzLayout")
        self.dynamicSliderMuteButton = QtWidgets.QPushButton(parent=DynamicSliderContainer)
        self.dynamicSliderMuteButton.setMinimumSize(QtCore.QSize(30, 0))
        self.dynamicSliderMuteButton.setMaximumSize(QtCore.QSize(30, 16777215))
        font = QtGui.QFont()
        font.setPointSize(10)
        self.dynamicSliderMuteButton.setFont(font)
        self.dynamicSliderMuteButton.setText("🔇")
        self.dynamicSliderMuteButton.setObjectName("dynamicSliderMuteButton")
        self.dynamicSliderTopButtonHorzLayout.addWidget(self.dynamicSliderMuteButton)
        self.dynamicSliderVertLayout.addLayout(self.dynamicSliderTopButtonHorzLayout)
        self.dynamicSliderBottomButtonHorzLayout = QtWidgets.QHBoxLayout()
        self.dynamicSliderBottomButtonHorzLayout.setSpacing(0)
        self.dynamicSliderBottomButtonHorzLayout.setObjectName("dynamicSliderBottomButtonHorzLayout")
        self.dynamicSliderDeleteButton = QtWidgets.QPushButton(parent=DynamicSliderContainer)
        self.dynamicSliderDeleteButton.setMinimumSize(QtCore.QSize(30, 0))
        self.dynamicSliderDeleteButton.setMaximumSize(QtCore.QSize(20, 16777215))
        self.dynamicSliderDeleteButton.setObjectName("dynamicSliderDeleteButton")
        self.dynamicSliderBottomButtonHorzLayout.addWidget(self.dynamicSliderDeleteButton)
        self.dynamicSliderEditButton = QtWidgets.QPushButton(parent=DynamicSliderContainer)
        self.dynamicSliderEditButton.setMinimumSize(QtCore.QSize(30, 0))
        self.dynamicSliderEditButton.setMaximumSize(QtCore.QSize(20, 16777215))
        self.dynamicSliderEditButton.setObjectName("dynamicSliderEditButton")
        self.dynamicSliderBottomButtonHorzLayout.addWidget(self.dynamicSliderEditButton)
        self.dynamicSliderVertLayout.addLayout(self.dynamicSliderBottomButtonHorzLayout)
        self.horizontalLayout.addLayout(self.dynamicSliderVertLayout)

        self.retranslateUi(DynamicSliderContainer)
        QtCore.QMetaObject.connectSlotsByName(DynamicSliderContainer)

    def retranslateUi(self, DynamicSliderContainer):
        _translate = QtCore.QCoreApplication.translate
        DynamicSliderContainer.setWindowTitle(_translate("DynamicSliderContainer", "Form"))
        self.dynamicSliderLabel.setText(_translate("DynamicSliderContainer", "Game"))
        self.dynamicSliderLeftButton.setText(_translate("DynamicSliderContainer", "<"))
        self.dynamicSliderRightButton.setText(_translate("DynamicSliderContainer", ">"))
        self.dynamicSliderDeleteButton.setText(_translate("DynamicSliderContainer", "🗑️"))
        self.dynamicSliderEditButton.setText(_translate("DynamicSliderContainer", "📝"))
