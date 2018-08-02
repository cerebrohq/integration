# -*- coding: utf-8 -*-
from tentaculo.core import capp
from tentaculo.api import menu

"""
def draw_item(self, context):
	layout = self.layout
	layout.menu(CerebroMenu.bl_idname)
"""
if capp.HOST == capp.BLENDER:
	import bpy

	class CerebroTodo(bpy.types.Operator):
		bl_idname = "object.cerebro_todo"
		bl_label = "Todo list"

		def execute(self, context):
			menu.todolist()
			return {'FINISHED'}

	class CerebroLink(bpy.types.Operator):
		bl_idname = "object.cerebro_link"
		bl_label = "Link/Embed"

		def execute(self, context):
			menu.browser()
			return {'FINISHED'}

	class CerebroReport(bpy.types.Operator):
		bl_idname = "object.cerebro_report"
		bl_label = "Save as version"

		def execute(self, context):
			menu.createreport()
			return {'FINISHED'}

	class CerebroPublish(bpy.types.Operator):
		bl_idname = "object.cerebro_publish"
		bl_label = "Publish"

		def execute(self, context):
			menu.publish()
			return {'FINISHED'}

	class CerebroLogout(bpy.types.Operator):
		bl_idname = "object.cerebro_logout"
		bl_label = "Logout"

		def execute(self, context):
			menu.logout()
			return {'FINISHED'}

	class CerebroChdir(bpy.types.Operator):
		bl_idname = "object.cerebro_chdir"
		bl_label = "Change working directory"

		def execute(self, context):
			menu.workdir()
			return {'FINISHED'}

	class CerebroAbout(bpy.types.Operator):
		bl_idname = "object.cerebro_about"
		bl_label = "About"

		def execute(self, context):
			menu.about()
			return {'FINISHED'}

	class CerebroReload(bpy.types.Operator):
		bl_idname = "object.cerebro_reload"
		bl_label = "Reload"

		def execute(self, context):
			menu.reload()
			return {'FINISHED'}
	"""
	class CerebroMenu(bpy.types.Menu):
		bl_label = "Cerebro"
		bl_idname = "view3D.cerebro_menu"

		def draw(self, context):
			layout = self.layout

			layout.operator("object.cerebro_todo")
			layout.operator("object.cerebro_link")
			layout.operator("object.cerebro_report")
			layout.operator("object.cerebro_publish")
			layout.separator()
			layout.operator("object.cerebro_logout")
			layout.separator()
			layout.operator("object.cerebro_chdir")
			layout.separator()
			layout.operator("object.cerebro_about")
			if capp.DEBUG is True:
				layout.operator("object.cerebro_reload")

	bpy.utils.register_class(CerebroTodo)
	bpy.utils.register_class(CerebroLink)
	bpy.utils.register_class(CerebroReport)
	bpy.utils.register_class(CerebroPublish)
	bpy.utils.register_class(CerebroLogout)
	bpy.utils.register_class(CerebroChdir)
	bpy.utils.register_class(CerebroAbout)
	bpy.utils.register_class(CerebroReload)
	bpy.utils.register_class(CerebroMenu)
	bpy.types.INFO_HT_header.prepend(draw_item)
	"""

	class CerebroPanel(bpy.types.Panel):
		bl_space_type = "VIEW_3D"
		bl_region_type = "TOOLS"
		bl_label = "Cerebro Tentaculo"
		bl_context = "objectmode"
		bl_category = "Cerebro"

		def draw(self, context):
			layout = self.layout

			layout.operator("object.cerebro_todo")
			layout.operator("object.cerebro_link")
			layout.operator("object.cerebro_report")
			layout.operator("object.cerebro_publish")
			layout.separator()
			layout.operator("object.cerebro_logout")
			layout.separator()
			layout.operator("object.cerebro_chdir")
			layout.separator()
			layout.operator("object.cerebro_about")
			if capp.DEBUG is True:
				layout.operator("object.cerebro_reload")

	bpy.utils.register_class(CerebroTodo)
	bpy.utils.register_class(CerebroLink)
	bpy.utils.register_class(CerebroReport)
	bpy.utils.register_class(CerebroPublish)
	bpy.utils.register_class(CerebroLogout)
	bpy.utils.register_class(CerebroChdir)
	bpy.utils.register_class(CerebroAbout)
	bpy.utils.register_class(CerebroReload)
	bpy.utils.register_class(CerebroPanel)
