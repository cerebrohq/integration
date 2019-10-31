import fs from 'fs-extra'
import vm from 'vm'
import _ from 'lodash'
import timers from 'timers'
import Helpers from './helpers'

declare const Babel: any

export default class Processor {
  filename: string = ''
  source: string = ''
  code: string = ''
  sandbox: any = {}
  context!: vm.Context
  method: string = ''

  constructor(filename, method) {
    if (!fs.existsSync(filename)) throw new Error('Processor file not found!')
    this.filename = filename
    this.source = fs.readFileSync(filename).toString()
    this.method = method
    var transformedCode = Babel.transform(this.source, {
      ast: false,
      filename: filename,
      sourceFileName: filename,
      presets: ['es2015', 'es2017'],
    })
    this.code = transformedCode.code

    _.extend(this.sandbox, window, timers, {
      //hostOpenFile: hostOpenFile,
      //hostCreateFile: hostCreateFile,
      app: window.app,
      fs,
      console,
      message: window.app.$Message,
    })
  }

  addContext(key, object, readonly) {
    this.sandbox[key] = readonly ? Helpers.deepFreeze(object) : object
  }
  async run() {
    this.context = vm.createContext(this.sandbox)
    var scriptResult = vm.runInContext(this.code, this.context, {
      filename: this.filename,
      timeout: 15000,
    })
    if (scriptResult.then) {
      return await scriptResult
    } else return scriptResult
  }

  async hasMethod(methodName) {
    await this.run()
    return (
      this.context[methodName] && typeof this.context[methodName] === 'function'
    )
  }

  async runMethod(method, ...args) {
    if (!method && !this.method) {
      throw new Error('Processor method name is null')
    }
    await this.run()
    method = method ? method : this.method
    var funcArgs = args.map(o => _.cloneDeep(o))
    if (this.context[method] && typeof this.context[method] === 'function') {
      var result = this.context[method].apply(global, funcArgs)
      if (result == undefined) return false
      return result
    } else return false
  }
}
