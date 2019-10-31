import { CSInterface, SystemPath, CSEvent } from 'csinterface-ts'
import shortUuid from 'short-uuid'
import path from 'path'
import xmlParser from 'xml2js'
import _ from 'lodash'
import moment from 'moment'
import { exec } from 'child_process'
import fs from 'fs-extra'
import CargadorRPC from './cargador-rpc'
import copyClipboard from 'copy-text-to-clipboard'
import os from 'os'
import { Vue } from 'vue-property-decorator'
import b64 from 'bitwise64'

const decimalTranslator = shortUuid('0123456789')
var csInterface: CSInterface
const EvalScript_ErrMessage = 'EvalScript error.'
const debug = process.env.NODE_ENV !== 'production' && !window.cep

declare module 'os' {
  function tmpDir(): string
}

if (!debug) {
  csInterface = new CSInterface()
}

interface ReadFileOptions {
  encoding: string
  flag?: string
}

export default class Helpers {
  static alert(message: string): void {
    Vue.prototype.$Modal.error({
      title: 'Cerebro Tentaculo',
      content: message,
    })
  }
  static getTaskInfo(task: any, usid: any, username: any): any {
    return {
      id: task.uid,
      name: task.name,
      parentId: task.parent_uid,
      parentPath: task.parent,
      statusId: task.status.uid,
      statusName: task.status.name,
      activityId: task.acivityid,
      activityName: task.activity,
      currentUserId: usid,
      currentUserName: username,
    }
  }
  /**
   * Encode the password by login, used Base64.
   *
   * @param login User login
   * @param password User decoded password
   * @return Encoded password
   *
   */
  static encodePassword(login: string, password: string) {
    return new Buffer(password + login).toString('base64')
  }

  /**
   * Decode the password by login, used Base64.
   *
   * @param login User login
   * @param password User encoded password
   * @return Decoded password
   *
   */
  static decodePassword(login: string, password: string) {
    return new Buffer(password, 'base64').toString().replace(login, '')
  }

  /**
   * Generate random ID, 10 digits.
   *
   * @return Random ID
   *
   */
  static generateID(): number {
    return Number(decimalTranslator.generate().slice(0, 10))
  }

  /**
   * Open URL in browser.
   *
   * @param url Opening URL
   *
   */
  static openUrl(url: string): void {
    if (debug) {
      window.open(url, '_blank')
    } else {
      csInterface.openURLInDefaultBrowser(url)
    }
  }

  static readFile(path: string, options?: ReadFileOptions): Promise<string> {
    return new Promise((resolve, reject) => {
      fs.readFile(
        path,
        options || {},
        (
          error: any,
          data: {
            toString: () => string | PromiseLike<string> | undefined
          },
        ) => {
          if (!error) {
            return resolve(data.toString())
          } else {
            return reject(error)
          }
        },
      )
    })
  }

  static saveFile(path: string, data: any): Promise<void> {
    return new Promise((resolve, reject) => {
      fs.writeFile(path, data, (error: any) => {
        if (!error) {
          return resolve()
        } else {
          return reject(error)
        }
      })
    })
  }

  static getAppDataFolder(): string {
    if (debug) {
      return process.env.APPDATA || ''
    } else {
      return csInterface.getSystemPath(SystemPath.USER_DATA)
    }
  }

  static getAppFolder(): string {
    if (debug) {
      return ''
    } else {
      return csInterface.getSystemPath(SystemPath.HOST_APPLICATION)
    }
  }

  static getExtensionFolder(): string {
    if (debug) {
      return ''
    } else {
      return csInterface.getSystemPath(SystemPath.EXTENSION)
    }
  }

  static getTMPFolder(): string {
    return (os.tmpdir && os.tmpdir()) || os.tmpDir()
  }

  static parseXml(data: string): Promise<any> {
    return new Promise((resolve, reject) => {
      xmlParser.parseString(data, (error, result) => {
        if (!error) {
          return resolve(result)
        } else {
          return reject(error)
        }
      })
    })
  }

  static evalHostScript(script: string) {
    return new Promise(resolve => {
      csInterface.evalScript(script, resolve)
    })
  }

  static async getExtensionVersion(): Promise<string> {
    if (debug) {
      return 'DEBUG'
    } else {
      let manifestPath = path.join(
        Helpers.getExtensionFolder(),
        'CSXS',
        'manifest.xml',
      )
      let xml = await Helpers.readFile(manifestPath)
      try {
        let xmlObject = await Helpers.parseXml(xml)
        return _.get(
          xmlObject,
          'ExtensionManifest.$.ExtensionBundleVersion',
          'Unknown',
        )
      } catch (error) {
        console.error(error)
        return 'Unknown'
      }
    }
  }

  static getHostEnvironment(): any {
    return csInterface.getHostEnvironment()
  }

  static getHostID(): string {
    if (debug) {
      return navigator.appName
    } else {
      let hostEnvironment = Helpers.getHostEnvironment()
      return hostEnvironment.appId
    }
  }

