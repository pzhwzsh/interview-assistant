<template>
  <div class="favorites-container">
    <el-tabs v-model="activeTab" type="card">
      <el-tab-pane label="⭐ 我的收藏" name="favorites">
        <el-card shadow="hover">
          <template #header>
            <div class="card-header">
              <span>收藏的题目</span>
              <el-tag type="info">{{ favorites.length }} 题</el-tag>
            </div>
          </template>

          <el-empty v-if="!favorites.length" description="暂无收藏题目" />

          <div v-else class="question-list">
            <el-card
              v-for="(item, index) in favorites"
              :key="index"
              class="question-item"
              shadow="hover"
            >
              <div class="question-header">
                <el-tag size="small">{{ item.difficulty }}</el-tag>
                <el-tag size="small" type="info">{{ item.language }}</el-tag>
                <el-button
                  size="small"
                  type="danger"
                  text
                  @click="removeFavorite(item.id)"
                >
                  取消收藏
                </el-button>
              </div>
              <div class="question-content">{{ item.content }}</div>
            </el-card>
          </div>
        </el-card>
      </el-tab-pane>

      <el-tab-pane label="❌ 错题本" name="wrong">
        <el-card shadow="hover">
          <template #header>
            <div class="card-header">
              <span>需要复习的题目</span>
              <el-tag type="danger">{{ wrongQuestions.length }} 题</el-tag>
            </div>
          </template>

          <el-empty v-if="!wrongQuestions.length" description="太棒了！暂无错题" />

          <div v-else class="question-list">
            <el-card
              v-for="(item, index) in wrongQuestions"
              :key="index"
              class="question-item"
              shadow="hover"
            >
              <div class="question-header">
                <el-tag size="small" type="danger">{{ item.score }}分</el-tag>
                <el-tag size="small">{{ item.difficulty }}</el-tag>
                <span class="question-time">{{ formatDate(item.submitted_at) }}</span>
              </div>
              <div class="question-content">{{ item.question_content }}</div>

              <el-divider />

              <div class="answer-review">
                <h4>你的回答：</h4>
                <p>{{ item.your_answer }}</p>

                <h4>反馈：</h4>
                <p>{{ item.feedback }}</p>
              </div>
            </el-card>
          </div>
        </el-card>
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import axios from 'axios'

const activeTab = ref('favorites')
const favorites = ref<any[]>([])
const wrongQuestions = ref<any[]>([])

const userId = localStorage.getItem('user_id') || ''

onMounted(() => {
  loadFavorites()
  loadWrongQuestions()
})

async function loadFavorites() {
  if (!userId) return

  try {
    const response = await axios.get(`/api/user-favorites/${userId}`)
    favorites.value = response.data.favorites
  } catch (error) {
    console.error('加载收藏失败:', error)
  }
}

async function loadWrongQuestions() {
  if (!userId) return

  try {
    const response = await axios.get(`/api/wrong-questions/${userId}`)
    wrongQuestions.value = response.data.wrong_questions
  } catch (error) {
    console.error('加载错题失败:', error)
  }
}

async function removeFavorite(questionId: string) {
  try {
    await axios.post(`/api/favorite/${questionId}?user_id=${userId}`)
    ElMessage.success('已取消收藏')
    loadFavorites()
  } catch (error) {
    ElMessage.error('操作失败')
  }
}

function formatDate(dateStr: string): string {
  return new Date(dateStr).toLocaleDateString('zh-CN')
}
</script>

<style scoped>
.favorites-container {
  max-width: 1200px;
  margin: 0 auto;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.question-list {
  display: flex;
  flex-direction: column;
  gap: 15px;
}

.question-item {
  transition: transform 0.2s;
}

.question-item:hover {
  transform: translateY(-2px);
}

.question-header {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 10px;
}

.question-time {
  margin-left: auto;
  color: #909399;
  font-size: 12px;
}

.question-content {
  line-height: 1.6;
  color: #606266;
}

.answer-review {
  margin-top: 15px;
}

.answer-review h4 {
  margin: 10px 0 5px 0;
  color: #606266;
  font-size: 14px;
}

.answer-review p {
  color: #909399;
  line-height: 1.6;
  font-size: 14px;
}
</style>
