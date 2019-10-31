# -*- coding: utf-8 -*-
from tentaculo.core import capp
from tentaculo.api import menu

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

	class CerebroMenu(bpy.types.Menu):
		bl_label = "Cerebro"
		bl_description = "Cerebro Tentaculo connector plugin"
		bl_idname = "OBJECT_MT_TENTACULO"

		def draw(self, context):
			layout = self.layout
			layout.menu(CerebroSubmenu.bl_idname)

	class CerebroSubmenu(bpy.types.Menu):
		bl_label = "Tentaculo"
		bl_description = "Cerebro Tentaculo"
		bl_idname = "OBJECT_MT_TENTACULO_SUB"

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

	def register():
		unregister()
		bpy.utils.register_class(CerebroTodo)
		bpy.utils.register_class(CerebroLink)
		bpy.utils.register_class(CerebroReport)
		bpy.utils.register_class(CerebroPublish)
		bpy.utils.register_class(CerebroLogout)
		bpy.utils.register_class(CerebroChdir)
		bpy.utils.register_class(CerebroAbout)
		bpy.utils.register_class(CerebroReload)
		bpy.utils.register_class(CerebroSubmenu)
		bpy.utils.register_class(CerebroMenu)
		bpy.types.TOPBAR_MT_editor_menus.append(CerebroMenu.draw)

	def unregister():
		if hasattr(bpy.types, "CerebroMenu"):
			bpy.types.TOPBAR_MT_editor_menus.remove(bpy.types.CerebroMenu.draw)
			bpy.utils.unregister_class(CerebroTodo)
			bpy.utils.unregister_class(CerebroLink)
			bpy.utils.unregister_class(CerebroReport)
			bpy.utils.unregister_class(CerebroPublish)
			bpy.utils.unregister_class(CerebroLogout)
			bpy.utils.unregister_class(CerebroChdir)
			bpy.utils.unregister_class(CerebroAbout)
			bpy.utils.unregister_class(CerebroReload)
			bpy.utils.unregister_class(CerebroMenu)
			bpy.utils.unregister_class(CerebroSubmenu)
