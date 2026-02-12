<template>
  <el-container class="layout">
    <el-header class="header">
      <div class="header-left">
        <div class="brand-mark">NW</div>
        <div>
          <div class="brand-title">AI写作平台</div>
          <div class="brand-sub">编辑部创作台</div>
        </div>
      </div>

      <div class="header-center">
        <div class="meta-card">
          <span class="meta-label">当前小说</span>
          <span class="meta-value">{{ novelId || '未选择' }}</span>
        </div>
        <div class="meta-card">
          <span class="meta-label">章节</span>
          <span class="meta-value">
            {{ chapter ? chapter.chapter_number : '-' }}
          </span>
        </div>
      </div>

      <div class="header-actions">
        <el-button
          size="small"
          class="header-btn"
          :loading="loading"
          @click="initNovelHandler"
        >
          初始化
        </el-button>
        <el-button
          size="small"
          class="header-btn"
          :loading="loading"
          :disabled="!novelId"
          @click="nextChapterHandler"
        >
          下一章
        </el-button>
        <el-button
          size="small"
          class="header-btn"
          :loading="exporting"
          :disabled="!novelId"
          @click="exportNovelHandler"
        >
          导出
        </el-button>
      </div>
    </el-header>

    <el-container>
      <el-aside width="320px" class="aside">
        <el-card class="card aside-card fixed-card settings-card">
          <div class="card-header-row">
            <h3 class="card-title">项目设置</h3>
            <span class="card-note">仅首次初始化需要主题</span>
          </div>
          <div class="card-scroll">
            <el-form label-position="top" class="aside-form">
              <el-form-item label="Novel ID">
                <el-input
                  v-model="novelId"
                  placeholder="选择或输入小说 ID"
                />
              </el-form-item>

              <el-form-item label="小说主题">
                <el-input
                  v-model="topic"
                  placeholder="仅第一次初始化需要"
                />
              </el-form-item>
            </el-form>
          </div>
        </el-card>

        <el-card class="card aside-card fixed-card actions-card">
          <div class="card-header-row">
            <h3 class="card-title">操作按钮</h3>
            <span class="card-note">一键生成并保存</span>
          </div>
          <div class="card-scroll">
            <div class="aside-actions">
              <el-button
                type="success"
                block
                :loading="loading"
                @click="initNovelHandler"
              >
                初始化小说
              </el-button>

              <el-button
                type="primary"
                block
                :loading="loading"
                :disabled="!novelId"
                @click="nextChapterHandler"
              >
                生成下一章
              </el-button>

              <el-button
                type="info"
                block
                :loading="exporting"
                :disabled="!novelId"
                @click="exportNovelHandler"
              >
                导出小说
              </el-button>
            </div>
          </div>
        </el-card>

        <div class="aside-bottom">
          <el-card class="card aside-card card-compact fixed-card library-card">
            <div class="card-header-row">
              <h3 class="card-title">我的创作中心</h3>
              <span class="card-note">点选快速加载</span>
            </div>
            <div class="card-scroll">
              <el-table
                :data="novels"
                size="small"
                style="width: 100%"
                height="100%"
                @row-click="selectNovel"
              >
                <el-table-column prop="novel_id" label="小说 ID" />
                <el-table-column prop="topic" label="主题" />
                <el-table-column
                  prop="current_chapter"
                  label="当前章节"
                  width="90"
                />
              </el-table>
            </div>
          </el-card>
        </div>
      </el-aside>

      <el-main class="main">
        <div class="workspace">
          <section class="workspace-primary">
            <el-card class="card fixed-card process-card">
              <div class="card-header-row">
                <h3 class="card-title">AI 创作流程</h3>
                <span class="card-badge">实时进度</span>
              </div>
              <div class="card-scroll">
                <el-steps
                  direction="vertical"
                  :active="activeStep"
                  finish-status="success"
                >
                  <el-step title="世界观构建" />
                  <el-step title="角色与状态分析" />
                  <el-step title="剧情推进规划" />
                  <el-step title="正文生成" />
                </el-steps>
              </div>
            </el-card>

            <el-card class="card chapter-card">
              <div class="card-header-row">
                <h3 class="card-title">章节正文</h3>
                <span v-if="chapter" class="card-badge">
                  第 {{ chapter.chapter_number }} 章
                </span>
              </div>

              <div v-if="chapter" class="chapter-body">
                <h2 class="chapter-title">
                  {{ chapter.title }}
                </h2>

                <div
                  v-if="chapter.rewrite && chapter.rewrite.reasons && chapter.rewrite.reasons.length"
                  class="rewrite-note"
                >
                  <span class="rewrite-label">已重写</span>
                  <span class="rewrite-reasons">
                    原因：{{ chapter.rewrite.reasons.join('、') }}
                  </span>
                </div>

                <pre class="content">{{ chapter.content }}</pre>
              </div>

              <el-empty
                v-else
                description="选择小说或生成下一章"
              />
            </el-card>
          </section>

          <aside class="workspace-secondary">
            <el-card class="card fixed-card review-card">
              <div class="card-header-row">
                <h3 class="card-title">章节评审</h3>
                <span v-if="chapter && chapter.review" class="card-badge">
                  {{ chapter.review.overall_score }}/10
                </span>
              </div>
              <div class="card-scroll">
                <div v-if="chapter && chapter.review" class="review">
                  <el-descriptions column="2" size="small" border>
                    <el-descriptions-item label="整体评分">
                      {{ chapter.review.overall_score }}/10
                    </el-descriptions-item>
                    <el-descriptions-item label="世界观一致性">
                      {{ chapter.review.world_consistency_score }}/10
                    </el-descriptions-item>
                    <el-descriptions-item label="是否跑题">
                      <el-tag
                        :type="chapter.review.off_topic ? 'danger' : 'success'"
                      >
                        {{ chapter.review.off_topic ? '是' : '否' }}
                      </el-tag>
                    </el-descriptions-item>
                    <el-descriptions-item label="评语">
                      {{ chapter.review.summary }}
                    </el-descriptions-item>
                  </el-descriptions>

                  <div
                    v-if="chapter.review.issues && chapter.review.issues.length"
                    class="review-issues"
                  >
                    <h4>主要问题</h4>
                    <ul>
                      <li v-for="(issue, idx) in chapter.review.issues" :key="idx">
                        {{ issue }}
                      </li>
                    </ul>
                  </div>
                </div>

                <el-empty
                  v-else
                  description="暂无评审信息"
                />
              </div>
            </el-card>

            <el-card class="card fixed-card notes-card">
              <div class="card-header-row">
                <h3 class="card-title">编辑提示</h3>
                <span class="card-note">保持节奏</span>
              </div>
              <div class="card-scroll">
                <ul class="notes-list">
                  <li>每章只推进一个关键冲突</li>
                  <li>确保人物动机与情绪一致</li>
                  <li>埋下一处可回收的伏笔</li>
                </ul>
              </div>
            </el-card>
          </aside>
        </div>
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { useAuthStore } from '@/store/auth'
import {
  getStatus,
  getNovelList,
  exportNovel
} from '@/api/novel'

