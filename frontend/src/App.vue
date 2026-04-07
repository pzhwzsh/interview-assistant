<template>
  <div class="app-container">
    <el-header class="header">
      <div class="header-content">
        <h1 class="logo">🎯 面试助手</h1>
        <el-menu mode="horizontal" :ellipsis="false" class="nav-menu" :default-active="activeMenu" @select="handleMenuSelect">
          <el-menu-item index="/">首页</el-menu-item>
          <el-menu-item index="/interview">开始面试</el-menu-item>
          <el-menu-item index="/history">历史记录</el-menu-item>
          <el-menu-item v-if="!isLoggedIn" index="/auth">登录/注册</el-menu-item>
          <el-menu-item v-else @click="handleLogout">退出登录</el-menu-item>
        </el-menu>
      </div>
    </el-header>

    <el-main class="main-content">
      <router-view />
    </el-main>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useInterviewStore } from '@/stores/interview'
import { ElMessage } from 'element-plus'

const route = useRoute()
const router = useRouter()
const store = useInterviewStore()

const activeMenu = computed(() => route.path)
const isLoggedIn = computed(() => !!localStorage.getItem('access_token'))

function handleMenuSelect(index: string) {
  router.push(index)
}

function handleLogout() {
  store.logout()
  ElMessage.success('已退出登录')
  router.push('/auth')
}
</script>

<style scoped>
.app-container {
  min-height: 100vh;
  background: #f5f7fa;
}

.header {
  background: #fff;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  padding: 0;
}

.header-content {
  max-width: 1400px;
  margin: 0 auto;
  display: flex;
  align-items: center;
  padding: 0 20px;
}

.logo {
  font-size: 24px;
  color: #00a1d6;
  margin-right: 40px;
}

.nav-menu {
  flex: 1;
  border-bottom: none;
}

.main-content {
  max-width: 1400px;
  margin: 0 auto;
  padding: 20px;
}
</style>
