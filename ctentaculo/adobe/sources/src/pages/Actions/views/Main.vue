<template>
  <div class="main-form">
    <layout>
      <div class="content">
        <i-button
          :disabled="mainWindowState"
          :loading="mainWindowOpening"
          @click="openTodoList"
          type="primary"
          >Todo list</i-button
        >
        <i-button @click="actionReport" type="primary"
          >Save as version</i-button
        >
        <i-button @click="actionPublish" type="primary">Publish</i-button>
      </div>
      <div class="footer">
        <i-button @click="logout" type="ghost">Logout</i-button>
        <i-button @click="openAbout" type="text" class="text-btn"
          >About</i-button
        >
      </div>
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
import { TMP_DIR } from '@/pages/consts'

declare const DB: CerebroDB

declare global {
  interface Window {
    cep: any
  }
}

@Component
export default class MainView extends Vue {
  @Prop() accountID!: string

  usid: string | null = null
  username: string | null = null
  downloadFolder: string = ''
  mainWindowState: boolean = false
  lastMainWindowState: boolean = false
  mainWindowOpening: boolean = false
  timeoutid: NodeJS.Timeout | null = null
  openPublishModal: boolean = false
  openSaveVersionModal: boolean = false
  openReportModal: boolean = false
  openedFiles: any = new CerebroConfig(
    path.join(Helpers.getAppDataFolder(), 'cerebro', 'taskfile_config.json'),
    {},
  )

  async created() {
    Helpers.addEventListener('updateOpenedFiles', (event: any) => {
      // TODO
    })
    var menu = `
        <Menu>
            <MenuItem Id="change_savepath" Label="Change working directory"/>
        </Menu>
        `
    Helpers.setPanelMenu(menu)
    Helpers.addEventListener(
      'com.adobe.csxs.events.flyoutMenuClicked',
      this.onPanelMenuClicked,
    )
    var account = _.find(this.$parent.config.accounts, ['id', this.accountID])
    account = account ? account : {}

    if (
      (account && !account.savepath) ||
      window.cep.fs.stat(account.savepath).err !== 0
    ) {
      account.savepath = TMP_DIR
      ;(<any>this.$parent).saveConfig()
    }

    this.downloadFolder = account.savepath
    const user = await DB.getUser()
    if (user) {
      this.usid = user.uid
      this.username = `${user.firstname} ${user.lastname}`
      Helpers.setWindowTitle(`Cerebro - ${this.username}`)
    }
    //Helpers.dispatchEvent('closeMainWindow') // REMOVE COMMENTS FOR PROD
    Helpers.addEventListener('onMainWindowOpened', this.onCheckWindowState)
  }

  mounted() {
    Helpers.addEventListener('requestData', this.onRequestData)
    Helpers.addEventListener('mainWindowDBError', this.onDatabaseError)
  }

  beforeDestroy() {
    Helpers.removeEventListener('requestData', this.onRequestData)
    Helpers.removeEventListener('mainWindowDBError', this.onDatabaseError)
  }

  onCheckWindowState() {
    if (this.timeoutid !== null) clearTimeout(this.timeoutid)
    this.mainWindowOpening = false
    this.mainWindowState = true
    this.timeoutid = setTimeout(() => (this.mainWindowState = false), 700)
  }

  onDatabaseError({ data }) {
    const { code: errorCode, message: errorMessage } = data
    console.error(errorMessage)
    this.$router.push({
      name: 'auth',
      params: {
        errorCode,
        errorMessage,
      },
    })
  }

  onRequestData() {
    var data = {
      username: this.username,
      usid: this.usid,
      sid: DB.sid,
      host: DB.host,
      port: DB.port,
      queryId: DB.queryId,
      primaryURL: DB.primaryURL,
      secondaryURL: DB.secondaryURL,
      login: DB.login,
      password: DB.password,
      downloadFolder: this.downloadFolder,
      openPublishModal: this.openPublishModal,
      openSaveVersionModal: this.openSaveVersionModal,
    }
    Helpers.dispatchEvent('responseData', data)
  }

  onPanelMenuClicked({ data }) {
    const { menuId = '' } = data
    switch (menuId) {
      case 'change_savepath':
        this.changeSavePath()
        break
      default:
        console.error(`Unknown panel menu '${menuId}'`)
        break
    }
  }

  async changeSavePath() {
    let result: any = null
    do {
      result = window.cep.fs.showOpenDialog(
        false,
        true,
        'Choose the folder for downloading files',
        '',
      )
    } while (result.err !== 0)
    if (result.data.length !== 0) {
      var account = _.find(this.$parent.config.accounts, ['id', this.accountID])
      account = account ? account : {}
      account.savepath = result.data[0]
      ;(<any>this.$parent).saveConfig()
      this.downloadFolder = account.savepath

      var data = {
        username: this.username,
        usid: this.usid,
        sid: DB.sid,
        host: DB.host,
        port: DB.port,
        queryId: DB.queryId,
        primaryURL: DB.primaryURL,
        secondaryURL: DB.secondaryURL,
        login: DB.login,
        password: DB.password,
        downloadFolder: this.downloadFolder,
        openPublishModal: this.openPublishModal,
        openSaveVersionModal: this.openSaveVersionModal,
      }
      Helpers.dispatchEvent('responseData', data)
    }
  }

  openAbout() {
    this.$router.push({
      name: 'about',
      params: {
        accountID: this.accountID,
      },
    })
  }
  actionReport() {
    if (this.mainWindowState) {
      Helpers.dispatchEvent('openSaveVersionModal')
    } else {
      this.openSaveVersionModal = true
      this.mainWindowOpening = true
      Helpers.openExtension('ctentaculo.main')
    }
  }
  actionPublish() {
    if (this.mainWindowState) {
      Helpers.dispatchEvent('openPublishModal')
    } else {
      this.openPublishModal = true
      this.mainWindowOpening = true
      Helpers.openExtension('ctentaculo.main')
    }
  }

  openChooseFolderDialog() {
    var self = this
    return new Promise(function(resolve) {
      self.$Modal.warning({
        title: 'Warning',
        content: '<p>Please choose the folder for download files!</p>',
        okText: 'OK',
        onOk: function() {
          resolve(true)
        },
      })
    })
  }
  openTodoList() {
    if (this.mainWindowOpening) return
    this.openSaveVersionModal = false
    this.openPublishModal = false
    this.openReportModal = false
    this.mainWindowOpening = true
    Helpers.openExtension('ctentaculo.main')
  }
  logout() {
    this.$router.push({ name: 'auth' })
  }
}
</script>