/* ---------- state ---------- */
const novels = ref([])
const novelId = ref('')
const topic = ref('')
const chapter = ref(null)
const loading = ref(false)
const exporting = ref(false)

const activeStep = ref(0)
const auth = useAuthStore()

/* ---------- 初始化小说 ---------- */
const initNovelHandler = async () => {
  if (!novelId.value) {
    ElMessage.error('请输入小说 ID')
    return
  }

  loading.value = true
  activeStep.value = 0
  chapter.value = null

  try {
    await streamChapter('/novel/init_stream', {
      novel_id: novelId.value,
      topic: topic.value
    }, { init: true })
    ElMessage.success('小说初始化完成')
  } catch (e) {
    ElMessage.error(e.message || '初始化失败')
  } finally {
    loading.value = false
  }
}


/* ---------- 写下一章（非流式但有过程感） ---------- */
const nextChapterHandler = async () => {
  if (!novelId.value) {
    ElMessage.error('请选择小说')
    return
  }

  chapter.value = null
  activeStep.value = 0
  loading.value = true

  try {
    await streamChapter('/novel/next_chapter_stream', {
      novel_id: novelId.value
    })
    ElMessage.success('章节生成完成')
  } catch (e) {
    ElMessage.error(e.message || '生成失败')
  } finally {
    loading.value = false
  }
}

