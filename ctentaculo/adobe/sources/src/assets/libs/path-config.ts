import { transliterate as tr } from 'transliteration'
import fs from 'fs-extra'
import path from 'path'
import { exec } from 'child_process'
import _ from 'lodash'
import {
  APPS,
  HOST_ID,
  NET_MODE,
  OS,
  OS_BITS,
  MIRADA_PATH_MAPPING,
  CTENTACULO_LOCATION,
} from '@/pages/consts'
import CerebroConfig from './cerebro-config'
import Processor from './processor'
import Helpers from './helpers'

export default class PathConfig extends CerebroConfig {
  tasks: any = {}
  type: string = ''
  downloadFolder: string = ''

  constructor(configFile, type, downloadFolder) {
    super('', {})
    this.type = type
    this.downloadFolder = downloadFolder
    if (type === 'db') {
      this.configPath = ''
    } else {
      this.configPath = configFile
    }
    try {
      var configStr =
        type === 'db'
          ? configFile
          : this.configPath
          ? fs.readFileSync(this.configPath, 'utf8')
          : ''
      try {
        this.config = JSON.parse(configStr)
      } catch (error) {
        console.error(error)
        console.info(
          /*eslint-disable */
          "Failed parse 'path_config.json'. Uses default configuration.",
        )
      }
    } catch (error) {
      console.error(error)
      console.info(
        /*eslint-disable */
        "Could't open 'path_config.json'. Uses default configuration.",
      )
    }
  }

  replaceVariables(task, str) {
    var taskParents = _.compact(path.join(task.parent, task.name).split('\\'))
    try {
      return str
        .replace(/\$\(url\[(\d+)\]\)/g, function(match, index) {
          if (+index >= taskParents.length) throw Error()
          return taskParents[+index]
        })
        .replace(/\$\(task_name\)/g, task.name)
        .replace(/\$\(task_path\)/g, task.parent + task.name)
        .replace(
          /\$\(task_parent_name\)/g,
          _.last(_.compact(task.parent.split('/'))),
        )
        .replace(/\$\(task_parent_path\)/g, task.parent.replace(/\/$/g, ''))
        .replace(/\$\(soft_folder\)/g, this.getSoftFolder())
        .replace(/\$\(([a-zA-Z_-]+)\)/g, function(variable, name) {
          return process.env[name] || ''
        })
    } catch (e) {
      console.error(e)
      return null
    }
  }

  getProcessor(processor) {
    var processorPath = this.getProcessorPath(processor)
    var processorMethod = this.getProcessorMethod(processor)
    if (this.isRemoteMode()) return null
    if (!processorPath) return null
    if (!processorMethod) return null
    if (typeof processorPath !== 'string') return null
    if (typeof processorMethod !== 'string') return null
    processorPath = processorPath.replace(
      /%([^%]+)%/g,
      (_, n) => process.env[n] || '',
    )
    if (!path.isAbsolute(processorPath)) {
      if (CTENTACULO_LOCATION) {
        processorPath = path.resolve(CTENTACULO_LOCATION, processorPath)
      } else {
        console.error('CTENTACULO_LOCATION not specified')
        return null
      }
    }
    if (fs.existsSync(processorPath)) {
      try {
        return new Processor(processorPath, processorMethod)
      } catch (error) {
        console.error(error)
        return null
      }
    } else {
      return null
    }
  }

  getProcessorMethod(processor) {
    if (this.isRemoteMode()) return null
    return this.get(
      'processors.' +
        APPS[HOST_ID] +
        '.' +
        processor.toLowerCase() +
        '.function',
      null,
    )
  }

  getProcessorPath(processor) {
    return this.get(
      'processors.' +
        APPS[HOST_ID] +
        '.' +
        processor.toLowerCase() +
        '.script_path',
      null,
    )
  }

  getNetmode() {
    if (!this.config) return NET_MODE.REMOTE
    var netMode = this.get('net_mode.' + APPS[HOST_ID], 'REMOTE').toUpperCase()
    return NET_MODE[netMode] || NET_MODE.REMOTE
  }

  getSoftFolder() {
    if (!this.config || this.isRemoteMode()) return ''
    var softFolder = this.get('soft_folder.' + APPS[HOST_ID], '')
    return softFolder
  }

  getTransMode() {
    if (!this.config || this.isRemoteMode()) return false
    var TransMode = this.get('trans_mode.' + APPS[HOST_ID], true)
    if (TransMode == 'True') TransMode = true
    if (TransMode == 'False') TransMode = false
    return TransMode
  }

  getValidPath(task) {
    var projectPath = this.getProjectPath(task)
    if (!projectPath) return null
    if (projectPath.validPath) return projectPath.validPath
    var validPath = null
    for (var i = 0; i < projectPath.paths.length; i++) {
      if (fs.existsSync(projectPath.paths[i])) {
        validPath = projectPath.paths[i]
        break
      }
    }
    if (validPath) projectPath.validPath = validPath
    return validPath
  }

