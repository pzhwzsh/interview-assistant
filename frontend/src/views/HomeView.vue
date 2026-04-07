<template>
  <div class="home-container">
    <div class="banner-section">
      <el-card class="banner-card" shadow="hover">
        <h2>🚀 AI 面试助手</h2>
        <p>基于 DeepSeek AI 的智能面试练习平台</p>
        <div class="features">
          <el-tag type="success" effect="plain">多语言支持</el-tag>
          <el-tag type="warning" effect="plain">难度分级</el-tag>
          <el-tag type="danger" effect="plain">智能评估</el-tag>
          <el-tag type="info" effect="plain">历史记录</el-tag>
        </div>
      </el-card>
    </div>

    <div class="config-section">
      <el-card shadow="hover">
        <template #header>
          <div class="card-header">
            <span>⚙️ 面试配置</span>
          </div>
        </template>

        <el-form :model="config" label-width="120px">
          <el-form-item label="编程语言">
            <el-select v-model="config.language" placeholder="选择语言" style="width: 100%">
              <el-option label="Python" value="python" />
              <el-option label="Java" value="java" />
              <el-option label="JavaScript" value="javascript" />
              <el-option label="Go" value="go" />
              <el-option label="Rust" value="rust" />
              <el-option label="C++" value="cpp" />
            </el-select>
          </el-form-item>

          <el-form-item label="项目类型">
            <el-select v-model="config.project_type" placeholder="选择项目类型" style="width: 100%">
              <el-option label="Web 后端" value="web_backend" />
              <el-option label="移动应用" value="mobile_app" />
              <el-option label="数据管道" value="data_pipeline" />
              <el-option label="微服务" value="microservices" />
              <el-option label="分布式系统" value="distributed_system" />
              <el-option label="AI/ML" value="ai_ml" />
            </el-select>
          </el-form-item>

          <el-form-item label="难度级别">
            <el-radio-group v-model="config.difficulty">
              <el-radio-button label="beginner">入门</el-radio-button>
              <el-radio-button label="intermediate">中级</el-radio-button>
              <el-radio-button label="advanced">高级</el-radio-button>
              <el-radio-button label="expert">专家</el-radio-button>
            </el-radio-group>
          </el-form-item>

          <el-form-item label="重点关注（可选）">
            <el-input
              v-model="config.topic_focus"
              placeholder="例如：并发编程、设计模式..."
              clearable
            />
          </el-form-item>

          <el-form-item>
            <el-button type="primary" size="large" @click="handleStart" :loading="loading" style="width: 100%">
              🎯 开始面试
            </el-button>
          </el-form-item>
        </el-form>
      </el-card>
    </div>

    <div class="recommendation-section">
      <el-row :gutter="20">
        <el-col :span="8" v-for="(item, index) in recommendations" :key="index">
          <el-card class="rec-card" shadow="hover" @click="applyRecommendation(item)">
            <div class="rec-icon">{{ item.icon }}</div>
            <h3>{{ item.title }}</h3>
            <p>{{ item.desc }}</p>
          </el-card>
        </el-col>
      </el-row>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'

const router = useRouter()

const config = reactive({
  language: 'python',
  project_type: 'web_backend',
  difficulty: 'intermediate',
  topic_focus: ''
})

const loading = ref(false)

const recommendations = [
  { icon: '🔥', title: '热门题目', desc: '高频面试题练习', config: { difficulty: 'intermediate' } },
  { icon: '💪', title: '挑战自我', desc: '高级难度突破', config: { difficulty: 'advanced' } },
  { icon: '📚', title: '基础巩固', desc: '夯实基础知识', config: { difficulty: 'beginner' } }
]

const handleStart = () => {
  if (!config.language || !config.project_type || !config.difficulty) {
    ElMessage.warning('请选择完整的面试配置')
    return
  }

  // 检查是否登录
  const token = localStorage.getItem('access_token')
  if (!token) {
    ElMessage.warning('请先登录')
    router.push('/auth')
    return
  }

  // 保存配置到 sessionStorage
  sessionStorage.setItem('interview_config', JSON.stringify(config))
  router.push('/interview')
}

const applyRecommendation = (item: any) => {
  Object.assign(config, item.config)
}
</script>

<style scoped>
.home-container {
  max-width: 1200px;
  margin: 0 auto;
}

.banner-section {
  margin-bottom: 30px;
}

.banner-card {
  text-align: center;
  padding: 20px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border: none;
}

.banner-card h2 {
  font-size: 32px;
  margin: 0 0 10px 0;
}

.banner-card p {
  font-size: 16px;
  opacity: 0.9;
  margin: 0 0 20px 0;
}

.features {
  display: flex;
  gap: 10px;
  justify-content: center;
  flex-wrap: wrap;
}

.features .el-tag {
  background: rgba(255, 255, 255, 0.2);
  border-color: rgba(255, 255, 255, 0.3);
  color: white;
}

.config-section {
  margin-bottom: 30px;
}

.card-header {
  font-weight: bold;
  font-size: 18px;
}

.recommendation-section {
  margin-top: 30px;
}

.rec-card {
  cursor: pointer;
  transition: transform 0.3s;
  text-align: center;
  height: 180px;
}

.rec-card:hover {
  transform: translateY(-5px);
}

.rec-icon {
  font-size: 48px;
  margin-bottom: 10px;
}

.rec-card h3 {
  margin: 10px 0;
  color: #303133;
}

.rec-card p {
  color: #909399;
  font-size: 14px;
}
</style>
