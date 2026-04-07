import { defineStore } from 'pinia'
import { ref } from 'vue'
import axios from 'axios'

const api = axios.create({
  baseURL: '/api'
})

// 从 LocalStorage 读取 Token
const token = localStorage.getItem('access_token')
if (token) {
  api.defaults.headers.common['Authorization'] = `Bearer ${token}`
}

export const useInterviewStore = defineStore('interview', () => {
  const currentQuestion = ref<any>(null)
  const userId = ref(localStorage.getItem('user_id') || '')
  const username = ref(localStorage.getItem('username') || '')
  const history = ref<any[]>([])
  const loading = ref(false)

  async function generateQuestion(config: any) {
    loading.value = true
    try {
      const response = await api.post('/generate-question', {
        ...config,
        user_id: userId.value
      })
      currentQuestion.value = response.data
      return response.data
    } catch (error) {
      console.error('生成题目失败:', error)
      throw error
    } finally {
      loading.value = false
    }
  }

  async function submitAnswer(answerData: any) {
    loading.value = true
    try {
      const response = await api.post('/submit-answer', {
        ...answerData,
        user_id: userId.value
      })
      return response.data
    } catch (error) {
      console.error('提交答案失败:', error)
      throw error
    } finally {
      loading.value = false
    }
  }

  async function getUserHistory() {
    if (!userId.value) return null
    try {
      const response = await api.get(`/user-history/${userId.value}`)
      history.value = response.data.recent_answers
      return response.data
    } catch (error) {
      console.error('获取历史失败:', error)
      throw error
    }
  }

  function setUserInfo(id: string, name: string) {
    userId.value = id
    username.value = name
    localStorage.setItem('user_id', id)
    localStorage.setItem('username', name)
  }

  function logout() {
    userId.value = ''
    username.value = ''
    localStorage.removeItem('access_token')
    localStorage.removeItem('user_id')
    localStorage.removeItem('username')
    delete api.defaults.headers.common['Authorization']
  }

  function login(tokenValue: string) {
    localStorage.setItem('access_token', tokenValue)
    api.defaults.headers.common['Authorization'] = `Bearer ${tokenValue}`
  }

  return {
    currentQuestion,
    userId,
    username,
    history,
    loading,
    generateQuestion,
    submitAnswer,
    getUserHistory,
    setUserInfo,
    logout,
    login
  }
})
