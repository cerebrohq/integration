import os, shutil
from distutils import dir_util

COPY_LIST = ["elements", "environments", "frames", "jobs", "palette-library", "PALETTE_LIST", "scene.elementTable", "scene.versionTable"]

def copy_tree(src, dst):
	if src is None or dst is None or not os.path.isdir(src):
		raise Exception("Invalid arguments for copy_tree(): {0} : {1}".format(src, dst))
		
	try:
		if not os.path.exists(dst):
			os.makedirs(dst)
	except Exception as err:
		raise Exception("Error creating folder tree: {0}".format(str(err)))
		
	for rec in os.listdir(src):
		if rec not in COPY_LIST: continue
		
		path_src = os.path.join(src, rec)
		path_dst = os.path.join(dst, rec)
		
		#try:
		#	if os.path.exists(path_dst):
		#		os.remove(path_dst) if os.path.isfile(path_dst) else shutil.rmtree(path_dst)
		#except Exception as err:
		#	raise Exception("Error removing old files: {0}".format(str(err)))
		
		try:
			shutil.copy(path_src, path_dst) if os.path.isfile(path_src) else dir_util.copy_tree(path_src, path_dst)
		except Exception as err:
			raise Exception("Error copying files: {0}".format(str(err)))

			

def open_pre(task_info, arg):
	verdir = os.path.join(os.path.dirname(arg["original_file_path"]), os.path.splitext(os.path.basename(arg["original_file_path"]))[0])
	
	copy_tree(verdir, os.path.dirname(arg["local_file_path"]))
	
	return arg

def version_pre(task_info, arg):
	verdir = os.path.join(os.path.dirname(arg["version_file_path"]), os.path.splitext(os.path.basename(arg["version_file_path"]))[0])
	
	copy_tree(os.path.dirname(arg["local_file_path"]), verdir)
	
	return arg

def publish_pre(task_info, arg):
	verdir = os.path.join(os.path.dirname(arg["version_file_path"]), os.path.splitext(os.path.basename(arg["version_file_path"]))[0])
	pubdir = os.path.join(os.path.dirname(arg["publish_file_path"]), os.path.splitext(os.path.basename(arg["publish_file_path"]))[0])
	
	copy_tree(os.path.dirname(arg["local_file_path"]), pubdir)
	copy_tree(os.path.dirname(arg["local_file_path"]), verdir)
	
	return arg
