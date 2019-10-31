import { CSInterface, SystemPath, CSEvent } from 'csinterface-ts'

const EvalScript_ErrMessage = 'EvalScript error.'

function callFunc(func, ...params): any {
  if (!Array.isArray(params)) params = []
  var paramsStr = params
    .map(p => {
      if (p === null) return p
      switch (typeof p) {
        case 'number':
        case 'boolean':
        case 'undefined':
          return p
        default:
        case 'string':
          /*eslint-disable */
          return "'" + p.replace(/\\/g, '\\\\') + "'"
      }
    })
    .join(',')
  var script = func + '(' + paramsStr + ')'
  return new Promise((resolve, reject) => {
    new CSInterface().evalScript(script, result => {
      if (result === EvalScript_ErrMessage) {
        throw Error('Unhandled HOST error')
      } else {
        try {
          result = JSON.parse(result)
          if (result.error) {
            reject(result.error)
          } else {
            resolve(result.data)
          }
        } catch (e) {
          resolve(result)
        }
      }
    })
  })
}

export default abstract class HostApp {
  static pdfFile(fileName: any): any {
    throw new Error('Method not implemented.')
  }
  static jpegFile(fileName: any): any {
    throw new Error('Method not implemented.')
  }
  static async getFilename(): Promise<string> {
    return callFunc('getDocumentFilename')
  }

  static async createFile(location) {
    return callFunc('newDocument', location)
  }

  static async openFile(location) {
    return callFunc('openDocument', location)
  }

  static async snapshot(location, size) {
    return callFunc('takeSnapshot', location, size)
  }
}
