import fs from 'fs-extra'
import { NETWORK_CONFIG_PATH, LOCAL_CONFIG_PATH } from '@/pages/consts'
import PathConfig from './path-config'

export default class ConfigPool {
  universes: any
  configs: Record<string, PathConfig>

  constructor() {
    this.universes = {}
    this.configs = {}
  }

  async add(projectID, downloadFolder) {
    let universeID = this.universes[projectID]
    if (!universeID) {
      universeID = await window.DB.getUniverseIDByProjectID(projectID)
      if (universeID) this.universes[projectID] = universeID
      //console.info('Get universe from project -', universeID, projectID)
    }
    if (universeID) {
      if (!this.configs[universeID]) {
        const config = await window.DB.getUniverseAttribute(universeID, 120)
        if (config) {
          this.configs[universeID] = new PathConfig(
            config,
            'db',
            downloadFolder,
          )
          //console.info('For universe use db config', universeID)
        } else {
          if (fs.existsSync(NETWORK_CONFIG_PATH)) {
            this.configs[universeID] = new PathConfig(
              NETWORK_CONFIG_PATH,
              'network',
              downloadFolder,
            )
            //console.info('For universe use network config', universeID)
          } else {
            this.configs[universeID] = new PathConfig(
              LOCAL_CONFIG_PATH,
              'local',
              downloadFolder,
            )
            //console.info('For universe use local config', universeID)
          }
        }
      }
    }
  }

  config(projectID) {
    const universeID = this.universes[projectID]
    if (!universeID) return null
    return this.configs[universeID]
  }

  all() {
    return this.configs
  }

  count() {
    return Object.keys(this.configs).length
  }
}
