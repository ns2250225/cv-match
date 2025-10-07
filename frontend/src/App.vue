<template>
  <div id="app">
    <el-container style="height: 100vh;">
      <el-header style="background-color: #409EFF; color: white; display: flex; align-items: center;">
        <h1 style="margin: 0;">简历匹配打分系统</h1>
      </el-header>
      
      <el-container>
        <el-aside width="200px" style="background-color: #f5f7fa;">
          <el-menu
            :default-active="$route.path"
            router
            style="border: none;"
          >
            <el-menu-item index="/jobs">
              <el-icon><Document /></el-icon>
              <span>岗位JD管理</span>
            </el-menu-item>
            <el-menu-item index="/resumes">
              <el-icon><Upload /></el-icon>
              <span>简历上传</span>
            </el-menu-item>
            <el-menu-item index="/match">
              <el-icon><DataAnalysis /></el-icon>
              <span>匹配打分</span>
            </el-menu-item>
            <el-menu-item index="/results">
              <el-icon><Histogram /></el-icon>
              <span>匹配结果</span>
            </el-menu-item>
          </el-menu>
        </el-aside>
        
        <el-main style="padding: 20px;">
          <router-view />
        </el-main>
      </el-container>
    </el-container>
  </div>
</template>

<script>
import { Document, Upload, DataAnalysis, Histogram } from '@element-plus/icons-vue'

export default {
  name: 'App',
  components: {
    Document,
    Upload,
    DataAnalysis,
    Histogram
  }
}
</script>

<style>
#app {
  font-family: 'Helvetica Neue', Helvetica, 'PingFang SC', 'Hiragino Sans GB', 'Microsoft YaHei', sans-serif;
}

.el-header {
  padding: 0 20px;
}

.el-menu-item {
  height: 56px;
  line-height: 56px;
}
</style>