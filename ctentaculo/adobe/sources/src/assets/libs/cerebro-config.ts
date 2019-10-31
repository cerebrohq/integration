import fs from 'fs-extra'
import path from 'path'
import _ from 'lodash'

export default class CerebroConfig {
  protected configPath!: string
  protected config: any
  constructor(configPath?: string, defaultValue?: any) {
    if (!configPath) return
    this.configPath = configPath
    try {
      this.config = JSON.parse(fs.readFileSync(this.configPath, 'utf8'))
    } catch (error) {
      if (typeof defaultValue !== 'object') throw error
      else {
        this.config = defaultValue
        if (!fs.existsSync(path.dirname(this.configPath)))
          fs.mkdirSync(path.dirname(this.configPath))
        fs.writeFileSync(
          this.configPath,
          JSON.stringify(this.config, null, 4),
          'utf8',
        )
      }
    }
  }

  get(key: string, defaultValue: any) {
    return _.get(this.config, key, defaultValue)
  }

  set(key: string, value: any) {
    return _.set(this.config, key, value)
  }

  save() {
    fs.writeFileSync(
      this.configPath,
      JSON.stringify(this.config, null, 4),
      'utf8',
    )
  }
}
