<template>
  <div @keyup.enter="login" class="auth-form">
    <layout>
      <i-header :class="{ 'logo-hidden': extendOptions }">
        <i-button
          v-tooltip.auto="{
            content: extendOptions ? 'Back to simple' : 'Advanced',
            delay: 400,
          }"
          @click="toggleExtendOptions"
          type="ghost"
          shape="circle"
          icon="gear-b"
        ></i-button>
        <i-input
          v-show="extendOptions"
          v-tooltip.auto="{ content: 'Enter host', delay: 1000 }"
          :disabled="isConnecting"
          v-model="authFormData.host"
          placeholder="Host"
          style="max-width: 300px"
        ></i-input>
        <i-input
          v-show="extendOptions"
          v-tooltip.auto="{ content: 'Enter port', delay: 1000 }"
          :disabled="isConnecting"
          v-model="authFormData.port"
          placeholder="Port"
          style="max-width: 300px"
        ></i-input>
        <checkbox
          v-show="extendOptions"
          :disabled="isConnecting"
          v-model="$parent.config.autologin"
          >Autologin</checkbox
        >
      </i-header>
      <i-content>
        <auto-complete
          v-tooltip.auto="{ content: 'Enter login', delay: 1000 }"
          @on-select="loginSelect"
          :disabled="isConnecting"
          v-model="authFormData.login"
          :data="logins"
          :filter-method="filterMethod"
          placeholder="Login"
          style="max-width: 300px"
        >
        </auto-complete>
        <i-input
          @paste.capture.native.prevent="disableEvent"
          @copy.capture.native.prevent="disableEvent"
          @cut.capture.native.prevent="disableEvent"
          @drag.capture.native.prevent="disableEvent"
          @drop.capture.native.prevent="disableEvent"
          v-tooltip.auto="{ content: 'Enter password', delay: 1000 }"
          :disabled="isConnecting"
          v-model="authFormData.password"
          :type="showPassword ? 'text' : 'password'"
          autocomplete="off"
          placeholder="Password"
          style="max-width: 300px"
        >
          <i-button
            slot="append"
            :disabled="disableShowPassword"
            @click="showPassword = !showPassword"
            :icon="showPassword ? 'eye-disabled' : 'eye'"
          ></i-button>
        </i-input>
        <checkbox
          :disabled="isConnecting"
          v-model="$parent.config.remember"
          style="margin-bottom: 10px"
          >Remember me</checkbox
        >
        <i-button
          @click="login"
          :loading="isConnecting"
          class="login-btn"
          long
          style="max-width: 300px"
          >Login</i-button
        >
        <i-button
          @click="reportBug"
          type="text"
          class="text-btn"
          long
          style="max-width: 300px"
          >Report a bug</i-button
        >
        <i-button
          @click="newAccount"
          type="text"
          class="text-btn"
          long
          style="max-width: 300px"
          >New account</i-button
        >
      </i-content>
    </layout>
  </div>
</template>

<script lang="ts">
import { Component, Prop, Vue, Watch } from 'vue-property-decorator'
import path from 'path'
import fs from 'fs-extra'
import Helpers from '@/assets/libs/helpers'
import _ from 'lodash'
import { CerebroDB } from '@/assets/libs/cerebro-db'
import { TMP_DIR } from '@/pages/consts'

interface AuthFormData {
  host: string
  port: string
  login: string
  password: string
}

declare module 'vue/types/vue' {
  interface Vue {
    config: any
    $Message: any
    $Modal: any
  }
}

declare const DB: CerebroDB

Component.registerHooks([
  'beforeRouteEnter',
  'beforeRouteLeave',
  'beforeRouteUpdate', // for vue-router 2.2+
])

@Component
export default class AuthView extends Vue {
  @Prop() private errorMessage!: string
  @Prop() private errorCode!: number

  extendOptions: boolean = false
  isConnecting: boolean = false
  showPassword: boolean = false
  disableShowPassword: boolean = false
  authFormData: AuthFormData = {
    host: 'db.cerebrohq.com',
    port: '45432',
    login: '',
    password: '',
  }
  logins: string[] = []