/* ---------- 导出小说 ---------- */
const exportNovelHandler = async () => {
  if (!novelId.value) {
    ElMessage.error('请选择小说')
    return
  }

  exporting.value = true
  try {
    const blob = await exportNovel(novelId.value)
    const safeId = String(novelId.value).replace(/[^\w.-]+/g, '_')
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = `novel_${safeId}.txt`
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    window.URL.revokeObjectURL(url)
    ElMessage.success('导出成功')
  } catch (e) {
    ElMessage.error('导出失败')
  } finally {
    exporting.value = false
  }
}

/* ---------- 小说列表 ---------- */
const fetchNovels = async () => {
  console.log('🔥 fetchNovels called')

  const res = await getNovelList()
  console.log('📦 novel list res:', res)
  console.log(res.data)
  const list = res.data || []
  console.log('📦 novel list:', list)

  novels.value = await Promise.all(
    list.map(async (n) => {
      const status = await getStatus(n.novel_id)
      return {
        novel_id: n.novel_id,
        topic: n.topic,
        current_chapter: status.data.current_chapter
      }
    })
  )
}

/* ---------- 选中小说 ---------- */
const selectNovel = (row) => {
  novelId.value = row.novel_id
  topic.value = row.topic
  chapter.value = null
}

const stepMap = {
  world_building_task: 1,
  character_design_task: 2,
  story_planning_task: 3,
  plot_analysis_task: 3,
  writing_task: 4,
  chapter_rewrite_task: 4
}

const updateProgress = (task) => {
  if (task && stepMap[task]) {
    activeStep.value = stepMap[task]
  }
}

const streamChapter = async (endpoint, payload, options = {}) => {
  const targetChapter = options.init
    ? 1
    : (chapter.value?.chapter_number ? chapter.value.chapter_number + 1 : 1)

  const headers = { 'Content-Type': 'application/json' }
  if (auth.token) {
    headers.Authorization = `Bearer ${auth.token}`
  }

  const response = await fetch(`http://127.0.0.1:8000${endpoint}`, {
    method: 'POST',
    headers,
    body: JSON.stringify(payload)
  })

  if (!response.ok) {
    throw new Error('流式请求失败')
  }

  if (!response.body) {
    throw new Error('当前环境不支持流式读取')
  }

  const reader = response.body.getReader()
  const decoder = new TextDecoder('utf-8')
  let buffer = ''

  const initDraft = () => {
    chapter.value = {
      novel_id: novelId.value,
      chapter_number: targetChapter,
      title: '',
      content: '',
      review: null,
      rewrite: null
    }
  }

  const handleMessage = (msg) => {
    if (msg.type === 'progress') {
      updateProgress(msg.task)
    }

    if (msg.type === 'draft_start') {
      initDraft()
    }

    if (msg.type === 'rewrite_start') {
      if (!chapter.value) initDraft()
      chapter.value.content = ''
      chapter.value.rewrite = {
        reasons: ['触发重写'],
        applied: true
      }
    }

    if (msg.type === 'title') {
      if (!chapter.value) initDraft()
      chapter.value.title = msg.data || ''
    }

    if (msg.type === 'content_delta') {
      if (!chapter.value) initDraft()
      chapter.value.content += msg.data || ''
    }

    if (msg.type === 'final') {
      if (msg.data) {
        if (!chapter.value) initDraft()
        chapter.value = { ...chapter.value, ...msg.data }
      }
      activeStep.value = 4
    }

    if (msg.type === 'error') {
      throw new Error(msg.message || '流式输出失败')
    }
  }

  while (true) {
    const { done, value } = await reader.read()
    if (done) break
    buffer += decoder.decode(value, { stream: true })
    const lines = buffer.split('\n')
    buffer = lines.pop() || ''

    for (const line of lines) {
      if (!line.trim()) continue
      const msg = JSON.parse(line)
      handleMessage(msg)
    }
  }

  buffer += decoder.decode()
  if (buffer.trim()) {
    const tailLines = buffer.split('\n')
    for (const line of tailLines) {
      if (!line.trim()) continue
      const msg = JSON.parse(line)
      handleMessage(msg)
    }
  }

  await fetchNovels()
}



