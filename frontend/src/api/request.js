import axios from 'axios'
import { ElMessage } from 'element-plus'
import { useAuthStore } from '@/store/auth'

const request = axios.create({
  baseURL: 'http://127.0.0.1:8000',
  timeout: 1200000
})

request.interceptors.request.use(
  (config) => {
    const auth = useAuthStore()
    if (auth.token) {
      // ⭐⭐⭐ 关键修复点 ⭐⭐⭐
      config.headers.Authorization = `Bearer ${auth.token}`
    }
    return config
  },
  (error) => Promise.reject(error)
)

request.interceptors.response.use(
  (res) => res.data,
  (err) => {
    const msg = err.response?.data?.detail || '请求失败'
    ElMessage.error(msg)
    return Promise.reject(err)
  }
)

export default request
