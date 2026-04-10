<template>
  <div class="interview-container">
    <el-row :gutter="20">
      <el-col :span="16">
        <el-card class="question-card" shadow="hover" v-loading="store.loading">
          <template #header>
            <div class="question-header">
              <el-tag :style="{ backgroundColor: getDifficultyColor(interviewConfig?.difficulty) }" effect="dark">
                {{ getDifficultyText(interviewConfig?.difficulty) }}
              </el-tag>
              <el-tag type="info" effect="plain">{{ interviewConfig?.language }}</el-tag>
              <el-tag type="warning" effect="plain">{{ interviewConfig?.project_type }}</el-tag>
              <div class="timer">
                <el-icon><Clock /></el-icon>
                <span>{{ formatTime(timer) }}</span>
              </div>
            </div>
          </template>

          <div v-if="!store.currentQuestion" class="empty-state">
            <el-empty description="点击生成题目开始面试" />
            <el-button type="primary" size="large" @click="generateNewQuestion" :loading="store.loading">
              🎲 生成题目
            </el-button>
          </div>

          <div v-else class="question-content">
            <h3 class="question-title">{{ store.currentQuestion.question }}</h3>

            <el-collapse v-if="store.currentQuestion.hints?.length" class="hints-section">
              <el-collapse-item title="💡 查看提示" name="1">
                <ul class="hints-list">
                  <li v-for="(hint, index) in store.currentQuestion.hints" :key="index">
                    {{ hint }}
                  </li>
                </ul>
              </el-collapse-item>
            </el-collapse>

            <el-divider />

            <div class="answer-section">
              <h4>答题模式：</h4>
              <el-radio-group v-model="answerMode" size="large" class="mode-switcher">
                <el-radio-button label="text">📝 文字描述</el-radio-button>
                <el-radio-button label="code">💻 代码实现</el-radio-button>
              </el-radio-group>

              <div v-if="answerMode === 'text'" class="text-answer">
                <el-input
                  v-model="textAnswer"
                  type="textarea"
                  :rows="12"
                  placeholder="请详细回答，包括思路、实现细节、优缺点分析..."
                  maxlength="5000"
                  show-word-limit
                  @input="handleAnswerInput"
                />
              </div>

              <div v-else class="code-answer">
                <CodeEditor
                  v-model="codeAnswer"
                  :language="interviewConfig?.language || 'python'"
                  :editor-height="450"
                  :show-run-button="true"
                  @run="handleRunCode"
                />
              </div>

              <div v-if="validationResult" class="validation-result">
                <el-alert
                  v-if="!validationResult.is_valid"
                  type="error"
                  :closable="false"
                  show-icon
                >
                  <div v-for="(error, idx) in validationResult.errors" :key="idx">
                    {{ error }}
                  </div>
                </el-alert>

                <el-alert
                  v-if="validationResult.warnings.length"
                  type="warning"
                  :closable="false"
                  show-icon
                >
                  <div v-for="(warn, idx) in validationResult.warnings" :key="idx">
                    {{ warn }}
                  </div>
                </el-alert>

                <el-alert
                  v-if="validationResult.suggestions.length"
                  type="info"
                  :closable="false"
                  show-icon
                >
                  <div v-for="(sugg, idx) in validationResult.suggestions" :key="idx">
                    {{ sugg }}
                  </div>
                </el-alert>
              </div>
            </div>

            <div class="confidence-section">
              <span>自信程度：</span>
              <el-rate v-model="confidence" :max="10" show-score />
            </div>

            <div class="action-buttons">
              <el-button @click="generateNewQuestion" :disabled="store.loading">
                🔄 换一题
              </el-button>
              <el-button
                type="primary"
                @click="submitAnswer"
                :loading="store.loading"
                :disabled="!canSubmit"
              >
                ✓ 提交答案
              </el-button>
            </div>
          </div>
        </el-card>
      </el-col>

      <el-col :span="8">
        <el-card class="stats-card" shadow="hover">
          <template #header>
            <span>📊 答题统计</span>
          </template>
          <div class="stats-content">
            <div class="stat-item">
              <span class="label">已答时间</span>
              <span class="value">{{ formatTime(timer) }}</span>
            </div>
            <div class="stat-item">
              <span class="label">答案长度</span>
              <span class="value">{{ answerLength }} 字</span>
            </div>
            <div class="stat-item">
              <span class="label">预计时间</span>
              <span class="value">{{ store.currentQuestion?.estimated_time_minutes || 15 }} 分钟</span>
            </div>
            <div class="stat-item" v-if="answerMode === 'code'">
              <span class="label">答题模式</span>
              <span class="value">💻 代码</span>
            </div>
          </div>
        </el-card>

        <el-card class="tips-card" shadow="hover" v-if="evaluation">
          <template #header>
            <span>📝 评估结果</span>
          </template>
          <div class="evaluation-content">
            <div class="score-display">
              <el-progress
                type="circle"
                :percentage="evaluation.score"
                :color="getScoreColor(evaluation.score)"
              />
              <div class="score-text">{{ evaluation.score }} 分</div>
            </div>

            <el-divider />

            <div class="feedback-section">
              <h4>反馈：</h4>
              <p>{{ evaluation.feedback }}</p>
            </div>

            <div v-if="evaluation.strengths.length" class="strengths-section">
              <h4>✅ 优点：</h4>
              <ul>
                <li v-for="(item, idx) in evaluation.strengths" :key="idx">{{ item }}</li>
              </ul>
            </div>

            <div v-if="evaluation.weaknesses.length" class="weaknesses-section">
              <h4>⚠️ 不足：</h4>
              <ul>
                <li v-for="(item, idx) in evaluation.weaknesses" :key="idx">{{ item }}</li>
              </ul>
            </div>

            <div v-if="evaluation.suggested_improvements.length" class="improvements-section">
              <h4>💡 改进建议：</h4>
              <ul>
                <li v-for="(item, idx) in evaluation.suggested_improvements" :key="idx">{{ item }}</li>
              </ul>
            </div>

            <el-button type="primary" @click="generateNewQuestion" style="width: 100%; margin-top: 20px">
              下一题
            </el-button>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { Clock } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { useInterviewStore } from '@/stores/interview'
