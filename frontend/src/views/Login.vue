<template>
  <div class="login-page">
    <div class="login-shell">
      <section class="login-cover">
        <div class="cover-inner">
          <div class="cover-brand">
            <div class="cover-mark">NW</div>
            <div>
              <p class="cover-tag">编辑部创作台</p>
              <h1 class="cover-title">AI写作平台</h1>
              <p class="cover-subtitle">
                把灵感写在纸上，把流程交给 AI。
              </p>
            </div>
          </div>

          <div class="cover-quote">
            “结构、节奏、情绪，都有迹可循。”
          </div>

          <ul class="cover-list">
            <li>世界观与人物自动编排</li>
            <li>章节评审与重写记录</li>
            <li>一键导出完整稿件</li>
          </ul>

          <div class="cover-footer">
            Editorial Desk · 让创作有章法
          </div>
        </div>
      </section>

      <section class="login-panel">
        <div class="login-card">
          <div class="card-header">
            <p class="card-kicker">编辑部账号</p>
            <h2 class="title">欢迎回来</h2>
            <p class="subtitle">输入账号进入创作工作台</p>
          </div>

          <el-input
            v-model="username"
            placeholder="用户名"
            size="large"
            class="input"
          />

          <el-input
            v-model="password"
            type="password"
            placeholder="密码"
            size="large"
            show-password
            class="input"
          />

          <el-button
            type="primary"
            size="large"
            class="btn"
            @click="handleSubmit"
          >
            {{ isRegister ? '注册' : '进入工作台' }}
          </el-button>

          <div class="switch">
            <span v-if="!isRegister">
              还没有账号？
              <a @click="isRegister = true">去注册</a>
            </span>
            <span v-else>
              已有账号？
              <a @click="isRegister = false">去登录</a>
            </span>
          </div>
        </div>
      </section>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { login, register } from '@/api/auth'
import { useAuthStore } from '@/store/auth'

const username = ref('')
const password = ref('')
const isRegister = ref(false)

const router = useRouter()
const auth = useAuthStore()

const handleSubmit = async () => {
  if (!username.value || !password.value) {
    ElMessage.error('请输入用户名和密码')
    return
  }

  try {
    if (isRegister.value) {
      await register(username.value, password.value)
      ElMessage.success('注册成功，请登录')
      isRegister.value = false
      return
    }

    const res = await login(username.value, password.value)
    const token = res.data.token

    if (!token) {
      throw new Error('token 不存在')
    }

    auth.setToken(token)
    ElMessage.success('登录成功')
    router.push('/writer')

  } catch (e) {
    ElMessage.error(isRegister.value ? '注册失败' : '登录失败')
  }
}
</script>

<style scoped>
.login-page {
  min-height: 100vh;
  display: flex;
  align-items: stretch;
  justify-content: center;
  padding: 32px;
  position: relative;
}

.login-page::before {
  content: "";
  position: absolute;
  inset: 0;
  background:
    radial-gradient(circle at 80% 10%, rgba(255, 255, 255, 0.6), transparent 50%),
    radial-gradient(circle at 10% 80%, rgba(255, 255, 255, 0.45), transparent 55%);
  pointer-events: none;
}

.login-shell {
  width: min(1100px, 100%);
  margin: auto;
  display: grid;
  grid-template-columns: 1.15fr 0.85fr;
  background: rgba(247, 241, 230, 0.9);
  border: 1px solid rgba(66, 52, 44, 0.15);
  border-radius: 22px;
  overflow: hidden;
  box-shadow: var(--shadow-strong);
  position: relative;
  z-index: 1;
}

.login-cover {
  background:
    linear-gradient(140deg, rgba(139, 47, 47, 0.16), transparent 55%),
    linear-gradient(20deg, rgba(63, 95, 74, 0.18), transparent 60%),
    #f3e9d8;
  position: relative;
}

.login-cover::after {
  content: "";
  position: absolute;
  inset: 0;
  background-image:
    linear-gradient(transparent 94%, rgba(65, 52, 45, 0.06)),
    repeating-linear-gradient(
      0deg,
      rgba(65, 52, 45, 0.04),
      rgba(65, 52, 45, 0.04) 1px,
      transparent 1px,
      transparent 26px
    );
  opacity: 0.6;
  pointer-events: none;
}

