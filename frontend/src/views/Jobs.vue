<template>
  <div class="jobs-container">
    <div class="header">
      <h2>岗位JD管理</h2>
      <el-button type="primary" @click="showDialog = true">
        <el-icon><Plus /></el-icon>
        新增岗位
      </el-button>
    </div>

    <el-table :data="jobs" style="width: 100%" v-loading="loading">
      <el-table-column prop="title" label="岗位标题" min-width="200" />
      <el-table-column prop="description" label="岗位描述" min-width="300" :show-overflow-tooltip="true" />
      <el-table-column prop="created_at" label="创建时间" width="180" />
      <el-table-column label="操作" width="120">
        <template #default="scope">
          <el-button size="small" type="danger" @click="deleteJob(scope.row.id)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <!-- 新增岗位对话框 -->
    <el-dialog v-model="showDialog" title="新增岗位" width="600px">
      <el-form :model="form" label-width="80px">
        <el-form-item label="岗位标题">
          <el-input v-model="form.title" placeholder="请输入岗位标题" />
        </el-form-item>
        <el-form-item label="岗位描述">
          <el-input 
            v-model="form.description" 
            type="textarea" 
            :rows="6" 
            placeholder="请输入详细的岗位描述和要求" 
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showDialog = false">取消</el-button>
        <el-button type="primary" @click="createJob" :loading="saving">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script>
import { Plus } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import api from '../api'

export default {
  name: 'Jobs',
  components: { Plus },
  data() {
    return {
      jobs: [],
      loading: false,
      showDialog: false,
      saving: false,
      form: {
        title: '',
        description: ''
      }
    }
  },
  mounted() {
    this.loadJobs()
  },
  methods: {
    async loadJobs() {
      this.loading = true
      try {
        const response = await api.getJobs()
        this.jobs = response.data
      } catch (error) {
        ElMessage.error('加载岗位列表失败')
      } finally {
        this.loading = false
      }
    },
    async createJob() {
      if (!this.form.title || !this.form.description) {
        ElMessage.warning('请填写完整的岗位信息')
        return
      }

      this.saving = true
      try {
        await api.createJob(this.form)
        ElMessage.success('岗位创建成功')
        this.showDialog = false
        this.form = { title: '', description: '' }
        this.loadJobs()
      } catch (error) {
        ElMessage.error('创建岗位失败')
      } finally {
        this.saving = false
      }
    },
    async deleteJob(id) {
      try {
        await ElMessageBox.confirm('确定要删除这个岗位吗？', '提示', {
          type: 'warning'
        })
        
        await api.deleteJob(id)
        ElMessage.success('删除成功')
        this.loadJobs()
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
.jobs-container {
  padding: 20px;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}
</style>