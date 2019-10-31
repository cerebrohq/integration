import '@babel/polyfill'
import Vue from 'vue'
import App from './App.vue'
import router from './router'
import store from '@/store'
import iView from 'iview'
import locale from 'iview/dist/locale/en-US'
import '@/assets/iview-styles/index.less'
import VTooltip from 'v-tooltip'
import './styles.scss'
import { CerebroDB } from '@/assets/libs/cerebro-db'
import fetch from 'isomorphic-fetch'

if (typeof window.fetch === 'undefined') window.fetch = fetch

declare global {
  interface Window {
    APP_ROOT: string
    DB: CerebroDB
    app: any
  }
}

window.DB = new CerebroDB()

Vue.config.productionTip = false
Vue.use(iView, { locale })
Vue.use(VTooltip)
window.app = new Vue({
  router,
  store,
  render: h => h(App),
}).$mount('#app')