.cover-inner {
  position: relative;
  padding: 48px 52px;
  height: 100%;
  display: flex;
  flex-direction: column;
  gap: 18px;
  z-index: 1;
}

.cover-brand {
  display: flex;
  gap: 16px;
  align-items: center;
}

.cover-mark {
  width: 52px;
  height: 52px;
  border-radius: 14px;
  display: grid;
  place-items: center;
  font-weight: 700;
  letter-spacing: 1px;
  background: #2f2622;
  color: #f6efe5;
  box-shadow: inset 0 0 0 2px rgba(255, 255, 255, 0.15);
}

.cover-tag {
  text-transform: uppercase;
  letter-spacing: 3px;
  font-size: 12px;
  color: rgba(47, 38, 34, 0.6);
  margin: 0 0 6px;
}

.cover-title {
  font-size: 30px;
  margin: 0;
  color: #2f2622;
}

.cover-subtitle {
  margin: 8px 0 0;
  color: rgba(47, 38, 34, 0.7);
  max-width: 280px;
}

.cover-quote {
  margin-top: 20px;
  padding: 18px 20px;
  border-left: 3px solid rgba(139, 47, 47, 0.6);
  background: rgba(255, 255, 255, 0.4);
  color: #3b2f2a;
  font-size: 15px;
}

.cover-list {
  list-style: none;
  margin: 6px 0 0;
  padding: 0;
  display: grid;
  gap: 10px;
  color: rgba(47, 38, 34, 0.8);
}

.cover-list li {
  padding-left: 18px;
  position: relative;
}

.cover-list li::before {
  content: "•";
  position: absolute;
  left: 0;
  color: var(--accent);
}

.cover-footer {
  margin-top: auto;
  font-size: 12px;
  text-transform: uppercase;
  letter-spacing: 2px;
  color: rgba(47, 38, 34, 0.5);
}

.login-panel {
  background: #fbf6ee;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 40px;
}

.login-card {
  width: min(360px, 100%);
  padding: 30px 28px;
  background: #fffaf2;
  border-radius: var(--radius-lg);
  border: 1px solid rgba(68, 54, 44, 0.15);
  box-shadow: var(--shadow-soft);
  text-align: left;
  animation: rise 0.4s ease;
}

.card-header {
  margin-bottom: 18px;
}

.card-kicker {
  font-size: 12px;
  letter-spacing: 2px;
  text-transform: uppercase;
  color: rgba(47, 38, 34, 0.55);
  margin: 0 0 8px;
}

.title {
  margin: 0 0 4px;
  font-size: 24px;
  font-weight: 700;
  color: #2f2622;
}

.subtitle {
  margin: 0 0 14px;
  color: rgba(47, 38, 34, 0.65);
  font-size: 14px;
}

.input {
  margin-bottom: 14px;
}

.btn {
  width: 100%;
  margin-top: 8px;
  font-weight: 700;
  letter-spacing: 1px;
  background: linear-gradient(120deg, #8b2f2f, #6b1f1f);
  border: none;
  box-shadow: 0 8px 18px rgba(139, 47, 47, 0.3);
}

.btn:hover {
  transform: translateY(-1px);
}

.switch {
  margin-top: 16px;
  font-size: 13px;
  color: rgba(47, 38, 34, 0.7);
}

.switch a {
  color: var(--accent);
  cursor: pointer;
  margin-left: 4px;
}

:deep(.el-input__wrapper) {
  border-radius: 12px;
  background: #f7efe3;
  box-shadow: inset 0 0 0 1px rgba(85, 64, 51, 0.12);
}

:deep(.el-input__inner) {
  color: #2f2622;
}

:deep(.el-button) {
  border-radius: 12px;
  transition: transform 0.2s ease, box-shadow 0.2s ease;
}

@keyframes rise {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@media (max-width: 960px) {
  .login-shell {
    grid-template-columns: 1fr;
  }

  .login-cover {
    min-height: 260px;
  }

  .cover-inner {
    padding: 36px 32px;
  }
}

@media (max-width: 560px) {
  .login-page {
    padding: 18px;
  }

  .login-panel {
    padding: 26px 18px;
  }
}
</style>
