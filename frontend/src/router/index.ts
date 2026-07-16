import { createRouter, createWebHashHistory } from 'vue-router'
import Layout from '@/views/Layout/index.vue'

const router = createRouter({
  history: createWebHashHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      component: Layout,
      redirect: '/chat',
      children: [
        {
          path: 'chat',
          name: 'Chat',
          component: () => import('@/views/Chat/index.vue'),
          meta: { title: '对话' },
        },
        {
          path: 'models',
          name: 'Models',
          component: () => import('@/views/Models/index.vue'),
          meta: { title: '模型' },
        },
        {
          path: 'rag',
          name: 'Rag',
          component: () => import('@/views/Rag/index.vue'),
          meta: { title: '知识库' },
        },
        {
          path: 'agent',
          name: 'Agent',
          component: () => import('@/views/Agent/index.vue'),
          meta: { title: '智能体' },
        },
        {
          path: 'mcp',
          name: 'Mcp',
          component: () => import('@/views/Mcp/index.vue'),
          meta: { title: 'MCP' },
        },
      ],
    },
  ],
})

export default router
