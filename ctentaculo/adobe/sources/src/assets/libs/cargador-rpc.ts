import _ from 'lodash'
import xmlrpc from 'xmlrpc'
import fs from 'fs-extra'
import path from 'path'
import Helpers from './helpers'

var statusTable = []
var refreshTableTimer = null
var lastTime = -1

function getDownlaodStatus(hash) {
  return new Promise(function(resolve, reject) {
    return getStatus(hash).then(function(status) {
      setTimeout(function() {
        if (!status) return reject(Error('Status not found'))
        if (+status == 0x7fffffff || +status == 90 || +status == 70)
          return resolve(+status)
        if (+status == 80) return resolve(+status)
        return reject(Error('Downloading'))
      }, 1000)
    })
  })
}

function connectToRPC(host) {
  return new Promise(function(resolve, reject) {
    if (!host.local) return resolve({ status: 'error' })
    CargadorAPI.clientRPC = xmlrpc.createClient({
      host: host.host,
      port: host.port,
    })
    CargadorAPI.clientRPC.methodCall('statusInfo', [], function(error, _) {
      if (error) {
        resolve({ status: 'error' })
        return
      }
      CargadorAPI.rpcConnected = true
      resolve({ status: 'error' })
    })
  })
}

function getStatusTable() {
  return new Promise(function(resolve, reject) {
    var now = Date.now()
    if (now - lastTime > 5000) {
      lastTime = now
      CargadorAPI.request('statusTables', [1 | 2 | 4 | 8 | 0x10, 0])
        .then(function(data: any) {
          statusTable = data
          return resolve(data)
        })
        .catch(function(error) {
          return reject(Error(error))
        })
    } else if (statusTable.length == 0) {
      var int = setInterval(function() {
        if (statusTable.length != 0) {
          clearInterval(int)
          return resolve(statusTable)
        }
      }, 500)
    } else {
      return resolve(statusTable)
    }
  })
}

function getStatus(hash) {
  return getStatusTable().then(function(data: any) {
    var item = _.find(data, ['hash', hash])
    if (item) return item.status
    else return null
  })
}

function getImportOptions(filename: string) {
  return {
    method: 'PUT',
    body: fs.readFileSync(filename),
    headers: {
      'User-Agent': 'Adobe Cerebro uploader',
      'Content-Type': 'application/octet-stream',
      'Content-Length': String(fs.statSync(filename).size),
    },
  }
}

export default class CargadorAPI {
  static siteList: any[] = []
  static _siteList: string = ''
  static clientRPC: any
  static rpcConnected: boolean = false

  static async connect(hosts) {
    CargadorAPI.siteList = hosts
    CargadorAPI._siteList = CargadorAPI.siteList
      .map(o => `${o.host}:${o.nativeport}?${o.name}`)
      .join(';')
    let result: any
    for (const host of hosts) {
      result = await connectToRPC(host)
      if (result.status === 'ok') {
        break
      }
    }
    return result
  }

  static request(method, args) {
    return new Promise(function(resolve, reject) {
      if (!CargadorAPI.clientRPC || !CargadorAPI.rpcConnected)
        return reject(Error('Not connect'))
      CargadorAPI.clientRPC.methodCall(method, args, function(error, value) {
        if (error) return reject(Error(error))
        if (!value) {
          return resolve([])
        }
        if (value.length == 1) {
          return resolve([])
        }
        var props = value.shift()
        var values: any[] = []
        for (var i = 0; i < value.length; i++) {
          values.push(_.zipObject(props, value[i]))
        }
        return resolve(values)
      })
    })
  }

  static async fileInfo(hash) {
    if (!hash) return null
    return CargadorAPI.request('catalogResolve', [hash])
  }
  // download file
  static async fileDownload(hash, url) {
    if (!hash) throw Error('Hash empty')
    const fileInfo: any = await CargadorAPI.fileInfo(hash)
    if (fileInfo.length == 0) {
      await CargadorAPI.request('catalogDownload', [
        hash,
        CargadorAPI._siteList,
        0,
        'ctentaculo',
        url,
        1,
      ])
      const downloaded = await CargadorAPI.checkDownloadStatus(hash)
      if (downloaded) {
        return await CargadorAPI.fileInfo(hash)
      } else throw Error('File not found')
    } else return fileInfo
  }

  static async checkDownloadStatus(hash) {
    try {
      const status: any = await getDownlaodStatus(hash)
      if (+status == 80) return true
      return false
    } catch (error) {
      return await CargadorAPI.checkDownloadStatus(hash)
    }
  }

  static async catalogDownload(hash, url) {
    try {
      return await CargadorAPI.fileInfo(hash)
    } catch (error) {
      if (
        error.message == 'RPC not connect' ||
        error.message == 'Hash is empty'
      ) {
        throw error
      } else {
        const error = await CargadorAPI.request('catalogDownload', [
          hash,
          CargadorAPI._siteList,
          0,
          'ctentaculo',
          url,
          1,
        ])
        if (error) {
          throw error
        } else {
          await CargadorAPI.checkDownloadStatus(hash)
          return await CargadorAPI.fileInfo(hash)
        }
      }
    }
  }

  static async getImportHash(filename, url, address): Promise<string> {
    const endUrl = Helpers.toCorrectPath(
      encodeURIComponent(`${url.trim()}/${path.basename(filename)}`),
    )
    const importUrl = `http://${address.host}:${address.port}/${endUrl}`
    const hash = await (await fetch(
      importUrl,
      getImportOptions(filename),
    )).text()
    return hash
  }

  static async importFile(addresses, filename, url): Promise<string> {
    let hash = ''
    let lastError = null
    for (const address of addresses) {
      try {
        hash = await CargadorAPI.getImportHash(filename, url, address)
        break
      } catch (e) {
        lastError = e
      }
    }
    if (hash != '') return Helpers.hash64to16(hash)
    else throw lastError
  }
}
