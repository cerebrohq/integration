# -*- coding: utf-8 -*-
import sys, os, ctypes, time
from tentaculo.api import standalone
from tentaculo.core import capp, utils

if capp.HOST == capp.MAYA:
	import maya.cmds as mc
	import maya.mel as mel
	import pymel.core as pm
	from shiboken import wrapInstance
	from maya import OpenMayaUI as omui
	from maya import OpenMaya as om

if capp.HOST == capp.MAYA2:
	import maya.cmds as mc
	import maya.mel as mel
	import pymel.core as pm
	from shiboken2 import wrapInstance
	from maya import OpenMayaUI as omui
	from maya import OpenMaya as om

if capp.HOST == capp.NUKE:
	import nuke
	import nukescripts

if capp.HOST == capp.HOUDINI:
	import hou

if capp.HOST == capp.MAX:
	import MaxPlus

if capp.HOST == capp.C4D:
	import c4d

if capp.HOST == capp.BLENDER:
	import bpy

from tentaculo import Qt
from tentaculo.Qt.QtGui import *
from tentaculo.Qt.QtCore import *
from tentaculo.Qt.QtWidgets import *

class Shot(object):

	__slots__ = ('parent', 'img', 'thumb', 'thumbSize', 'fname')

	def __init__(self, parent = None):
		self.clear()
		self.parent = parent

	def take(self):
		if capp.HOST == capp.MAYA or capp.HOST == capp.MAYA2:
			view = omui.M3dView.active3dView()
			view.setColorMask(1, 1, 1, 0)
			width = view.portWidth()
			height = view.portHeight()
			image = om.MImage()
			if view.getRendererName() == view.kViewport2Renderer:      
				image.create(view.portWidth(), view.portHeight(), 4, om.MImage.kFloat)
				view.readColorBuffer(image)
				image.convertPixelFormat(om.MImage.kByte)
			else:
				view.readColorBuffer(image)
			ptr = ctypes.cast(image.pixels().__long__(), ctypes.POINTER(ctypes.c_char))
			ptrAsStr = ctypes.string_at(ptr, width * height * 4)
			image = QImage(ptrAsStr, width, height, QImage.Format_RGB32)
			image = image.mirrored(horizontal=False, vertical=True)
			self.img = QPixmap.fromImage(image)
			self.set(self.save(self.img))

		elif capp.HOST == capp.NUKE:
			viewer = nuke.activeViewer()
			viewer_input = nuke.ViewerWindow.activeInput(viewer)
			viewer_node = nuke.activeViewer().node()

			if viewer_input is not None and viewer_node is not None:
				inputNode = nuke.Node.input(viewer_node, viewer_input)

				out_path = os.path.join(utils.tempdir(), "cerebro_screen.png").replace('\\', '/')

				node_write = nuke.nodes.Write(file = out_path, name = "cerebro_screen_node" , file_type = "png")
				node_write.setInput(0, inputNode)

				cur_frame = int(nuke.knob("frame"))
				nuke.execute(node_write.name(), cur_frame, cur_frame)

				self.set(out_path)
				# Cleanup
				for n in [node_write]:
					nuke.delete(n)

		elif capp.HOST == capp.HOUDINI:
			cur_desktop = hou.ui.curDesktop()
			frame = hou.frame()
			desktop = cur_desktop.name()
			panetab = cur_desktop.paneTabOfType(hou.paneTabType.SceneViewer).name()
			persp = cur_desktop.paneTabOfType(hou.paneTabType.SceneViewer).curViewport().name()
			camera_path = desktop + '.' + panetab + ".world." + persp

			out_path = os.path.join(utils.tempdir(), "cerebro_screen.jpg").replace('\\', '/')
			hou.hscript("viewwrite -r 800 600 -f {0} {1} {2} '{3}'".format(frame, frame, camera_path, out_path))

			self.set(out_path)

		elif capp.HOST == capp.MAX:
			view = MaxPlus.ViewportManager.GetActiveViewport()
			bm = MaxPlus.Factory.CreateBitmap()
			storage = MaxPlus.Factory.CreateStorage(7)
			info = storage.GetBitmapInfo()

			bm.SetStorage(storage)
			bm.DeleteStorage()

			res = view.GetDIB(info,bm)
			if res:
				#bm.Display()
				out_path = os.path.join(utils.tempdir(), "cerebro_screen.jpg")

				info.SetName(out_path)
				bm.OpenOutput(info)
				bm.Write(info)
				bm.Close(info)

				self.set(out_path)

		elif capp.HOST == capp.C4D:
			xres, yres = 800, 600
			doc = c4d.documents.GetActiveDocument()
			rd = c4d.documents.RenderData()
			rd[c4d.RDATA_XRES] = xres
			rd[c4d.RDATA_YRES] = yres
			rd[c4d.RDATA_RENDERENGINE] = c4d.RDATA_RENDERENGINE_PREVIEWHARDWARE

			bmp = c4d.bitmaps.BaseBitmap()
			if bmp.Init(xres, yres) == c4d.IMAGERESULT_OK:
				res = c4d.documents.RenderDocument(doc, rd.GetData(), bmp, c4d.RENDERFLAGS_EXTERNAL)
				if res == c4d.RENDERRESULT_OK:
					out_path = os.path.join(utils.tempdir(), "cerebro_screen.png")
					res = bmp.Save(out_path, c4d.FILTER_PNG)
					if res == c4d.IMAGERESULT_OK:
						self.set(out_path)

		elif capp.HOST == capp.BLENDER:
			out_path = os.path.join(utils.tempdir(), "cerebro_screen.png")

			for window in bpy.context.window_manager.windows:
				screen = window.screen
				for area in screen.areas:
					if area.type == 'VIEW_3D':
						for space in area.spaces:
							if space.type == 'VIEW_3D':
								for region in area.regions:
									if region.type == 'WINDOW':
										L_altBpyCtx = {							# defining alternative context (allowing modifications without altering real one)
										'area'      : area						# our 3D View (first found)
										, 'blend_data': bpy.context.blend_data	# just to suppress PyContext warning, doesn't seem to have any effect
										#, 'edit_text' : bpy.context.edit_text	# just to suppress PyContext warning, doesn't seem to have any effect
										, 'region'    : None					# just to suppress PyContext warning, doesn't seem to have any effect
										, 'scene'     : window.scene if utils.PY37 else screen.scene
										, 'space'     : space
										, 'screen'    : window.screen
										, 'window'    : window					# current window, could also copy context
										}
										bpy.ops.screen.screenshot(L_altBpyCtx, filepath = out_path, check_existing = False, full = False)
										break #XXX: limit to the window of the 3D View
								break #XXX: limit to the corresponding space (3D View)
						break #XXX: limit to the first 3D View (area)

			self.set(out_path)

		elif capp.HOST == capp.STANDALONE:
			out_path = os.path.join(utils.tempdir(), "standalone_screen.png")
			if standalone.message_function("screenshot", [out_path])[0]:
				self.set(out_path)

		elif capp.HOST == capp.KATANA:
			out_path = os.path.join(utils.tempdir(), "cerebro_screen.png")
			wnd = capp.app_window()
			pix = QPixmap.grabWindow(wnd.winId())
			pix.save(out_path)
			self.set(out_path)

		return self.img

	def activeScreen(self):
		
		out_path = os.path.join(utils.tempdir(), "screenshot-{0}.png".format(time.strftime("%Y-%m-%d--%H-%M-%S")))
				
		sw = SnippingWidget(self.parent, out_path)

		return out_path if sw.exec_() == QDialog.Accepted else None

	def clear(self):
		self.img = None
		self.thumb = None
		self.thumbSize = 512
		self.fname = None

	def set(self, fname = None):
		if fname is None: return None
		if not os.path.exists(fname): return None
		self.fname = fname
		self.img = QPixmap(self.fname)
		self.thumb = self.scale(self.img, self.thumbSize)

	def rescale(self, newwidth = 160):
		if self.img is None: return None
		self.img = self.scale(self.img, newwidth)
		return self.img

	def scale(self, img = None, newwidth = 160):
		result = None
		if img is None or img.isNull(): return result
		width = img.width()
		height = img.height()
		ratio = float(width)/float(height)
		newheight = newwidth/ratio
		thumb = img.scaled(newwidth, newheight, aspectRatioMode = Qt.KeepAspectRatio, transformMode = Qt.SmoothTransformation)
		return thumb

	def save(self, img = None):
		result = None
		if img is None: return result
		tmp = utils.tempdir()
		result = os.path.join(tmp, 'cerebro_screen.png')
		r = img.save(result)
		if r is not True: return None
		return result



