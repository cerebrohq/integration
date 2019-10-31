import '@babel/polyfill'
import Vue from 'vue'
import App from './App.vue'
import router from './router'
import store from '@/store'
import { CerebroDB } from '@/assets/libs/cerebro-db'
import iView from 'iview'
import '@/assets/iview-styles/index.less'
import locale from 'iview/dist/locale/en-US'
import VTooltip from 'v-tooltip'
import './styles.scss'
import fetch from 'isomorphic-fetch'
window.fetch = fetch

declare global {
  interface Window {
    DB: CerebroDB
  }
}

window.DB = new CerebroDB()

Vue.config.productionTip = false
Vue.use(iView, { locale })
Vue.use(VTooltip)
new Vue({
  router,
  store,
  render: h => h(App),
}).$mount('#app')
