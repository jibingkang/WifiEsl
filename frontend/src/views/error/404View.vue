<template>
  <div class="error-page">
    <div class="error-content">
      <div class="error-code">404</div>
      <h2 class="error-title">页面不存在</h2>
      <p class="error-desc">抱歉，您访问的页面已丢失或从未存在过。</p>
      <div class="error-actions">
        <el-button type="primary" size="large" @click="$router.push('/dashboard')">
          返回首页
        </el-button>
        <el-button size="large" @click="$router.back()">返回上页</el-button>
      </div>
    </div>

    <!-- 装饰 -->
    <div class="error-bg">
      <span class="bg-circle c1" />
      <span class="bg-circle c2" />
    </div>
  </div>
</template>

<script setup lang="ts">
// 404 Not Found page
</script>

<style lang="scss" scoped>
.error-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
  overflow: hidden;
  background: var(--el-bg-color-page);
}

.error-content {
  text-align: center;
  position: relative;
  z-index: 10;
}

.error-code {
  font-size: 120px;
  font-weight: 900;
  line-height: 1;
  background: linear-gradient(135deg, #6366f1, #8b5cf6, #a78bfa);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  letter-spacing: -6px;
}

.error-title {
  font-size: 24px;
  font-weight: 700;
  color: var(--el-text-color-primary);
  margin: 16px 0 8px;
}

.error-desc {
  font-size: 15px;
  color: var(--el-text-color-secondary);
  margin: 0 0 32px;
}

.error-actions { display: flex; gap: 12px; justify-content: center; }

.error-bg .bg-circle {
  position: absolute;
  border-radius: 50%;
  opacity: 0.06;
}
.c1 { width: 400px; height: 400px; top: -150px; right: -100px; }
.c2 { width: 300px; height: 300px; bottom: -100px; left: -80px; }

html.dark {
  .error-bg .bg-circle { opacity: 0.04; }
}
</style>