  static getHostVersion(): string {
    if (debug) {
      return navigator.appVersion
    } else {
      let hostEnvironment = Helpers.getHostEnvironment()
      return hostEnvironment.appVersion
    }
  }

  static getOS(): string {
    if (debug) {
      return navigator.platform
    } else {
      return csInterface.getOSInformation().startsWith('Windows')
        ? 'win'
        : 'mac'
    }
  }

  static getOSBits(): number {
    const os = Helpers.getOS()
    if (os === 'win') {
      return csInterface.getOSInformation().match(/64-bit/g) ? 64 : 32
    } else return -1
  }

  static openExtension(name: string) {
    if (debug) {
      console.error('openExtension: App current in DEBUG mode')
    } else {
      csInterface.requestOpenExtension(name, '')
    }
  }

  static setPanelMenu(menu: string) {
    if (debug) {
      console.error('setPanelMenu: App current in DEBUG mode')
    } else {
      csInterface.setPanelFlyoutMenu(menu)
    }
  }

  static setWindowTitle(title: string) {
    if (debug) {
      document.title = title
    } else {
      csInterface.setWindowTitle(title)
    }
  }

  static addEventListener(eventName: string, callback: Function) {
    if (debug) {
      console.error('addEventListener: App current in DEBUG mode')
    } else {
      csInterface.addEventListener(eventName, callback)
    }
  }

  static removeEventListener(eventName: string, func: Function) {
    if (debug) {
      console.error('removeEventListener: App current in DEBUG mode')
    } else {
      csInterface.removeEventListener(eventName, func)
    }
  }

  static dispatchEvent(eventName: string, payload?: any) {
    if (debug) {
      console.error('dispatchEvent: App current in DEBUG mode')
    } else {
      let event = new CSEvent(eventName, 'APPLICATION')
      event.data = payload
      csInterface.dispatchEvent(event)
    }
  }

  static decimalToHours(hours: number) {
    function getDecimal(num: number) {
      var str = '' + num
      var zeroPos = str.indexOf('.')
      if (zeroPos == -1) return 0
      str = str.slice(zeroPos)
      return +str
    }
    var result = {
      hours: 0,
      minutes: 0,
      seconds: 0,
    }
    result.hours = Math.trunc(hours)
    var minutes = getDecimal(hours) * 60
    result.minutes = Math.trunc(minutes)
    var seconds = getDecimal(minutes) * 60
    result.seconds = Math.round(seconds)
    return result
  }

  static decimalToDays(hours: number) {
    return Helpers.decimalToHours(hours * 24)
  }

  static getTaskDeadline(task: any) {
    if (task.tg_cc_stop_at_js) return moment(task.tg_cc_stop_at_js)
    const startOffset = task.human_start ? task.human_start : task.offset
    let stopOffset = task.human_stop
      ? task.human_stop
      : startOffset + task.duration
    stopOffset = Helpers.decimalToDays(stopOffset)
    return moment('2000-01-01')
      .add(moment().utcOffset(), 'minutes')
      .add(stopOffset)
  }

  static stripTags(html: string) {
    var tmp = document.createElement('div')
    tmp.innerHTML = html.replace(/<br\/?>/gm, '\n').replace(/<br \/?>/gm, '\n')
    var style = tmp.querySelector('style')
    if (style) style.remove()
    var res = tmp.textContent || tmp.innerText
    tmp.remove()
    return res ? res.trim().replace(/\n/g, '<br />') : ''
  }

  static getBitValue(bit) {
    let result = 1
    for (let i = 1; i <= bit; i++) {
      result *= 2
    }
    return result
  }

  static bitTest(mask, bit) {
    return b64.and(mask, Helpers.getBitValue(bit)) // (mask & (1 << bit)) != 0
  }

  static bitSet(num, bit) {
    return num | (1 << bit)
  }

  static bitClear(num, bit) {
    return num & ~(1 << bit)
  }

  static bitToggle(num, bit) {
    return Helpers.bitTest(num, bit)
      ? Helpers.bitClear(num, bit)
      : Helpers.bitSet(num, bit)
  }

