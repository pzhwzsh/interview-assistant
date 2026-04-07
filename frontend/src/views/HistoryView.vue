<template>
  <div class="history-container">
    <el-card class="stats-card" shadow="hover">
      <template #header>
        <span>📊 学习统计</span>
      </template>
      <el-row :gutter="20">
        <el-col :span="6">
          <div class="stat-box">
            <div class="stat-value">{{ historyData?.total_questions || 0 }}</div>
            <div class="stat-label">总答题数</div>
          </div>
        </el-col>
        <el-col :span="6">
          <div class="stat-box">
            <div class="stat-value">{{ (historyData?.average_score || 0).toFixed(1) }}</div>
            <div class="stat-label">平均分数</div>
          </div>
        </el-col>
        <el-col :span="6">
          <div class="stat-box">
            <div class="stat-value">{{ thisWeekCount }}</div>
            <div class="stat-label">本周答题</div>
          </div>
        </el-col>
        <el-col :span="6">
          <div class="stat-box">
            <div class="stat-value">{{ historyData?.difficulty_distribution ? Object.keys(historyData.difficulty_distribution).length : 0 }}</div>
            <div class="stat-label">涉及难度</div>
          </div>
        </el-col>
      </el-row>
    </el-card>

    <el-card class="records-card" shadow="hover" style="margin-top: 20px">
      <template #header>
        <div class="card-header">
          <span>📝 最近一周答题记录</span>
          <el-button size="small" @click="loadHistoryData">
            <el-icon><Refresh /></el-icon>
            刷新
          </el-button>
        </div>
      </template>

      <el-empty v-if="!thisWeekRecords.length" description="最近一周暂无答题记录" />

      <div v-else class="records-list">
        <el-collapse v-model="activeNames" accordion>
          <el-collapse-item
            v-for="(record, index) in thisWeekRecords"
            :key="record.id"
            :name="index"
          >
            <template #title>
              <div class="record-title">
                <el-tag :style="{ backgroundColor: getScoreColor(record.score) }" effect="dark" size="small">
                  {{ record.score }}分
                </el-tag>
                <span class="question-preview">{{ record.question_content?.substring(0, 50) }}...</span>
                <span class="record-time">{{ formatDate(record.submitted_at) }}</span>
              </div>
            </template>

            <div class="record-detail">
              <el-divider content-position="left">📋 题目</el-divider>
              <div class="detail-section">
                <p>{{ record.question_content }}</p>
              </div>

              <el-divider content-position="left">✍️ 你的答案</el-divider>
              <div class="detail-section answer-section">
                <pre>{{ record.answer_content }}</pre>
              </div>

              <el-divider content-position="left">📊 评估结果</el-divider>
              <div class="detail-section">
                <el-descriptions :column="2" border>
                  <el-descriptions-item label="得分">
                    <el-tag :style="{ backgroundColor: getScoreColor(record.score) }" effect="dark">
                      {{ record.score }} 分
                    </el-tag>
                  </el-descriptions-item>
                  <el-descriptions-item label="用时">
                    {{ formatTime(record.time_spent) }}
                  </el-descriptions-item>
                </el-descriptions>

                <div class="feedback-box" v-if="record.feedback">
                  <h4>💬 评估反馈：</h4>
                  <p>{{ record.feedback }}</p>
                </div>

                <div class="strengths-box" v-if="record.evaluation_details?.strengths?.length">
                  <h4>✅ 优点：</h4>
                  <ul>
                    <li v-for="(item, idx) in record.evaluation_details.strengths" :key="idx">{{ item }}</li>
                  </ul>
                </div>

                <div class="weaknesses-box" v-if="record.evaluation_details?.weaknesses?.length">
                  <h4>⚠️ 不足：</h4>
                  <ul>
                    <li v-for="(item, idx) in record.evaluation_details.weaknesses" :key="idx">{{ item }}</li>
                  </ul>
                </div>

                <div class="improvements-box" v-if="record.evaluation_details?.suggested_improvements?.length">
                  <h4>💡 改进建议：</h4>
                  <ul>
                    <li v-for="(item, idx) in record.evaluation_details.suggested_improvements" :key="idx">{{ item }}</li>
                  </ul>
                </div>
              </div>
            </div>
          </el-collapse-item>
        </el-collapse>
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { Refresh } from '@element-plus/icons-vue'
import { useInterviewStore } from '@/stores/interview'
import { formatDate, formatTime, getScoreColor } from '@/utils/format'

const store = useInterviewStore()
const historyData = ref<any>(null)
const activeNames = ref<number[]>([])

const thisWeekRecords = computed(() => {
  if (!historyData.value?.recent_answers) return []

  const oneWeekAgo = new Date()
  oneWeekAgo.setDate(oneWeekAgo.getDate() - 7)

  return historyData.value.recent_answers.filter((record: any) => {
    const recordDate = new Date(record.submitted_at)
    return recordDate >= oneWeekAgo
  })
})

const thisWeekCount = computed(() => thisWeekRecords.value.length)

onMounted(() => {
  loadHistoryData()
})

async function loadHistoryData() {
  try {
    historyData.value = await store.loadHistory()
  } catch (error) {
    console.error('加载历史记录失败:', error)
  }
}
</script>

<style scoped>
.history-container {
  max-width: 1200px;
  margin: 0 auto;
}

.stats-card {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
}

.stat-box {
  text-align: center;
  padding: 20px;
}

.stat-value {
  font-size: 36px;
  font-weight: bold;
  margin-bottom: 10px;
}

.stat-label {
  font-size: 14px;
  opacity: 0.9;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.records-list {
  margin-top: 10px;
}

.record-title {
  display: flex;
  align-items: center;
  gap: 15px;
  width: 100%;
}

.question-preview {
  flex: 1;
  color: #606266;
  font-size: 14px;
}

.record-time {
  color: #909399;
  font-size: 12px;
}

.record-detail {
  padding: 10px;
}

.detail-section {
  margin: 15px 0;
  line-height: 1.8;
}

.detail-section h4 {
  margin-bottom: 10px;
  color: #606266;
}

.detail-section p {
  color: #606266;
  white-space: pre-wrap;
}

.answer-section pre {
  background: #f5f7fa;
  padding: 15px;
  border-radius: 4px;
  white-space: pre-wrap;
  word-wrap: break-word;
  font-family: 'Courier New', monospace;
  font-size: 14px;
  line-height: 1.6;
  max-height: 400px;
  overflow-y: auto;
}

.feedback-box, .strengths-box, .weaknesses-box, .improvements-box {
  margin-top: 15px;
  padding: 15px;
  background: #f9fafb;
  border-radius: 4px;
}

.feedback-box h4, .strengths-box h4, .weaknesses-box h4, .improvements-box h4 {
  margin-bottom: 10px;
  color: #303133;
}

.feedback-box p {
  color: #606266;
  line-height: 1.8;
}

.strengths-box ul, .weaknesses-box ul, .improvements-box ul {
  padding-left: 20px;
  color: #606266;
}

.strengths-box li, .weaknesses-box li, .improvements-box li {
  margin: 5px 0;
}
</style>

