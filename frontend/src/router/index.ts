import { createRouter, createWebHistory } from 'vue-router'
import HomeView from '../views/HomeView.vue'
import InterviewView from '../views/InterviewView.vue'
import HistoryView from '../views/HistoryView.vue'
import AuthView from '../views/AuthView.vue'
import MockInterviewView from '../views/MockInterviewView.vue'
import FavoritesView from '../views/FavoritesView.vue'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', name: 'home', component: HomeView },
    { path: '/interview', name: 'interview', component: InterviewView },
    { path: '/mock-interview', name: 'mock-interview', component: MockInterviewView },
    { path: '/history', name: 'history', component: HistoryView },
    { path: '/favorites', name: 'favorites', component: FavoritesView },
    { path: '/auth', name: 'auth', component: AuthView }
  ]
})

export default router
