import maya.cmds as mc #imports maya commands to be used here
import maya.OpenMayaUI as omui #imports maya open ui module to find main window
import shiboken2 #helps convert maya main window to the pyside type

from PySide2.QtWidgets import (QLineEdit, QMainWindow, QMessageBox, QWidget, QVBoxLayout, 
                               QHBoxLayout, QLabel, QSlider,
                               QPushButton) #imports all widgets needed
from PySide2.QtCore import Qt #imports values to configure widget

def GetMayaMainWindow()->QMainWindow:
    mayaMainWindow = omui.MQtUtil.mainWindow()
    return shiboken2.wrapInstance(int(mayaMainWindow), QMainWindow)

def DeleteWindowWithName(name):
    for window in GetMayaMainWindow().findChildren(QWidget, name):
        window.deleteLater()

class LimbRigger:
    def __init__(self):
        self.root = ""
        self.mid = ""
        self.end = ""
        self.controllerSize = 5

    def AutoFindJnts(self):
        self.root = mc.ls(sl=True, type="joint")[0]
        self.mid = mc.listRelatives(self.root, c=True, type="joint")[0]
        self.end = mc.listRelatives(self.mid, c=True, type="joint")[0]

    def CreateFKControlForJnt(self, jntName):
        ctrlName = "ac_fk_" + jntName
        ctrlGrpName = ctrlName + "_grp"
        mc.circle(nc=ctrlName, r=self.controllerSize, nr = (1,0,0))

        mc.group(ctrlName, n=ctrlGrpName)
        mc.matchTransform(ctrlGrpName, jntName)
        mc.orientConstraint(ctrlName, jntName)
        return ctrlName, ctrlGrpName

    def RigLimb(self):
        rootCtrl, rootCtrlGrp = self.CreateFKControlForJnt(self.root)
        midCtrl, midCtrlGrp = self.CreateFKControlForJnt(self.mid)
        endCtrl, endCtrlGrp = self.CreateFKControlForJnt(self.end)

        mc.parent(midCtrlGrp, rootCtrl)
        mc.parent(endCtrlGrp, midCtrl)

class QMayaWindow(QWidget):
    def __init__(self):
        DeleteWindowWithName(self.GetWindowHash())
        super().__init__(parent = GetMayaMainWindow())
        self.setWindowFlags(Qt.WindowType.Window)
        self.setObjectName(self.GetWindowHash())

        

    def GetWindowHash(self):
        return "valid crashout"

class LimbRigToolWidget(QMayaWindow):
    def __init__(self):
        super().__init__()
        self.rigger = LimbRigger()

        self.masterLayout = QVBoxLayout()
        self.setLayout(self.masterLayout)

        self.tipLabel = QLabel("Select the first joint of the limb")
        self.masterLayout.addWidget(self.tipLabel)

        self.jointSelectionText = QLineEdit()
        self.masterLayout.addWidget(self.jointSelectionText)
        self.jointSelectionText.setEnabled(False)

        self.autoFindBtn = QPushButton("Auto Find")
        self.masterLayout.addWidget(self.autoFindBtn)
        self.autoFindBtn.clicked.connect(self.AutoFindBtnClicked)

        ctrlSliderLayout = QHBoxLayout()

        self.ctrlSizeSlider = QSlider()
        self.ctrlSizeSlider.setValue(self.rigger.controllerSize)
        self.ctrlSizeSlider.valueChanged.connect(self.CtrlSizeValueChanged)
        self.ctrlSizeSlider.setRange(1, 30)
        self.ctrlSizeSlider.setOrientation(Qt.Horizontal)
        ctrlSliderLayout.addWidget(self.ctrlSizeSlider)
        self.ctrlSizeLabel = QLabel(f"{self.rigger.controllerSize}")
        ctrlSliderLayout.addWidget(self.ctrlSizeLabel)

        self.masterLayout.addLayout(ctrlSliderLayout)

        self.rigLimbBtn = QPushButton("Rig Limb")
        self.masterLayout.addWidget(self.rigLimbBtn)
        self.rigLimbBtn.clicked.connect(self.RigLimbBtnClicked)
        
        self.setWindowTitle("Limb Rigging Tool")

    def CtrlSizeValueChanged(self, newValue):
        self.rigger.controllerSize = newValue
        self.ctrlSizeLabel.setText(f"{self.rigger.controllerSize}")

    def RigLimbBtnClicked(self):
        self.rigger.RigLimb()

    def AutoFindBtnClicked(self):
        try:
            self.rigger.AutoFindJnts()
            self.jointSelectionText.setText(f"{self.rigger.root},{self.rigger.mid},{self.rigger.end}")
        except Exception as e:
            QMessageBox.critical(self, "Error", "you are an idiot :)")
        

limbRigToolWidget = LimbRigToolWidget()
limbRigToolWidget.show()
GetMayaMainWindow()

