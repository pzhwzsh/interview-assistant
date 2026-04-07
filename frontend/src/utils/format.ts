export function formatTime(seconds: number): string {
  const mins = Math.floor(seconds / 60)
  const secs = seconds % 60
  return `${mins}:${secs.toString().padStart(2, '0')}`
}

export function formatDate(dateStr: string): string {
  const date = new Date(dateStr)
  return date.toLocaleString('zh-CN')
}

export function getDifficultyText(level: string): string {
  const map: Record<string, string> = {
    beginner: '入门',
    intermediate: '中级',
    advanced: '高级',
    expert: '专家'
  }
  return map[level] || level
}

export function getDifficultyColor(level: string): string {
  const map: Record<string, string> = {
    beginner: '#67c23a',
    intermediate: '#409eff',
    advanced: '#e6a23c',
    expert: '#f56c6c'
  }
  return map[level] || '#909399'
}

export function getScoreColor(score: number): string {
  if (score >= 90) return '#67c23a'
  if (score >= 75) return '#409eff'
  if (score >= 60) return '#e6a23c'
  return '#f56c6c'
}
