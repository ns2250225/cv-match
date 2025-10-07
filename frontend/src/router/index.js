import { createRouter, createWebHistory } from 'vue-router'
import Jobs from '../views/Jobs.vue'
import Resumes from '../views/Resumes.vue'
import Match from '../views/Match.vue'
import Results from '../views/Results.vue'

const routes = [
  {
    path: '/',
    redirect: '/jobs'
  },
  {
    path: '/jobs',
    name: 'Jobs',
    component: Jobs
  },
  {
    path: '/resumes',
    name: 'Resumes',
    component: Resumes
  },
  {
    path: '/match',
    name: 'Match',
    component: Match
  },
  {
    path: '/results',
    name: 'Results',
    component: Results
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router