/* ---------- lifecycle ---------- */
onMounted(fetchNovels)
</script>

<style scoped>
.layout {
  height: 100vh;
  --panel-sm: clamp(180px, 22vh, 240px);
  --panel-md: clamp(220px, 28vh, 320px);
  --panel-lg: clamp(280px, 36vh, 420px);
  background:
    radial-gradient(circle at 15% 10%, rgba(255, 255, 255, 0.65), transparent 50%),
    radial-gradient(circle at 90% 20%, rgba(255, 255, 255, 0.5), transparent 45%),
    #f7f1e6;
}

.header {
  height: 88px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  padding: 0 24px;
  background:
    linear-gradient(120deg, rgba(139, 47, 47, 0.18), transparent 45%),
    #f3e8d6;
  border-bottom: 1px solid rgba(63, 46, 35, 0.15);
  box-shadow: 0 6px 16px rgba(48, 36, 28, 0.12);
}

.header-left {
  display: flex;
  align-items: center;
  gap: 14px;
}

.brand-mark {
  width: 46px;
  height: 46px;
  border-radius: 12px;
  display: grid;
  place-items: center;
  background: #2f2622;
  color: #f7efe3;
  font-weight: 700;
  letter-spacing: 1px;
}

.brand-title {
  font-size: 20px;
  font-weight: 700;
  color: #2f2622;
}

.brand-sub {
  font-size: 12px;
  letter-spacing: 2px;
  text-transform: uppercase;
  color: rgba(47, 38, 34, 0.6);
}

.header-center {
  display: flex;
  gap: 12px;
  align-items: center;
}

.meta-card {
  background: rgba(255, 255, 255, 0.75);
  border: 1px solid rgba(63, 46, 35, 0.15);
  border-radius: 12px;
  padding: 8px 14px;
  min-width: 130px;
  display: grid;
  gap: 2px;
}

.meta-label {
  font-size: 11px;
  text-transform: uppercase;
  letter-spacing: 2px;
  color: rgba(47, 38, 34, 0.5);
}

.meta-value {
  font-size: 14px;
  font-weight: 600;
  color: #2f2622;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}

.header-btn {
  border-radius: 10px;
  background: #2f2622;
  color: #f7efe3;
  border: none;
}

.aside {
  background: rgba(250, 245, 236, 0.9);
  padding: 20px 18px;
  border-right: 1px solid rgba(96, 74, 58, 0.15);
  display: flex;
  flex-direction: column;
  gap: 18px;
}

.main {
  padding: 24px;
  background: transparent;
}

.card {
  margin-bottom: 0;
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-soft);
  border: 1px solid rgba(93, 72, 56, 0.16);
}

.fixed-card {
  display: flex;
  flex-direction: column;
  height: var(--panel-md);
}

.settings-card,
.actions-card,
.notes-card {
  height: var(--panel-sm);
}

.process-card,
.library-card {
  height: var(--panel-md);
}

.review-card {
  height: var(--panel-lg);
}

.card-compact {
  margin-bottom: 0;
}

.aside-card {
  background: rgba(255, 250, 242, 0.9);
}

.card-header-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
  gap: 12px;
}

.card-title {
  margin: 0;
  font-size: 16px;
  font-weight: 700;
  color: #2f2622;
}

.card-note {
  font-size: 12px;
  color: rgba(47, 38, 34, 0.5);
}

