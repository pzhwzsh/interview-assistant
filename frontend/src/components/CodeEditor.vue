<template>
  <div class="code-editor-container">
    <div class="editor-header">
      <div class="language-selector">
        <span class="label">编程语言：</span>
        <el-select v-model="selectedLanguage" size="small" style="width: 150px">
          <el-option label="Python" value="python" />
          <el-option label="JavaScript" value="javascript" />
          <el-option label="TypeScript" value="typescript" />
          <el-option label="Java" value="java" />
          <el-option label="Go" value="go" />
        </el-select>
      </div>

      <div class="editor-actions">
        <el-button size="small" @click="handleReset" type="warning">
          <el-icon><RefreshRight /></el-icon>
          重置
        </el-button>
        <el-button size="small" @click="handleCopy" type="primary">
          <el-icon><DocumentCopy /></el-icon>
          复制
        </el-button>
      </div>
    </div>

    <textarea
      ref="codeTextarea"
      v-model="codeContent"
      class="code-textarea"
      :style="{ height: editorHeight + 'px' }"
      spellcheck="false"
      @input="handleInput"
    ></textarea>

    <div class="editor-footer">
      <div class="status-info">
        <span>行数: {{ lineCount }}</span>
        <span>字符: {{ charCount }}</span>
      </div>
      <el-button
        v-if="showRunButton"
        type="success"
        size="small"
        @click="handleRun"
        :loading="running"
      >
        <el-icon><VideoPlay /></el-icon>
        运行代码
      </el-button>
    </div>

    <div v-if="runOutput" class="run-output">
      <div class="output-header">
        <span>运行结果</span>
        <el-button size="small" text @click="runOutput = ''">清空</el-button>
      </div>
      <pre class="output-content">{{ runOutput }}</pre>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, computed } from 'vue'
import { RefreshRight, DocumentCopy, VideoPlay } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'

const props = defineProps<{
  modelValue?: string
  language?: string
  editorHeight?: number
  showRunButton?: boolean
}>()

const emit = defineEmits(['update:modelValue', 'run'])

const selectedLanguage = ref(props.language || 'python')
const codeContent = ref(props.modelValue || '')
const running = ref(false)
const runOutput = ref('')
const codeTextarea = ref<HTMLTextAreaElement>()

const editorHeight = ref(props.editorHeight || 400)

const lineCount = computed(() => {
  return codeContent.value.split('\n').length
})

const charCount = computed(() => {
  return codeContent.value.length
})

function getDefaultCode(lang: string): string {
  const templates: Record<string, string> = {
    python: '# 在这里编写你的代码\n\ndef solution():\n    # TODO: 实现你的逻辑\n    pass\n\nif __name__ == "__main__":\n    print(solution())',
    javascript: '// 在这里编写你的代码\n\nfunction solution() {\n  // TODO: 实现你的逻辑\n}\n\nconsole.log(solution());',
    typescript: '// 在这里编写你的代码\n\nfunction solution(): void {\n  // TODO: 实现你的逻辑\n}\n\nconsole.log(solution());',
    java: 'public class Solution {\n    public static void main(String[] args) {\n        // TODO: 实现你的逻辑\n        System.out.println("Hello World");\n    }\n}',
    go: 'package main\n\nimport "fmt"\n\nfunc main() {\n    // TODO: 实现你的逻辑\n    fmt.Println("Hello World")\n}'
  }
  return templates[lang] || '// Start coding here...'
}

function handleInput() {
  emit('update:modelValue', codeContent.value)
}

function handleReset() {
  codeContent.value = getDefaultCode(selectedLanguage.value)
  emit('update:modelValue', codeContent.value)
  ElMessage.info('已重置为默认模板')
}

async function handleCopy() {
  try {
    await navigator.clipboard.writeText(codeContent.value)
    ElMessage.success('代码已复制到剪贴板')
  } catch (error) {
    ElMessage.error('复制失败')
  }
}

async function handleRun() {
  running.value = true
  runOutput.value = ''

  try {
    emit('run', { code: codeContent.value, language: selectedLanguage.value })
  } catch (error: any) {
    runOutput.value = `运行错误: ${error.message}`
  } finally {
    running.value = false
  }
}

watch(() => props.modelValue, (newValue) => {
  if (newValue !== undefined && newValue !== codeContent.value) {
    codeContent.value = newValue
  }
})

watch(() => props.language, (newLang) => {
  if (newLang) {
    selectedLanguage.value = newLang
  }
})

// 初始化默认代码
if (!codeContent.value) {
  codeContent.value = getDefaultCode(selectedLanguage.value)
}
</script>

<style scoped>
.code-editor-container {
  border: 1px solid #dcdfe6;
  border-radius: 4px;
  overflow: hidden;
  background: #1e1e1e;
}

.editor-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 15px;
  background: #2d2d2d;
  border-bottom: 1px solid #3e3e3e;
}

.language-selector {
  display: flex;
  align-items: center;
  gap: 10px;
}

.language-selector .label {
  color: #ccc;
  font-size: 14px;
}

.editor-actions {
  display: flex;
  gap: 8px;
}

.code-textarea {
  width: 100%;
  background: #1e1e1e;
  color: #d4d4d4;
  border: none;
  padding: 15px;
  font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
  font-size: 14px;
  line-height: 1.6;
  resize: none;
  outline: none;
  tab-size: 2;
}

.code-textarea:focus {
  background: #1e1e1e;
  color: #d4d4d4;
}

.editor-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 15px;
  background: #2d2d2d;
  border-top: 1px solid #3e3e3e;
}

.status-info {
  display: flex;
  gap: 20px;
  color: #999;
  font-size: 12px;
}

.run-output {
  border-top: 1px solid #3e3e3e;
  background: #1a1a1a;
}

.output-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 15px;
  background: #252525;
  color: #ccc;
  font-size: 13px;
}

.output-content {
  margin: 0;
  padding: 15px;
  color: #4ec9b0;
  font-family: 'Consolas', 'Monaco', monospace;
  font-size: 13px;
  line-height: 1.6;
  max-height: 200px;
  overflow-y: auto;
  white-space: pre-wrap;
  word-break: break-all;
}
</style>


