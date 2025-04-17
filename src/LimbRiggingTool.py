from PySide2.QtGui import QColor
import maya.cmds as mc #imports maya commands to be used here
import maya.OpenMayaUI as omui #imports maya open ui module to find main window
import shiboken2 #helps convert maya main window to the pyside type
import maya.mel as mel
from maya.OpenMaya import MVector

from PySide2.QtWidgets import (QColorDialog, QLineEdit, QMainWindow, QMessageBox, QWidget, QVBoxLayout, 
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
    
    def CreateBoxController(self, name):
        mel.eval(f"curve -n {name} -d 1 -p 0.5 0.5 0.5 -p 0.5 0.5 -0.5 -p -0.5 0.5 -0.5 -p -0.5 0.5 0.5 -p 0.5 0.5 0.5 -p 0.5 -0.5 0.5 -p -0.5 -0.5 0.5 -p -0.5 0.5 0.5 -p -0.5 -0.5 0.5 -p -0.5 -0.5 -0.5 -p -0.5 0.5 -0.5 -p -0.5 -0.5 -0.5 -p 0.5 -0.5 -0.5 -p 0.5 0.5 -0.5 -p 0.5 -0.5 -0.5 -p 0.5 -0.5 0.5 -k 0 -k 1 -k 2 -k 3 -k 4 -k 5 -k 6 -k 7 -k 8 -k 9 -k 10 -k 11 -k 12 -k 13 -k 14 -k 15 ;")
        mc.scale(self.controllerSize, self.controllerSize, self.controllerSize, name)
        mc.makeIdentity(name, apply = True) # this is freeze transformation

        grpName = name + "_grp"
        mc.group(name, n=grpName)
        return name, grpName
    
    def CreatePlusController(self, name):
        mel.eval(f"curve -n {name} -d 1 -p 1 1 0 -p 1 3 0 -p -1 3 0 -p -1 1 0 -p -3 1 0 -p -3 -1 0 -p -1 -1 0 -p -1 -3 0 -p 1 -3 0 -p 1 -1 0 -p 3 -1 0 -p 3 1 0 -p 1 1 0 -k 0 -k 1 -k 2 -k 3 -k 4 -k 5 -k 6 -k 7 -k 8 -k 9 -k 10 -k 11 -k 12 ;")


        grpName = name + "_grp"
        mc.group(name, n=grpName)
        return name, grpName
    
    def GetObjectLoc(self, objectName)->MVector:
        x, y, z = mc.xform(objectName, q=True, t=True, ws=True) #get the world space translation of the objectName
        return MVector(x, y, z)
    
    def PrintMVector(self, vectorToPrint):
        print(f"<{vectorToPrint.x}, {vectorToPrint.y}, {vectorToPrint.z}>")

    def RigLimb(self, r, g, b):
        rootFKCtrl, rootFKCtrlGrp = self.CreateFKControlForJnt(self.root)
        midFKCtrl, midFKCtrlGrp = self.CreateFKControlForJnt(self.mid)
        endFKCtrl, endFKCtrlGrp = self.CreateFKControlForJnt(self.end)

        mc.parent(midFKCtrlGrp, rootFKCtrl)
        mc.parent(endFKCtrlGrp, midFKCtrl)

        ikEndCtrl = "ac_ik_" + self.end
        ikEndCtrl, ikEndCtrlGrp = self.CreateBoxController(ikEndCtrl)
        mc.matchTransform(ikEndCtrlGrp, self.end)
        endOrientConstraint = mc.orientConstraint(ikEndCtrl, self.end)[0]

        rootJntLoc = self.GetObjectLoc(self.root)
        endJntLoc = self.GetObjectLoc(self.end)

        rootToEndVec = endJntLoc - rootJntLoc

        ikHandleName = "ikHandle_" + self.end
        mc.ikHandle(n=ikHandleName, sj=self.root, ee = self.end, sol="ikRPsolver")
        ikPoleVectorVals = mc.getAttr(ikHandleName + ".poleVector")[0]
        ikPoleVector = MVector(ikPoleVectorVals[0], ikPoleVectorVals[1], ikPoleVectorVals[2])

        ikPoleVector.normalize()
        ikPoleVectorCtrlLoc = rootJntLoc + rootToEndVec / 2 + ikPoleVector * rootToEndVec.length() 

        ikPoleVectorCtrlName = "ac_ik_" + self.mid
        mc.spaceLocator(n=ikPoleVectorCtrlName)
        ikPoleVectorCtrlGrp = ikPoleVectorCtrlName + "_grp"
        mc.group(ikPoleVectorCtrlName, n=ikPoleVectorCtrlGrp)
        mc.setAttr(ikPoleVectorCtrlGrp+".t", ikPoleVectorCtrlLoc.x, ikPoleVectorCtrlLoc.y, ikPoleVectorCtrlLoc.z, typ = "double3")
        mc.poleVectorConstraint(ikPoleVectorCtrlName, ikHandleName)

        ikfkBlendCtrlName = "ac_ikfk_blend_" + self.root
        ikfkBlendCtrlName, ikfkBlendCtrlGrp = self.CreatePlusController(ikfkBlendCtrlName)
        ikfkBlendCtrLoc = rootJntLoc + MVector(rootJntLoc.x, 0, rootJntLoc.z)
        mc.setAttr(ikfkBlendCtrlGrp+".t", ikfkBlendCtrLoc.x, ikfkBlendCtrLoc.y, ikfkBlendCtrLoc.z, typ="double3")

        ikfkBlendAttrName = "ikfkBlend"
        mc.addAttr(ikfkBlendCtrlName, ln=ikfkBlendAttrName, min=0, max=1, k=True)
        ikfkBlendAttr = ikfkBlendCtrlName + "." + ikfkBlendAttrName

        mc.expression(s=f"{ikHandleName}.ikBlend = {ikfkBlendAttr}")
        mc.expression(s=f"{ikEndCtrlGrp}.v = {ikPoleVectorCtrlGrp}.v = {ikfkBlendAttr}")
        mc.expression(s=f"{rootFKCtrlGrp}.v = 1 - {ikfkBlendAttr}")
        mc.expression(s=f"{endOrientConstraint}.{endFKCtrl}W0 = 1-{ikfkBlendAttr}")
        mc.expression(s=f"{endOrientConstraint}.{ikEndCtrl}W1 = {ikfkBlendAttr}")

        mc.parent(ikHandleName, ikEndCtrl)
        mc.setAttr(ikHandleName+".v", 0)

        topGrpName = self.root + "_rig_grp"
        mc.group([rootFKCtrlGrp,ikEndCtrlGrp, ikPoleVectorCtrlGrp, ikfkBlendCtrlGrp], n= topGrpName)
        mc.setAttr(topGrpName+".overrideEnabled", 1)
        mc.setAttr(topGrpName+".overrideRGBColors", 1)
        mc.setAttr(topGrpName+".overrideColorRGB", r, g, b, type="double3")
        print("jobs Done!")
        print("jobs Done!")
        print("jobs Done!")

class ColorPicker(QWidget):
    def __init__(self):
        super().__init__()
        self.masterLayout = QVBoxLayout()
        self.setLayout(self.masterLayout)
        self.colorPickerBtn = QPushButton()
        self.colorPickerBtn.setStyleSheet(f"background-color: black")
        self.masterLayout.addWidget(self.colorPickerBtn)
        self.colorPickerBtn.clicked.connect(self.ColorPickerBtnClicked)
        self.color = QColor(0,0,0)

    def ColorPickerBtnClicked(self):
        self.color = QColorDialog.getColor()
        self.colorPickerBtn.setStyleSheet(f"background-color:{self.color.name()}")

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

