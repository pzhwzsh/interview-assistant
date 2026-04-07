<template>
  <div class="auth-container">
    <el-card class="auth-card">
      <h2>{{ isLogin ? '登录' : '注册' }}</h2>

      <el-form :model="form" label-width="80px">
        <el-form-item label="用户名">
          <el-input v-model="form.username" placeholder="请输入用户名" />
        </el-form-item>

        <el-form-item v-if="!isLogin" label="邮箱">
          <el-input v-model="form.email" placeholder="请输入邮箱" />
        </el-form-item>

        <el-form-item label="密码">
          <el-input
            v-model="form.password"
            type="password"
            placeholder="请输入密码"
            show-password
          />
        </el-form-item>

        <el-form-item>
          <el-button
            type="primary"
            @click="handleSubmit"
            :loading="loading"
            style="width: 100%"
          >
            {{ isLogin ? '登录' : '注册' }}
          </el-button>
        </el-form-item>
      </el-form>

      <div class="toggle-link">
        <a @click="toggleMode">
          {{ isLogin ? '没有账号？立即注册' : '已有账号？立即登录' }}
        </a>
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import axios from 'axios'
import { ElMessage } from 'element-plus'
import { useRouter } from 'vue-router'
import { useInterviewStore } from '../stores/interview'

const router = useRouter()
const store = useInterviewStore()
const isLogin = ref(true)
const loading = ref(false)

const form = reactive({
  username: '',
  email: '',
  password: ''
})

function toggleMode() {
  isLogin.value = !isLogin.value
  form.username = ''
  form.email = ''
  form.password = ''
}

async function handleSubmit() {
  if (!form.username || !form.password || (!isLogin.value && !form.email)) {
    ElMessage.warning('请填写完整信息')
    return
  }

  loading.value = true
  try {
    const endpoint = isLogin.value ? '/api/auth/login' : '/api/auth/register'
    const response = await axios.post(endpoint, {
      username: form.username,
      email: form.email,
      password: form.password
    })

    if (isLogin.value) {
      // 保存 Token 和用户信息
      localStorage.setItem('access_token', response.data.access_token)
      localStorage.setItem('user_id', response.data.user_id)
      localStorage.setItem('username', response.data.username)

      // 更新 store
      store.setUserInfo(response.data.user_id, response.data.username)
      store.login(response.data.access_token)

      ElMessage.success('登录成功')
      router.push('/')
    } else {
      ElMessage.success('注册成功，请登录')
      isLogin.value = true
    }
  } catch (error: any) {
    ElMessage.error(error.response?.data?.detail || '操作失败')
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.auth-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 60vh;
}

.auth-card {
  width: 450px;
  padding: 20px;
}

.auth-card h2 {
  text-align: center;
  margin-bottom: 30px;
  color: #303133;
}

.toggle-link {
  text-align: center;
  margin-top: 20px;
}

.toggle-link a {
  color: #409eff;
  cursor: pointer;
  text-decoration: none;
}

.toggle-link a:hover {
  text-decoration: underline;
}
</style>