  static toCorrectPath(p: string) {
    return p.replace(/\\/g, '/')
  }
  static pathJoin(...args) {
    return path.join(...args).replace(/\\/g, '/')
  }
  static pathNormalize(p) {
    return path.normalize(p).replace(/\\/g, '/')
  }
  static makePath(p: string) {
    if (!fs.existsSync(p)) fs.mkdirpSync(p)
  }
  static hash16to64(hash16) {
    if (!hash16) return ''
    var hash64 = new Buffer(hash16, 'hex').toString('base64')
    hash64 = hash64
      .replace(/\+/g, '-')
      .replace(/\//g, '_')
      .replace(/=/g, '~')
    return hash64
  }
  static hash64to16(hash64) {
    if (!hash64) return ''
    var hash16 = hash64
      .replace(/-/g, '+')
      .replace(/_/g, '/')
      .replace(/~/g, '=')
    hash16 = new Buffer(hash16, 'base64').toString('hex')
    return hash16.toUpperCase()
  }
  static closeExtension() {
    csInterface.closeExtension()
  }
  static openFS(filePath, select?: boolean) {
    const OS =
      csInterface.getOSInformation().indexOf('Windows') !== -1 ? 'Win' : 'Mac'
    if (OS == 'Win') {
      filePath = filePath.replace(/\//g, '\\')
      exec(`start explorer ${select ? '/select,' : ''} "${filePath}"`)
    } else {
      filePath = Helpers.toCorrectPath(filePath)
      exec(`open -R "${filePath}"`)
    }
  }

  static resetTaskData(task) {
    task.attachments = null
    task.filePath = null
    task.projectPath = null
    task.inWork = false
    task.definitionMsg = null
    task.messages = null
    task.statuses = null
  }

  static getTaskThumbPath(task, thumbsPath) {
    if (task.thumbHash) {
      const thumbPath = Helpers.pathJoin(thumbsPath, task.thumbHash + '.png')
      return thumbPath
    } else {
      return ''
    }
  }

  static deepFreeze(obj) {
    if (_.isObject(obj) || _.isArray(obj) || _.isFunction(obj)) {
      Object.freeze(obj)
      _.forOwn(obj, Helpers.deepFreeze)
    }
    return obj
  }

  static arrayBufferToBase64(buffer) {
    var binary = ''
    var bytes = [].slice.call(new Uint8Array(buffer))

    bytes.forEach(function(b) {
      binary += String.fromCharCode(b)
    })
    return binary
  }

  static download(hash, address) {
    return new Promise(function(resolve, reject) {
      if (!hash) return reject(Error('Hash is empty'))
      return fetch(`http://${address.host}:${address.port}/?hash=${hash}`)
        .then(function(response) {
          if (!response.ok) {
            return reject(Error('File not found'))
          }
          return (response.arrayBuffer
            ? response.arrayBuffer()
            : (<any>response).buffer()
          ).then(function(buffer) {
            return resolve(buffer)
          })
        })
        .catch(function(error) {
          return reject(Error(error))
        })
    })
  }

  static async downloadFile(hash, downloadDir, url, addresses, index?) {
    if (index == null || index == undefined) index = 0
    if (!hash) throw new Error('Hash is empty')
    if (fs.existsSync(downloadDir)) return true
    if (CargadorRPC.rpcConnected) {
      var hash64 = Helpers.hash16to64(hash)
      const fileInfo = await CargadorRPC.fileDownload(hash64, url)
      if (fileInfo.length == 0) throw Error('File not found')
      Helpers.makePath(path.dirname(downloadDir))
      fs.copySync(fileInfo[0].path, downloadDir)
      return true
    } else {
      try {
        const buffer = await Helpers.download(hash, addresses[index])
        var data = Helpers.arrayBufferToBase64(buffer)
        Helpers.makePath(path.dirname(downloadDir))
        fs.writeFileSync(downloadDir, data, 'ascii')
        return true
      } catch (error) {
        if (++index >= addresses.length) throw Error(error)
        return Helpers.downloadFile(hash, downloadDir, url, addresses, index)
      }
    }
  }

  static findFile(db, conditions): Promise<any> {
    return new Promise(function(resolve, reject) {
      db.findOne(conditions, function(error, file) {
        if (error) return reject(Error(error))
        return resolve(file)
      })
    })
  }

  static countFile(db, conditions): Promise<number> {
    return new Promise(function(resolve, reject) {
      db.count(conditions, function(error, count) {
        if (error) return reject(Error(error))
        return resolve(count)
      })
    })
  }

  static copyText(text) {
    const OS =
      csInterface.getOSInformation().indexOf('Windows') !== -1 ? 'Win' : 'Mac'
    if (OS == 'Win') {
      text = text.replace(/\//g, '\\')
    } else {
      text = Helpers.toCorrectPath(text)
    }
    copyClipboard(text)
  }

  static copyFileSync(oldPath, newPath) {
    if (!fs.existsSync(oldPath)) throw Error('Source file not found')
    Helpers.makePath(path.dirname(newPath))
    fs.copySync(oldPath, newPath)
  }

  static loadJSX(hostID) {
    const extensionRoot =
      csInterface.getSystemPath(SystemPath.EXTENSION) + '/jsx/'
    csInterface.evalScript(
      `$._ext.evalFile("${extensionRoot + hostID}.jsx")`,
      result => {
        if (result === EvalScript_ErrMessage)
          console.error(
            `Failed load JSX script. Path: ${extensionRoot + hostID}.jsx`,
          )
        else console.log('Success load JSX script')
      },
    )
  }

  static msgTagToStr(tag: number): string {
    let type = ''
    switch (tag) {
      case 0:
        type = 'Definition'
        break
      case 1:
        type = 'Review'
        break
      case 2:
        type = 'Report'
        break
      case 3:
        type = 'Note'
        break
      case 4:
        type = 'Client review'
        break
      case 5:
        type = 'Resource report'
        break
      default:
        break
    }
    return type
  }

  static sleep(mlsecs = 1000) {
    return new Promise(resolve => {
      setTimeout(resolve, mlsecs)
    })
  }
}