  getTaskPath(task) {
    var fullPath: any = null
    if (this.isRemoteMode()) {
      fullPath = Helpers.pathJoin(this.downloadFolder, task.parent, task.name)
    } else {
      fullPath = this.getFullPublishPath(task, this.getTransMode())
    }
    return fullPath
  }

  getVersionPrefix(task) {
    if (!this.config || this.isRemoteMode()) return '_v'
    var filePath = this.getFilePath(task)
    if (!filePath) return '_v'
    return filePath.ver_prefix
  }

  getVersionPadding(task) {
    if (!this.config || this.isRemoteMode()) return 3
    var filePath = this.getFilePath(task)
    if (!filePath) return 3
    return filePath.ver_padding
  }

  getPublishPath(task) {
    if (!this.config || this.isRemoteMode()) return ''
    var filePath = this.getFilePath(task)
    if (!filePath) return null
    return this.getTransMode() ? tr(filePath.publish) : filePath.publish
  }

  getFullPublishPath(task, translit = true) {
    if (!this.config || this.isRemoteMode()) return ''
    var projectPath = this.getValidPath(task)
    if (!projectPath) throw Error('Not have valid project paths')
    var filePath = this.getFilePath(task)
    if (!filePath) throw Error('Task not configured')
    if (!filePath.publish) throw Error('Task not configure publish folder')
    var fullPath = path.join(projectPath, filePath.publish)
    return translit && this.getTransMode() ? tr(fullPath) : fullPath
  }

  getVersionPath(task) {
    if (!this.config || this.isRemoteMode()) return ''
    var filePath = this.getFilePath(task)
    if (!filePath) return null
    return this.getTransMode() ? tr(filePath.version) : filePath.version
  }

  validateTask(task) {
    if (!this.config || this.isRemoteMode()) return true
    var filePath = this.getFilePath(task)
    return filePath ? true : false
  }

  getVersionFolder(task) {
    if (!this.config || this.isRemoteMode()) return ''
    var projectPath = this.getValidPath(task)
    return Helpers.pathJoin(projectPath, this.getVersionPath(task))
  }

  getPublishFolder(task) {
    if (!this.config || this.isRemoteMode()) return ''
    var projectPath = this.getValidPath(task)
    return Helpers.pathJoin(projectPath, this.getPublishPath(task))
  }

  getFileVersionFolder(task, filename) {
    if (!this.config || this.isRemoteMode()) return ''
    return Helpers.pathJoin(
      this.getVersionFolder(task),
      this.getTransMode() ? tr(filename) : filename,
    )
  }

  getFilePublishFolder(task, filename) {
    if (!this.config || this.isRemoteMode()) return ''
    return Helpers.pathJoin(
      this.getPublishFolder(task),
      this.getTransMode() ? tr(filename) : filename,
    )
  }

