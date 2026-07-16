import { createApp } from 'vue'
import { createPinia } from 'pinia'
import Vue3Toasity from 'vue3-toastify'
import App from './App.vue'
import router from './router'
import './assets/styles/index.scss'
import 'vue3-toastify/dist/index.css'

const app = createApp(App)
app.use(createPinia())
app.use(router)
app.use(Vue3Toasity, {
  autoClose: 3000,
  position: 'top-center',
  theme: 'auto',
  toastClassName: 'app-toast',
})
app.mount('#app')
