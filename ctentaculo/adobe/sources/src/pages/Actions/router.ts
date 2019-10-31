import Vue from 'vue'
import Router from 'vue-router'
import Auth from './views/Auth.vue'

Vue.use(Router)

export default new Router({
  routes: [
    { name: 'auth', path: '/', component: Auth, props: true },
    {
      name: 'main',
      path: '/main',
      component: () =>
        import(/* webpackChunkName: "main" */ './views/Main.vue'),
      props: true,
    },
    {
      name: 'about',
      path: '/about',
      component: () =>
        import(/* webpackChunkName: "about" */ './views/About.vue'),
      props: true,
    },
  ],
})