  getFilePath(task) {
    var existsInfo = this.tasks[task.uid] || {}
    if (!existsInfo.filePath) {
      var filePaths = this.get('file_path', [])
      var filePath = filePaths.filter(filePath => {
        var folderPath = this.replaceVariables(task, filePath.folder_path)
        return (
          filePath.folder_path.indexOf(folderPath) != -1 &&
          filePath.task_activity == task.activity
        )
      }, this)
      if (filePath.length == 0) {
        filePath = filePaths.filter(function(filePath) {
          return (
            filePath.folder_path == '' &&
            filePath.task_activity == task.activity
          )
        })
      }
      if (filePath.length == 0) {
        filePath = filePaths.filter(function(filePath) {
          return filePath.folder_path == '' && filePath.task_activity == ''
        })
      }
      filePath = filePath.length > 0 ? Object.assign({}, filePath[0]) : null
      if (!filePath) return null
      if (!filePath.publish && !filePath.version)
        throw new Error('Fill field "publish" or "version"')
      if (
        (filePath.publish && typeof filePath.publish != 'string') ||
        (filePath.version && typeof filePath.version != 'string')
      )
        throw new Error('Fill field "publish" or "version"')
      filePath.name_editable =
        filePath.name_editable == undefined ? false : filePath.name_editable
      filePath.ver_padding =
        filePath.ver_padding == undefined ? 3 : filePath.ver_padding
      filePath.ver_prefix =
        filePath.ver_prefix == undefined ? '' : filePath.ver_prefix
      if (typeof filePath.name_editable != 'boolean')
        throw new Error('Fill field "name_editable"')
      if (
        typeof filePath.ver_padding != 'number' &&
        typeof filePath.ver_padding == 'string' &&
        (Number.isNaN(+filePath.ver_padding) ||
          filePath.ver_padding.trim() == '')
      )
        throw new Error('Fill field "ver_padding"')
      if (typeof filePath.ver_prefix != 'string')
        throw new Error('Fill field "ver_prefix"')
      if (typeof filePath.name != 'string' && !Array.isArray(filePath.name))
        throw new Error('Fill field "name"')
      if (typeof filePath.name == 'string')
        filePath.name = [this.replaceVariables(task, filePath.name)]
      if (Array.isArray(filePath.name))
        filePath.name = _.compact(
          filePath.name.map(o => {
            return this.replaceVariables(task, o)
          }),
        )
      filePath.version =
        filePath.version === undefined
          ? undefined
          : this.replaceVariables(task, filePath.version)
      filePath.publish =
        filePath.publish === undefined
          ? undefined
          : this.replaceVariables(task, filePath.publish)
      existsInfo.filePath = filePath
    }
    this.tasks[task.uid] = existsInfo
    return existsInfo.filePath
  }
  getProjectPath(task) {
    var existsInfo = this.tasks[task.uid] || {}
    if (!existsInfo.projectPath) {
      var project = task.parent.split('/')
      project = project.length < 2 ? '' : project[1]
      var activity = task.activity
      var projectPaths = this.get('project_path', [])
      var foundedProjectPath = projectPaths.filter(function(projectPath) {
        return (
          projectPath.project_name == project &&
          projectPath.task_activity == activity
        )
      })
      if (foundedProjectPath.length == 0) {
        foundedProjectPath = projectPaths.filter(function(projectPath) {
          return (
            projectPath.project_name == '' &&
            projectPath.task_activity == activity
          )
        })
      }
      if (foundedProjectPath.length == 0) {
        foundedProjectPath = projectPaths.filter(function(projectPath) {
          return (
            projectPath.project_name == '' && projectPath.task_activity == ''
          )
        })
      }
      foundedProjectPath =
        foundedProjectPath.length > 0 ? foundedProjectPath[0] : null
      existsInfo.projectPath = foundedProjectPath
    }
    this.tasks[task.uid] = existsInfo
    return existsInfo.projectPath
  }

  getLocalFilePath(task, filename, localPath) {
    var destPath = ''
    var relativePath = ''
    switch (this.getNetmode()) {
      case NET_MODE.NETWORK:
        var validPath = this.getValidPath(task)
        var filePath = this.getFilePath(task)
        if (!validPath || !filePath) return null
        relativePath = filePath.version || filePath.publish
        relativePath = this.getTransMode() ? tr(relativePath) : relativePath
        destPath = path.join(validPath, relativePath)
        break
      case NET_MODE.LOCAL:
        relativePath = path.join(task.parent, task.name)
        relativePath = this.getTransMode() ? tr(relativePath) : relativePath
        destPath = path.join(localPath, relativePath)
        break
      case NET_MODE.REMOTE:
        relativePath = path.join(task.parent, task.name)
        relativePath = this.getTransMode() ? tr(relativePath) : relativePath
        destPath = path.join(localPath, relativePath)
        break
    }
    var prefix = this.getVersionPrefix(task)
    var padding = this.getVersionPadding(task)
    var regExp = new RegExp(prefix + '(\\d{' + padding + '})(\\..+)?$')
    var fileext = path.extname(filename)
    filename =
      path.basename(filename, fileext).replace(regExp, '') + '.vlocal' + fileext
    return path.join(destPath, filename)
  }

  hasPublish(task) {
    if (!this.config || this.isRemoteMode()) return false
    var filePath = this.getFilePath(task)
    if (!filePath) return false
    return filePath.publish ? true : false
  }

  isPublishFile(task, filename) {
    var prefix = this.getVersionPrefix(task)
    var padding = this.getVersionPadding(task)
    var regExp = new RegExp(prefix + '(\\d{' + padding + '})(\\..+)?$')
    if (this.isRemoteMode()) {
      return !regExp.test(filename)
    } else {
      var publishPath = this.getPublishPath(task)
      if (publishPath === '') return true
      if (!publishPath) return false
      var fullPublishPath = path
        .join(this.getValidPath(task), publishPath)
        .replace(/\\/g, '/')
      return filename.indexOf(fullPublishPath) != -1 && !regExp.test(filename)
    }
  }
  isVersionFile(task, filename) {
    var prefix = this.getVersionPrefix(task)
    var padding = this.getVersionPadding(task)
    var regExp = new RegExp(prefix + '(\\d{' + padding + '})(\\..+)?$')
    if (this.isRemoteMode()) {
      return regExp.test(filename)
    } else {
      var versionPath = this.getVersionPath(task)
      if (!versionPath) return false
      if (versionPath == '') return false
      var fullVersionPath = path
        .join(this.getValidPath(task), versionPath)
        .replace(/\\/g, '/')
      return filename.indexOf(fullVersionPath) != -1 && regExp.test(filename)
    }
  }

