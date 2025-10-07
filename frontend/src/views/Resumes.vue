<template>
  <div class="resumes-container">
    <div class="header">
      <h2>简历上传</h2>
    </div>

    <!-- 上传区域 -->
    <el-card class="upload-card">
      <template #header>
        <span>上传PDF简历</span>
      </template>
      
      <el-upload
        class="upload-demo"
        drag
        action="/api/resumes"
        :on-success="handleSuccess"
        :on-error="handleError"
        :before-upload="beforeUpload"
        :multiple="true"
        :show-file-list="true"
      >
        <el-icon class="el-icon--upload"><upload-filled /></el-icon>
        <div class="el-upload__text">
          将PDF文件拖到此处，或<em>点击上传</em>
        </div>
        <template #tip>
          <div class="el-upload__tip">
            支持多选PDF文件，每个文件不超过10MB
          </div>
        </template>
      </el-upload>
    </el-card>

    <!-- 简历列表 -->
    <el-card class="list-card">
      <template #header>
        <span>已上传简历列表</span>
      </template>
      
      <el-table :data="resumes" style="width: 100%" v-loading="loading">
        <el-table-column prop="filename" label="文件名" min-width="200" />
        <el-table-column prop="content" label="内容预览" min-width="300" :show-overflow-tooltip="true" />
        <el-table-column prop="created_at" label="上传时间" width="180" />
        <el-table-column label="操作" width="120">
          <template #default="scope">
            <el-button size="small" type="danger" @click="deleteResume(scope.row.id)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script>
import { UploadFilled } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import api from '../api'

export default {
  name: 'Resumes',
  components: { UploadFilled },
  data() {
    return {
      resumes: [],
      loading: false
    }
  },
  mounted() {
    this.loadResumes()
  },
  methods: {
    async loadResumes() {
      this.loading = true
      try {
        const response = await api.getResumes()
        this.resumes = response.data
      } catch (error) {
        ElMessage.error('加载简历列表失败')
      } finally {
        this.loading = false
      }
    },
    beforeUpload(file) {
      const isPDF = file.type === 'application/pdf'
      const isLt10M = file.size / 1024 / 1024 < 10

      if (!isPDF) {
        ElMessage.error('只能上传PDF格式的文件!')
        return false
      }
      if (!isLt10M) {
        ElMessage.error('文件大小不能超过10MB!')
        return false
      }
      return true
    },
    handleSuccess(response) {
      if (response.data && response.data.results) {
        // 批量上传结果
        const successCount = response.data.results.filter(r => r.success).length
        const totalCount = response.data.results.length
        
        if (successCount === totalCount) {
          ElMessage.success(`所有 ${totalCount} 个文件上传成功`)
        } else {
          ElMessage.warning(`上传完成，成功 ${successCount}/${totalCount} 个文件`)
        }
      } else {
        // 单个文件上传（兼容旧版本）
        ElMessage.success('简历上传成功')
      }
      this.loadResumes()
    },
    handleError(error) {
      ElMessage.error('简历上传失败')
    },
    async deleteResume(id) {
      try {
        await ElMessageBox.confirm('确定要删除这个简历吗？', '提示', {
          type: 'warning'
        })
        
        await api.deleteResume(id)
        ElMessage.success('删除成功')
        this.loadResumes()
      } catch (error) {
        if (error !== 'cancel') {
          ElMessage.error('删除失败')
        }
      }
    }
  }
}
</script>

<style scoped>
.resumes-container {
  padding: 20px;
}

.header {
  margin-bottom: 20px;
}

.upload-card {
  margin-bottom: 20px;
}

.list-card {
  margin-top: 20px;
}

.upload-demo {
  width: 100%;
}
</style>