<template>
  <div id="app" style="height: 100%; width: 100%">
    <router-view></router-view>
  </div>
</template>

<script lang="ts">
import { Component, Prop, Vue } from 'vue-property-decorator'
import path from 'path'
import fs from 'fs-extra'
import Helpers from '@/assets/libs/helpers'

@Component
export default class App extends Vue {
  configPath: string = path.join(Helpers.getAppDataFolder(), 'cerebro')
  config: any = null

  created() {
    var self = this
    try {
      this.config = fs.readJsonSync(path.join(this.configPath, '.ula'))
    } catch (e) {
      fs.mkdirpSync(this.configPath)
      this.config = {
        accounts: [],
        autologin: false,
        remember: false,
      }
      this.saveConfig()
    }
  }

  saveConfig() {
    try {
      fs.writeJsonSync(path.join(this.configPath, '.ula'), this.config)
    } catch (e) {
      console.error(e)
    }
  }
}
</script>