import { formatTime, getDifficultyText, getDifficultyColor, getScoreColor } from '@/utils/format'
import { useRouter } from 'vue-router'
import CodeEditor from '@/components/CodeEditor.vue'

const props = defineProps<{
  initialConfig: any
}>()

const router = useRouter()
const store = useInterviewStore()
const answerMode = ref<'text' | 'code'>('text')
const textAnswer = ref('')
const codeAnswer = ref('')
const confidence = ref(5)
const timer = ref(0)
let timerInterval: any = null
const validationResult = ref<any>(null)
const evaluation = ref<any>(null)
const startTime = ref(Date.now())
const runOutput = ref('')

const interviewConfig = computed(() => {
  if (props.initialConfig) return props.initialConfig
  const saved = sessionStorage.getItem('interview_config')
  return saved ? JSON.parse(saved) : null
})

const answerLength = computed(() => {
  return answerMode.value === 'text' ? textAnswer.value.length : codeAnswer.value.length
})

const canSubmit = computed(() => {
  if (answerMode.value === 'text') {
    return textAnswer.value.trim().length >= 20
  } else {
    return codeAnswer.value.trim().length >= 10
  }
})

onMounted(() => {
  const token = localStorage.getItem('access_token')
  if (!token) {
    ElMessage.warning('请先登录')
    router.push('/auth')
    return
  }

  if (!interviewConfig.value) {
    ElMessage.warning('请先配置面试')
    router.push('/')
    return
  }

  startTimer()
})

onUnmounted(() => {
  stopTimer()
})

function startTimer() {
  startTime.value = Date.now()
  timerInterval = setInterval(() => {
    timer.value = Math.floor((Date.now() - startTime.value) / 1000)
  }, 1000)
}

function stopTimer() {
  if (timerInterval) {
    clearInterval(timerInterval)
  }
}

async function generateNewQuestion() {
  evaluation.value = null
  textAnswer.value = ''
  codeAnswer.value = ''
  confidence.value = 5
  validationResult.value = null
  runOutput.value = ''
  stopTimer()

  try {
    console.log('开始生成新题目，配置:', interviewConfig.value)
    const question = await store.generateQuestion(interviewConfig.value)
    console.log('题目生成成功:', question)

    if (!question || !question.question_id) {
      throw new Error('返回的题目数据不完整')
    }

    startTimer()
    ElMessage.success('题目生成成功')
  } catch (error: any) {
    console.error('生成题目失败:', error)
    ElMessage.error(error.response?.data?.detail || error.message || '生成题目失败，请检查配置')
  }
}