  beforeRouteEnter(to: any, from: any, next: any) {
    next(async (self: AuthView) => {
      Helpers.setWindowTitle('Cerebro - Authorization')
      Helpers.setPanelMenu('')
      if (
        from.path === '/' &&
        self.$parent.config.autologin &&
        self.$parent.config.lastlogin
      ) {
        try {
          var account = _.find(self.$parent.config.accounts, [
            'id',
            self.$parent.config.lastlogin,
          ])
          var address = account.address.split(':')
          DB.init(address[0], address[1])
          self.isConnecting = true
          const data: any = await self.connect(
            account.login,
            Helpers.decodePassword(account.login, account.psw),
          )
          self.isConnecting = false
          if (data.result === false) return
          self.$router.push({
            name: 'main',
            params: {
              accountID: self.$parent.config.lastlogin,
            },
          })
        } catch (error) {
          self.$Message.error(error.message)
        } finally {
          self.isConnecting = false
        }
      }
    })
  }
  created() {
    if (this.errorMessage) {
      if (this.errorCode == 1)
        this.$Message.error({ content: 'Session has expired', duration: 5 })
      else this.$Message.error({ content: this.errorMessage, duration: 5 })
    }
    if (this.$parent.config && this.$parent.config.accounts) {
      this.logins = _.flatMap(this.$parent.config.accounts, function(o) {
        return o.login
      })
    }
  }

  connect(login: string, password: string) {
    return DB.connect(login, password)
  }

  toggleExtendOptions() {
    this.extendOptions = !this.extendOptions
  }

  filterMethod = (value: string, option: string) =>
    option.toUpperCase().indexOf(value.toUpperCase()) !== -1

  loginSelect(login: string) {
    if (!(this.$parent.config && this.$parent.config.accounts)) return
    var account = _.find(this.$parent.config.accounts, ['login', login])
    if (!account) return
    this.authFormData.password = Helpers.decodePassword(
      account.login,
      account.psw,
    )
    var addressInfo = account.address.split(':')
    this.authFormData.host = addressInfo[0]
    this.authFormData.port = addressInfo[1]
    this.showPassword = false
    this.disableShowPassword = true
  }

  reportBug() {
    Helpers.openUrl('https://support.cerebrohq.com/hc/en-us/requests/new')
  }

  newAccount() {
    Helpers.openUrl('https://cerebrohq.com/en/registration/#form_anchor')
  }

  async login() {
    const { login, password, host, port } = this.authFormData
    if (!login || !password) {
      this.$Message.error('Please enter login and password!')
      return
    }
    if (!host || !port) {
      this.$Message.error('Please enter host and port!')
      return
    }
    DB.init(host, +port)
    var self = this
    this.isConnecting = true
    try {
      const sid = await this.connect(login, password)
      if (this.$parent.config.remember) {
        var exist = _.find(this.$parent.config.accounts, ['login', login])
        if (!exist) this.addAccount()
        else this.changeAccount()
      }
      if (this.$parent.config.autologin) {
        let account = _.find(this.$parent.config.accounts, ['login', login])
        if (account) this.$parent.config.lastlogin = account.id
      }
      ;(<any>this.$parent).saveConfig()
      let account = _.find(this.$parent.config.accounts, ['login', login])
      this.$router.push({
        name: 'main',
        params: {
          accountID: account ? account.id : null,
        },
      })
    } catch (error) {
      this.$Message.error(error.message)
    } finally {
      this.isConnecting = false
    }
  }

  addAccount() {
    var exist = _.find(this.$parent.config.accounts, [
      'login',
      this.authFormData.login,
    ])
    if (exist) return
    var newID = Helpers.generateID()
    var login = this.authFormData.login
    var password = this.authFormData.password
    var address = `${this.authFormData.host}:${this.authFormData.port}`
    this.$parent.config.accounts.push({
      id: newID,
      login: login,
      psw: Helpers.encodePassword(login, password),
      address: address,
      savepath: TMP_DIR,
    })
  }
  changeAccount() {
    var account = _.find(this.$parent.config.accounts, [
      'login',
      this.authFormData.login,
    ])
    if (!account) return
    var login = this.authFormData.login
    var password = this.authFormData.password
    var address = `${this.authFormData.host}:${this.authFormData.port}`
    account.login = login
    account.psw = Helpers.encodePassword(login, password)
    account.address = address
  }

  @Watch('$parent.config.autologin')
  onAutologinChange(value: boolean) {
    if (value === true) {
      this.$parent.config.remember = true
    }
  }

  @Watch('$parent.config.remember')
  onRemeberChange(value: boolean) {
    if (value === false) {
      this.$parent.config.autologin = false
    }
  }

  @Watch('authFormData.password')
  onPasswordChange(value: string) {
    if (value == '') this.disableShowPassword = false
  }
}
</script>