def scale(imgpath = None, newwidth = 160):
	''' Standalone out-of-class version'''
	img = QPixmap(imgpath)
	result = None
	if img is None: return result
	width = img.width()
	height = img.height()
	ratio = float(width)/float(height)
	newheight = newwidth/ratio
	thumb = img.scaled(newwidth, newheight, aspectRatioMode = Qt.KeepAspectRatio, transformMode = Qt.SmoothTransformation)
	return thumb


class SnippingWidget(QDialog):

	def __init__(self, parent, out_path):
		super(SnippingWidget, self).__init__()
		self.setWindowTitle("Tentaculo screenshot")
		self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint)
		self.setAttribute(Qt.WA_TranslucentBackground, True)
		self.setWindowOpacity(0.5)

		self.QT5 = False
		self.deffered = False

		try:
			self.screen = QApplication.primaryScreen()
			self.QT5 = capp.QT5
		except:
			pass

		self.parent = parent
		self.out_path = out_path
		self.sr = QApplication.desktop().geometry()
		self.deffered = (self.sr.width() + self.sr.height()) > 6000
		self.setGeometry(self.sr)

		if self.deffered:
			self.up_timer = QTimer(self)
			self.up_timer.setInterval(20)
			self.up_timer.setSingleShot(True)
			self.up_timer.timeout.connect(self.update)

		pal = self.palette()
		pal.setColor(QPalette.Window, QColor("white"))
		self.setPalette(pal)

		if self.QT5:
			self.screen = QApplication.primaryScreen()
			window = self.parent.windowHandle() if hasattr(self.parent, "windowHandle") else None
			if window is not None:
				self.screen = window.screen()
		#	if self.screen is not None:
		#		self.sr = self.screen.availableGeometry()
		#	self.sr = QApplication.desktop().geometry()
		#else:
		#	self.sr = QApplication.desktop().availableGeometry(self.parent)

		self.begin = QPoint()
		self.end = QPoint()

	def capture(self):
		fullscreen = True
		if not self.begin.isNull() and self.begin != self.end:
			fullscreen = False
			x1 = min(self.begin.x(), self.end.x())
			y1 = min(self.begin.y(), self.end.y())
			x2 = max(self.begin.x(), self.end.x())
			y2 = max(self.begin.y(), self.end.y())

		self.setWindowOpacity(0.0)
		if self.QT5:
			if fullscreen:
				pix = self.screen.grabWindow(QApplication.desktop().winId(), self.sr.x(), self.sr.y(), self.sr.width(), self.sr.height())
			else:
				pix = self.screen.grabWindow(QApplication.desktop().winId(), self.sr.x() + x1, self.sr.y() + y1, x2 - x1, y2 - y1)
			pix.save(self.out_path)
		else:
			if fullscreen:
				pix = QPixmap.grabWindow(QApplication.desktop().winId(), self.sr.x(), self.sr.y(), self.sr.width(), self.sr.height())
			else:
				pix = QPixmap.grabWindow(QApplication.desktop().winId(), self.sr.x() + x1, self.sr.y() + y1, x2 - x1, y2 - y1)
			pix.save(self.out_path)

		self.accept()

	def paintEvent(self, event):
		qp = QPainter(self)

		rect = QRect(10, 10, 300, 50)

		qp.begin(self)
		qp.fillRect(qp.viewport(), Qt.white)

		font = qp.font()
		font.setPixelSize(18)
		qp.setFont(font)
		qp.setBrush(QColor("black"))
		qp.setPen(Qt.NoPen)
		qp.drawRect(rect)
		qp.setPen(QPen(QColor("white"), 2))
		qp.drawText(rect, Qt.AlignVCenter | Qt.AlignLeft, "ESC to cancel\nENTER to capture entire screen")

		if not self.begin.isNull():
			selection = QRect(self.begin, self.end)
			qp.setPen(QPen(Qt.red, 2))
			qp.setBrush(Qt.black)
			qp.drawRect(selection)
			qp.setCompositionMode(QPainter.CompositionMode_Clear)
			qp.setPen(Qt.NoPen)
			qp.drawRect(selection)

		qp.end()

	def keyPressEvent(self, event):
		if event.key() == Qt.Key_Enter or event.key() == Qt.Key_Return:
			self.begin = QPoint()
			self.end = QPoint()
			event.accept()
			self.capture()
		super(SnippingWidget, self).keyPressEvent(event)

	def mousePressEvent(self, event):
		self.begin = event.pos()
		self.end = self.begin
		self.update()

	def mouseMoveEvent(self, event):
		if not self.begin.isNull():
			self.end = event.pos()
			if self.deffered:
				self.up_timer.start()
			else:
				self.update()

	def mouseReleaseEvent(self, event):
		self.capture()

	def showEvent(self, event):
		QApplication.setOverrideCursor(QCursor(Qt.CrossCursor))
		super(SnippingWidget, self).showEvent(event)

	def closeEvent(self, event):
		QApplication.restoreOverrideCursor()
		super(SnippingWidget, self).closeEvent(event)

	def hideEvent(self, event):
		QApplication.restoreOverrideCursor()
		super(SnippingWidget, self).hideEvent(event)