  isRemoteMode() {
    return this.getNetmode() == NET_MODE.REMOTE
  }
  isNET_MODE() {
    return this.getNetmode() == NET_MODE.NETWORK
  }
  isLocalMode() {
    return this.getNetmode() == NET_MODE.LOCAL
  }
  getStatusFilter() {
    if (!this.config || this.isRemoteMode()) return []
    var statusFilter = this.get('status_filter', [])
    return Array.isArray(statusFilter) ? statusFilter : []
  }

  getPublishStatus(task) {
    if (!this.config || this.isRemoteMode()) return null
    const filePath = this.getFilePath(task)
    return filePath && filePath.publish_status
  }

  filenames(task) {
    if (!this.config || this.isRemoteMode())
      return this.replaceVariables(task, '$(task_name)')
    const filePath = this.getFilePath(task)
    return filePath && filePath.name
  }

  filenameEditable(task) {
    if (!this.config || this.isRemoteMode()) return true
    const filePath = this.getFilePath(task)
    return filePath && filePath.name_editable
  }

  sortFilesByName(prefix: string, file: any) {
    var regexp = new RegExp(`${prefix}(\\d+)`, 'g')
    return path
      .basename(file.originalfilename, path.extname(file.originalfilename))
      .replace(regexp, '')
  }

  sortFilesByVersions(prefix: string, direction: 'asc' | 'desc', file: any) {
    let [, version]: string[] | number[] =
      /(\d+)(\..+)?$/.exec(file.filename) || []
    if (version === undefined) {
      version =
        direction === 'desc' ? Number.MAX_SAFE_INTEGER : Number.MIN_SAFE_INTEGER
    }
    return Number(version)
  }

  getFilename(prefix: string, filename: string) {
    return filename.replace(new RegExp(`(${prefix}\\d+)(.+)$`), '$2')
  }

  getMiradaPath(): string | null {
    const os = OS === 'win' ? 'windows' : 'darwin'
    const miradaPath = this.get(`mirada_path.${os}`, null)
    if (miradaPath && fs.existsSync(miradaPath)) return miradaPath
    const cerebroPath = window.process.env['CEREBRO'] || ''
    if (cerebroPath && fs.existsSync(path.join(cerebroPath, 'mirada.exe')))
      return path.join(cerebroPath, 'mirada.exe')
    if (os === 'windows') {
      if (fs.existsSync(MIRADA_PATH_MAPPING.win32))
        return MIRADA_PATH_MAPPING.win32
      if (fs.existsSync(MIRADA_PATH_MAPPING.win64))
        return MIRADA_PATH_MAPPING.win64
      return null
    }
    if (os === 'darwin' && fs.existsSync(MIRADA_PATH_MAPPING.mac))
      return MIRADA_PATH_MAPPING.mac
    console.warn('Mirada executable not found')
    return null
  }

  hasMirada() {
    const miradaPath = this.getMiradaPath()
    return !!miradaPath
  }

  generateThumbnail(
    filepath: string,
    destination: string,
    removeLista: boolean = true,
  ): Promise<string[]> {
    if (!this.hasMirada()) return Promise.resolve([])
    const miradaPath = this.getMiradaPath()
    console.log('Mirada path:', miradaPath)
    const command = `"${miradaPath}" "${filepath}" --hide --mode thumbstandalone --temp "${destination}"`
    return new Promise((resolve, reject) => {
      try {
        exec(command, (error, stdout, stderr) => {
          try {
            if (stderr) {
              const [, errorMessage = ''] =
                stderr.match(/\.mirada\.ERROR : {(.+)}/) || []
              if (errorMessage) {
                reject(new Error(`Mirada exited with error "${errorMessage}"`))
              }
            }
            const basename = path.basename(filepath)
            const files = fs.readdirSync(destination) || []
            const thumbs = files.filter(
              o => o.indexOf(`${basename}.thumb`) === 0,
            )
            if (removeLista) {
              const listaFiles = files.filter(o => path.extname(o) === '.lista')
              listaFiles.forEach(o => fs.removeSync(path.join(destination, o)))
            }
            resolve(thumbs.map(o => path.join(destination, o)))
          } catch (e) {
            reject(e)
          }
        })
      } catch (e) {
        reject(e)
      }
    })
  }
}

// _.find(
//   projectPaths,
//   o =>
//     (o.project_name == task.project && o.task_activity == task.activity) ||
//     (o.project_name == task.project && o.task_activity == "") ||
//     (o.project_name == "" && o.task_activity == task.activity) ||
//     (o.project_name == "" && o.task_activity == "")
// );
