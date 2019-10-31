<template>
  <div class="about-form">
    <layout>
      <i-header></i-header>
      <i-content style="text-align: center">
        Plugin version: {{ pluginVersion }}
        <br />
        Host ID: {{ hostId }}
        <br />
        Host version: {{ hostVersion }}
        <br />
        Operation System: {{ OSInfo }}
        <br />
      </i-content>
      <i-footer>
        <i-button
          @click="actionReportBug"
          type="text"
          class="text-btn"
          long
          style="max-width: 300px"
          >Report a bug</i-button
        >
        <i-button
          @click="actionBack"
          type="primary"
          class="login-btn"
          long
          style="max-width: 300px"
          >Back</i-button
        >
      </i-footer>
    </layout>
  </div>
</template>

<script lang="ts">
import { Component, Prop, Vue, Watch } from 'vue-property-decorator'
import path from 'path'
import fs from 'fs-extra'
import Helpers from '@/assets/libs/helpers'
import CerebroConfig from '@/assets/libs/cerebro-config'
import _ from 'lodash'
import { CerebroDB } from '@/assets/libs/cerebro-db'
import { parseString as xmlParse } from 'xml2js'

declare const DB: CerebroDB

@Component
export default class MainView extends Vue {
  @Prop() accountID!: string

  pluginVersion: string = ''
  hostId: string = ''
  hostVersion: string = ''
  OSInfo: string = ''

  created() {
    var xmlPath = path.join(
      Helpers.getExtensionFolder(),
      'CSXS',
      'manifest.xml',
    )
    try {
      var xml = fs.readFileSync(xmlPath)
      var self = this
      xmlParse(xml, function(error, result) {
        if (error) return
        self.pluginVersion = result.ExtensionManifest.$.ExtensionBundleVersion
      })
    } catch (e) {
      /*TODO*/
    }
    var hostEnv = Helpers.getHostEnvironment()
    this.hostId = hostEnv.appId
    this.hostVersion = hostEnv.appVersion
    this.OSInfo = Helpers.getOS()
  }
  actionReportBug() {
    var version =
      'Plugin: ' +
      this.pluginVersion +
      '; Host: ' +
      this.hostId +
      ' ' +
      this.hostVersion
    Helpers.openUrl(
      'https://support.cerebrohq.com/hc/en-us/requests/new?product=cerebro' +
        '&version=' +
        version +
        '&subject=Problem with Adobe Tentaculo',
    )
  }
  actionBack() {
    this.$router.push({
      name: 'main',
      params: {
        accountID: this.accountID,
      },
    })
  }
}
</script>
