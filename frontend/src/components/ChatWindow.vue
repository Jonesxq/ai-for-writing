<template>
  <div class="writer-page">
    <!-- 左侧小说信息栏 -->
    <aside class="sidebar">
      <h3>{{ novelTitle || '未命名小说' }}</h3>

      <el-descriptions column="1" size="small" border>
        <el-descriptions-item label="小说 ID">
          {{ novelId }}
        </el-descriptions-item>
        <el-descriptions-item label="当前章节">
          第 {{ currentChapter }} 章
        </el-descriptions-item>
        <el-descriptions-item label="状态">
          <el-tag type="success">可写作</el-tag>
        </el-descriptions-item>
      </el-descriptions>

      <!-- 小说主题输入（首次写作生效） -->
      <el-input 
        v-model="novelTitle" 
        placeholder="请输入小说主题（首次写作必填）" 
        style="margin: 12px 0;"
      />

      <!-- 统一的写作按钮 -->
      <el-button
        class="main-btn"
        type="primary"
        :loading="loading"
        @click="handleWrite"
      >
        开始/继续写作（第 {{ currentChapter + 1 }} 章）
      </el-button>
    </aside>

    <!-- 右侧聊天式生成面板 -->
    <section class="chat-panel" ref="chatPanel">
      <!-- 聊天消息列表 -->
      <div
        v-for="(msg, index) in messages"
        :key="index"
        class="chat-msg"
        :class="msg.role"
      >
        <div class="bubble">
          <div v-if="msg.title" class="title">{{ msg.title }}</div>
          <pre>{{ msg.content }}</pre>
        </div>
      </div>

      <!-- 加载中提示 -->
      <div v-if="loading" class="chat-msg system">
        <div class="bubble">AI 正在创作中，请稍候~</div>
      </div>
    </section>
  </div>
</template>

<script setup>
import { ref, onMounted, nextTick } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage, ElTag } from 'element-plus'

const route = useRoute()

// 小说基础信息
const novelId = Number(route.query.novel_id)
const novelTitle = ref('') // 小说主题（绑定输入框）
const currentChapter = ref(0)
const loading = ref(false)

// 聊天消息列表
const messages = ref([])
const chatPanel = ref(null)

// 滚动到最新消息
function scrollToBottom() {
  nextTick(() => {
    if (chatPanel.value) {
      chatPanel.value.scrollTop = chatPanel.value.scrollHeight
    }
  })
}

// 加载小说当前状态
async function loadNovelStatus() {
  try {
    const res = await fetch(`/api/novel/status/${novelId}`)
    if (!res.ok) throw new Error('获取小说状态失败')
    const data = await res.json()
    currentChapter.value = data.current_chapter
    novelTitle.value = data.topic || novelTitle.value
  } catch (e) {
    ElMessage.error('加载小说信息失败')
  }
}

// 生成章节（模拟流式/真实流式均可）
async function generateChapter() {
  loading.value = true
  const targetChapter = currentChapter.value + 1

  // 1. 推送「准备生成」的系统消息
  messages.value.push({
    role: 'system',
    content: `即将生成第 ${targetChapter} 章~`
  })
  scrollToBottom()

  // 2. 预创建章节消息（后续逐步更新内容）
  const chapterMsgIndex = messages.value.length
  messages.value.push({
    role: 'assistant',
    title: `第 ${targetChapter} 章（创作中）`,
    content: ''
  })
  scrollToBottom()

  try {
    // --- 方式1：后端支持流式响应（推荐）---
    const response = await fetch('/api/novel/next_chapter', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        novel_id: novelId,
        topic: novelTitle.value // 首次写作传主题
      })
    })

    if (!response.ok) throw new Error('创作请求失败')
    const reader = response.body.getReader()
    const decoder = new TextDecoder('utf-8')
    let chapterTitle = ''
    let fullContent = ''

    // 逐块读取流式内容
    while (true) {
      const { done, value } = await reader.read()
      if (done) break

      // 后端需返回格式：{ type: "title/content", data: "内容" }
      const chunk = JSON.parse(decoder.decode(value))
      if (chunk.type === 'title') {
        chapterTitle = chunk.data
        messages.value[chapterMsgIndex].title = `第 ${targetChapter} 章：${chapterTitle}`
      } else if (chunk.type === 'content') {
        fullContent += chunk.data
        messages.value[chapterMsgIndex].content = fullContent
      }
      scrollToBottom()
    }

    // --- 方式2：后端不支持流式（前端模拟逐步显示）---
    // const res = await fetch('/api/novel/next_chapter', {
    //   method: 'POST',
    //   headers: { 'Content-Type': 'application/json' },
    //   body: JSON.stringify({ novel_id: novelId, topic: novelTitle.value })
    // })
    // const { title, content } = await res.json()
    // // 模拟标题延迟显示
    // messages.value[chapterMsgIndex].title = `第 ${targetChapter} 章：${title}`
    // scrollToBottom()
    // await new Promise(resolve => setTimeout(resolve, 600))
    // // 模拟内容分块显示
    // const contentChunks = content.split(/(?<=[。！？；])/g) // 按标点分割
    // for (const chunk of contentChunks) {
    //   messages.value[chapterMsgIndex].content += chunk
    //   scrollToBottom()
    //   await new Promise(resolve => setTimeout(resolve, 200))
    // }

    // 更新章节号
    currentChapter.value = targetChapter
    novelTitle.value = chapterTitle || novelTitle.value

  } catch (e) {
    messages.value[chapterMsgIndex].content = `创作失败：${e.message}`
    throw e
  } finally {
    loading.value = false
    scrollToBottom()
  }
}

// 写作按钮点击事件
async function handleWrite() {
  // 首次写作需校验主题
  if (!novelTitle.value && currentChapter.value === 0) {
    ElMessage.warning('请先输入小说主题~')
    return
  }
  try {
    await generateChapter()
  } catch (e) {
    ElMessage.error('操作失败，请稍后重试')
    loading.value = false
  }
}

// 页面挂载后加载小说状态
onMounted(async () => {
  if (!novelId) {
    ElMessage.error('缺少小说ID参数')
    return
  }
  await loadNovelStatus()
})
</script>

<style scoped>
.writer-page {
  display: flex;
  height: calc(100vh - 60px);
  background: #f5f7fa;
}

.sidebar {
  width: 280px;
  padding: 16px;
  background: #ffffff;
  border-right: 1px solid #e5e7eb;
}

.sidebar h3 {
  margin-bottom: 12px;
}

.main-btn {
  margin-top: 16px;
  width: 100%;
}

.chat-panel {
  flex: 1;
  padding: 24px;
  overflow-y: auto;
}

.chat-msg {
  display: flex;
  margin-bottom: 16px;
}

.chat-msg.system {
  justify-content: center;
}

.chat-msg.assistant {
  justify-content: flex-start;
}

.chat-msg .bubble {
  max-width: 75%;
  padding: 12px 16px;
  border-radius: 8px;
  background: #ffffff;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.05);
  white-space: pre-wrap;
  line-height: 1.6;
}

.chat-msg.system .bubble {
  background: #eef2ff;
  color: #334155;
  font-size: 0.9em;
}

.title {
  font-weight: 600;
  margin-bottom: 8px;
  color: #1e40af;
}
</style>