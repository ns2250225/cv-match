import axios from 'axios'

// 创建axios实例
const api = axios.create({
  baseURL: '/api',
  timeout: 120000 // 增加到120秒，适应DeepSeek API的响应时间
})

// 请求拦截器
api.interceptors.request.use(
  (config) => {
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// 响应拦截器
api.interceptors.response.use(
  (response) => {
    return response
  },
  (error) => {
    console.error('API请求错误:', error)
    return Promise.reject(error)
  }
)

// API方法
export default {
  // 岗位相关API
  getJobs() {
    return api.get('/jobs')
  },
  
  createJob(data) {
    return api.post('/jobs', data)
  },
  
  deleteJob(id) {
    return api.delete(`/jobs/${id}`)
  },
  
  // 简历相关API
  getResumes() {
    return api.get('/resumes')
  },
  
  uploadResume(formData) {
    return api.post('/resumes', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })
  },
  
  deleteResume(id) {
    return api.delete(`/resumes/${id}`)
  },
  
  // 匹配相关API
  matchResume(data) {
    return api.post('/match', data)
  },
  
  batchMatchResumes(data) {
    return api.post('/batch-match', data)
  },
  
  getMatchProgress(taskId) {
    return api.get(`/match-progress/${taskId}`)
  },
  
  getMatchResults() {
    return api.get('/match-results')
  },
  
  deleteMatchResult(id) {
    return api.delete(`/match-results/${id}`)
  },
  
  clearAllMatchResults() {
    return api.delete('/match-results')
  }
}