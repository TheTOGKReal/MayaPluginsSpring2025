from Pyside2.QtGui import QColor
import maya.cmds as mc
import maya.mel as mel
from maya.OpenMaya import MVector
import maya.OpenMayaUI as omui

from PySide2.QtWidgets import (QLineEdit, QMainWindow, QMessageBox, QWidget, QVBoxLayout, 
                               QHBoxLayout, QLabel, QSlider,
                               QPushButton)

from PySide2.QtCore import Qt
from MayaUtils import QMayaWindow

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
    

class ProxyRigger:
    def CreateProxyRigFromSelectedMesh(self):
        self.jnts = jnts

        print(f"start build with mesh: {self.model}, skin: {self.skin} and joints: {self.jnts}")

        jntVertMap = self.GenerateJntVertDict()
        segments = []
        ctrls = []
        for jnt, verts in jntVertMap.items():
            print(f"joint {jnt} controls {verts} primarily")
            newSeg = self.CreateProxyModelForJntAndVerts(jnt, verts)
            if newSeg is None:
                continue

            newSkinCluster = mc.skinCluster(self.jnts, newSeg)[0]
            mc.copySkinWeights(ss=self.skin, ds=newSkinCluster, nm=True, sa="closestPoint", ia="closestJoint")
            segments.append(newSeg)

            ctrlLocator = "ac_" + jnt + "_proxy"
            mc.spaceLocator(n=ctrlLocator)
            ctrlLocatorGrp = ctrlLocator + "_grp"
            mc.group(ctrlLocator, n=ctrlLocatorGrp)
            mc.matchTransform(ctrlLocatorGrp, jnt)

            visibilityAttr = "vis"
            mc.addAttr(ctrlLocator, ln=visibilityAttr, min=0, max=1, dv=1, k=True)
            mc.connectAttr(ctrlLocator + "." + visibilityAttr, newSeg + ".v")
            ctrls.append(ctrlLocatorGrp)

        proxyTopGrp = self.model + "_proxy_grp"
        mc.group(ctrls, n=proxyTopGrp)

        ctrlTopGrp = "ac_" + self.model + "_proxy_grp"
        mc.group(ctrls, n=ctrlTopGrp)

        globalProxyCtrl = "ac_" + self.model + "_proxy_global"
        mc.circle(n=globalProxyCtrl, r=30)
        mc.parent(proxyTopGrp, globalProxyCtrl)
        mcparent(ctrlTopGrp, globalProxyCtrl)
        mc.settAttr(proxyTopGrp + ".inheritsTransform", 0)

        mc.addAttr(globalProxyCtrl, ln=visibilityAttr, min=0, max=1, dv=1, k=True)
        mc.connectAttr(globalProxyCtrl + "."+visibilityAttr, proxyTopGrp + ".v")

    def CreateProxyModelForJntAndVerts(self, jnt, verts):
        if not verts:
            return None
        
        faces = mc.polyListComponentConversion(verts, fromVertex=True, toFace=True)
        faces = mc.ls(faces, fl=True)

        labels = set()
        for face in faces:
            labels.add(face.replace(self.model, ""))

        dup = mc.duplicate(self.model)[0]

class ProxyRiggerWidget(QMayaWindow):
    def __init__(self):
        super().__init__()
        self.proxyRigger = ProxyRigger()
        self.setWindowTitle("Proxy Rigger")
        self.masterLayout = QVBoxLayout()
        self.setLayout(self.masterLayout)
        generateProxyRigBtn = QPushButton("Generate Proxy Rig")
        self. masterLayout.addWidget(generalProxyRigBtn)
        generateProxyRigBtn.clicked.connect(self.GenerateProxyRigButtonClicked)

    def GenerateProxyRigButtonClicked(self):
        self.proxyRigger.CreatePRoxyRigFromSelectedMesh()

    def GetWindowHash(self):
        return ""
        
proxyRiggerWidget = ProxyRiggerWidget()
proxyRiggerWidget.show()