function handleAnswerInput() {
  if (textAnswer.value.length > 50) {
    validationResult.value = null
  }
}

async function handleRunCode({ code, language }: { code: string; language: string }) {
  runOutput.value = `正在运行 ${language} 代码...\n\n`

  const controller = new AbortController()
  const timeoutId = setTimeout(() => controller.abort(), 10000)

  try {
    const response = await fetch('/api/run-code', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ code, language }),
      signal: controller.signal
    })

    clearTimeout(timeoutId)

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`)
    }

    const result = await response.json()

    if (result.error) {
      runOutput.value = result.error
    } else {
      runOutput.value = result.output || '代码执行完成，无输出'
    }
  } catch (error: any) {
    clearTimeout(timeoutId)

    if (error.name === 'AbortError') {
      runOutput.value = '⏱️ 请求超时，请稍后重试'
    } else {
      runOutput.value = `运行失败: ${error.message}\n\n注意：代码运行功能需要后端支持。`
    }
  }
}

async function submitAnswer() {
  if (!canSubmit.value || !store.currentQuestion) return

  stopTimer()

  const finalAnswer = answerMode.value === 'text' ? textAnswer.value : codeAnswer.value

  try {
    const result = await store.submitAnswer({
      question_id: store.currentQuestion.question_id,
      answer: finalAnswer,
      time_spent_seconds: timer.value,
      self_confidence: confidence.value,
      answer_type: answerMode.value
    })

    evaluation.value = result
    ElMessage.success('答案提交成功')
  } catch (error: any) {
    if (error.response?.data?.detail?.validation_errors) {
      validationResult.value = {
        is_valid: false,
        errors: error.response.data.detail.validation_errors,
        warnings: [],
        suggestions: []
      }
      ElMessage.warning('请修正答案后再提交')
    } else {
      ElMessage.error('提交失败，请重试')
    }
  }
}
</script>

<style scoped>
.interview-container {
  max-width: 1400px;
  margin: 0 auto;
}

.question-header {
  display: flex;
  align-items: center;
  gap: 10px;
}

.timer {
  margin-left: auto;
  display: flex;
  align-items: center;
  gap: 5px;
  font-size: 18px;
  font-weight: bold;
  color: #409eff;
}

.empty-state {
  text-align: center;
  padding: 40px 0;
}

.question-title {
  font-size: 20px;
  line-height: 1.6;
  margin-bottom: 20px;
  color: #303133;
}

.hints-section {
  margin-bottom: 20px;
}

.hints-list {
  padding-left: 20px;
  line-height: 1.8;
}

.answer-section h4 {
  margin-bottom: 10px;
  color: #606266;
}

.mode-switcher {
  margin-bottom: 15px;
}

.text-answer, .code-answer {
  margin-top: 10px;
}

.validation-result {
  margin-top: 15px;
}

.confidence-section {
  margin-top: 20px;
  display: flex;
  align-items: center;
  gap: 15px;
}

.action-buttons {
  margin-top: 20px;
  display: flex;
  gap: 10px;
  justify-content: flex-end;
}

.stats-card, .tips-card {
  margin-bottom: 20px;
}

.stats-content {
  padding: 10px 0;
}

.stat-item {
  display: flex;
  justify-content: space-between;
  padding: 12px 0;
  border-bottom: 1px solid #f0f0f0;
}

.stat-item:last-child {
  border-bottom: none;
}

.stat-item .label {
  color: #909399;
}

.stat-item .value {
  font-weight: bold;
  color: #303133;
}

.evaluation-content {
  padding: 10px 0;
}

.score-display {
  text-align: center;
}

.score-text {
  margin-top: 10px;
  font-size: 24px;
  font-weight: bold;
  color: #409eff;
}

.feedback-section, .strengths-section, .weaknesses-section, .improvements-section {
  margin-top: 15px;
}

.feedback-section h4, .strengths-section h4, .weaknesses-section h4, .improvements-section h4 {
  margin-bottom: 10px;
  color: #606266;
}

.feedback-section p {
  line-height: 1.8;
  color: #606266;
}

.strengths-section ul, .weaknesses-section ul, .improvements-section ul {
  padding-left: 20px;
  line-height: 1.8;
}
</style>