.card-badge {
  font-size: 12px;
  font-weight: 600;
  padding: 4px 10px;
  border-radius: 999px;
  background: rgba(139, 47, 47, 0.12);
  color: #7b2b2b;
}

.aside-form :deep(.el-form-item__label) {
  color: #2f2622;
  font-weight: 600;
}

.aside-bottom {
  margin-top: auto;
}

.aside :deep(.el-input__wrapper) {
  border-radius: 12px;
  background: #f7efe3;
  box-shadow: inset 0 0 0 1px rgba(85, 64, 51, 0.12);
}

.aside :deep(.el-button) {
  border-radius: 12px;
  font-weight: 600;
}

.aside-actions {
  display: grid;
  gap: 10px;
}

.workspace {
  display: grid;
  grid-template-columns: minmax(0, 1.6fr) minmax(0, 0.9fr);
  gap: 22px;
  align-items: start;
}

.workspace-primary,
.workspace-secondary {
  display: grid;
  gap: 20px;
  align-content: start;
}

.fixed-card :deep(.el-card__body) {
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
}

.card-scroll {
  flex: 1;
  min-height: 0;
  overflow: auto;
}

.library-card .card-scroll {
  overflow: hidden;
}

.process-card :deep(.el-steps) {
  padding-top: 6px;
}

.chapter-card {
  background:
    linear-gradient(0deg, rgba(255, 255, 255, 0.7), rgba(255, 255, 255, 0.7)),
    repeating-linear-gradient(
      0deg,
      rgba(74, 59, 47, 0.05) 0px,
      rgba(74, 59, 47, 0.05) 1px,
      transparent 1px,
      transparent 28px
    );
}

.chapter-body {
  padding-top: 4px;
}

.chapter-title {
  font-size: 22px;
  margin: 6px 0 8px;
  color: #2f2622;
}

.rewrite-note {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  background: rgba(139, 47, 47, 0.1);
  color: #7a2b2b;
  padding: 6px 10px;
  border-radius: 999px;
  font-size: 12px;
  margin-bottom: 8px;
}

.rewrite-label {
  font-weight: 700;
}

.content {
  white-space: pre-wrap;
  line-height: 1.9;
  margin-top: 10px;
  font-size: 16px;
  color: #2f2622;
}

.review-card {
  position: relative;
  overflow: hidden;
}

.review-card::before {
  content: "";
  position: absolute;
  inset: 0;
  border-left: 4px solid rgba(139, 47, 47, 0.45);
  pointer-events: none;
}

.review-issues {
  margin-top: 12px;
}

.review-issues ul {
  padding-left: 18px;
  margin: 6px 0 0;
}

.notes-card {
  background: rgba(255, 250, 242, 0.9);
}

.notes-list {
  margin: 0;
  padding-left: 18px;
  color: rgba(47, 38, 34, 0.75);
  display: grid;
  gap: 6px;
}

:deep(.el-card__body) {
  padding: 18px 20px;
}

:deep(.el-table) {
  --el-table-header-bg-color: rgba(139, 47, 47, 0.08);
  --el-table-row-hover-bg-color: rgba(139, 47, 47, 0.06);
}

:deep(.el-step__title) {
  font-weight: 600;
  color: rgba(47, 38, 34, 0.8);
}

:deep(.el-step__description) {
  color: rgba(47, 38, 34, 0.6);
}

@media (max-width: 1100px) {
  .workspace {
    grid-template-columns: 1fr;
  }

  .fixed-card {
    height: auto;
  }

  .card-scroll {
    overflow: visible;
  }
}

@media (max-width: 900px) {
  .header {
    height: auto;
    flex-direction: column;
    align-items: flex-start;
    padding: 18px 20px;
  }

  .header-actions {
    width: 100%;
    flex-wrap: wrap;
  }

  .layout > :deep(.el-container) {
    flex-direction: column;
  }

  .aside {
    width: 100%;
  }
}

@media (max-width: 600px) {
  .main {
    padding: 16px;
  }

  .meta-card {
    min-width: 110px;
  }
}
</style>
