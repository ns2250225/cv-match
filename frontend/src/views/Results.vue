<template>
  <div class="results-container">
    <div class="header">
      <h2>匹配结果历史</h2>
      <div class="header-actions">
        <el-button 
          type="danger" 
          :disabled="results.length === 0" 
          @click="clearAllResults"
          :loading="clearing"
        >
          <el-icon><Delete /></el-icon>
          一键清除所有结果
        </el-button>
      </div>
    </div>

    <el-card>
      <div class="table-header">
        <h3>匹配结果列表</h3>
        <div class="table-controls">
          <div class="filter-controls">
            <el-input
              v-model="jobTitleFilter"
              placeholder="请输入岗位标题进行筛选"
              prefix-icon="Search"
              clearable
              @clear="clearFilter"
              @input="filterResults"
              style="width: 250px; margin-right: 10px;"
            />
          </div>
          <div class="sort-controls">
            <el-button 
              type="primary" 
              size="small" 
              @click="sortByScore"
              :icon="Sort"
            >
              按匹配度降序排列
            </el-button>
          </div>
        </div>
      </div>
      <el-table :data="filteredResults" style="width: 100%" v-loading="loading">
        <el-table-column prop="job_title" label="岗位标题" min-width="200" />
        <el-table-column prop="resume_filename" label="简历文件" min-width="200">
          <template #default="scope">
            <el-link type="primary" @click="viewPdf(scope.row)">{{ scope.row.resume_filename }}</el-link>
          </template>
        </el-table-column>
        <el-table-column prop="match_score" label="匹配度" width="120">
          <template #default="scope">
            <el-progress 
              :percentage="scope.row.match_score" 
              :show-text="false"
              :color="getScoreColor(scope.row.match_score)"
            />
            <span style="margin-left: 10px;">{{ scope.row.match_score }}%</span>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="匹配时间" width="180" />
        <el-table-column label="操作" width="200">
          <template #default="scope">
            <el-button size="small" @click="viewDetail(scope.row)">查看详情</el-button>
            <el-button size="small" type="danger" @click="deleteResult(scope.row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 详情对话框 -->
    <el-dialog v-model="showDetail" title="匹配详情" width="900px">
      <div v-if="currentResult">
        <div class="detail-header">
          <h3>{{ currentResult.job_title }} - {{ currentResult.resume_filename }}</h3>
          <p>匹配时间: {{ currentResult.created_at }}</p>
        </div>
        
        <!-- 总分展示 -->
        <div class="total-score-section">
          <div class="total-score-card">
            <div class="score-display">
              <div class="score-circle">
                <span class="score-value">{{ currentResult.analysis_data.total_score || currentResult.match_score }}</span>
                <span class="score-label">分</span>
              </div>
              <div class="score-info">
                <h4>总体匹配度</h4>
                <p class="assessment-text">{{ currentResult.analysis_data.overall_assessment || '总体评估' }}</p>
              </div>
            </div>
          </div>
        </div>
        
        <!-- 多维度分析 -->
        <div class="dimension-analysis" v-if="currentResult.analysis_data.dimension_scores">
          <h4>多维度分析</h4>
          <div class="dimension-cards">
            <div 
              v-for="(scoreInfo, dimension) in currentResult.analysis_data.dimension_scores" 
              :key="dimension"
              class="dimension-card"
              :class="getDimensionCardClass(scoreInfo.score)"
            >
              <div class="dimension-header">
                <span class="dimension-name">{{ dimension }}</span>
                <el-tag :type="getScoreTagType(scoreInfo.score)" size="small">
                  {{ scoreInfo.score }}分
                </el-tag>
              </div>
              <div class="dimension-content">
                <p class="dimension-reason"><strong>原因:</strong> {{ scoreInfo.reason }}</p>
                <p class="dimension-suggestion"><strong>建议:</strong> {{ scoreInfo.suggestion }}</p>
              </div>
            </div>
          </div>
        </div>
        
        <!-- 改进建议 -->
        <div class="improvement-suggestions" v-if="currentResult.analysis_data.improvement_suggestions">
          <h4>改进建议</h4>
          <div class="suggestion-list">
            <div 
              v-for="(suggestion, index) in currentResult.analysis_data.improvement_suggestions" 
              :key="index"
              class="suggestion-item"
            >
              <el-icon><InfoFilled /></el-icon>
              <span>{{ suggestion }}</span>
            </div>
          </div>
        </div>
      </div>
      
      <template #footer>
        <el-button @click="showDetail = false">关闭</el-button>
      </template>
    </el-dialog>

    <!-- PDF预览对话框 -->
    <el-dialog v-model="showPdfDialog" :title="`预览简历: ${currentPdfTitle}`" width="80%" top="5vh">
      <div class="pdf-container">
        <iframe 
          v-if="currentPdfUrl"
          :src="currentPdfUrl" 
          width="100%" 
          height="600px"
          frameborder="0"
        ></iframe>
        <div v-else class="pdf-loading">
          <el-loading :loading="true"></el-loading>
          <p>正在加载PDF文件...</p>
        </div>
      </div>
      
      <template #footer>
        <el-button @click="showPdfDialog = false">关闭</el-button>
        <el-button type="primary" @click="downloadPdf">下载简历</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script>
import { ElMessage, ElMessageBox } from 'element-plus'
import { Delete, InfoFilled, Sort, Search } from '@element-plus/icons-vue'
import api from '../api'

export default {
  name: 'Results',
  components: {
    Delete,
    InfoFilled,
    Sort,
    Search
  },
  data() {
    return {
      results: [],
      filteredResults: [],
      loading: false,
      clearing: false,
      showDetail: false,
      currentResult: null,
      jobTitleFilter: '',
      showPdfDialog: false,
      currentPdfUrl: '',
      currentPdfTitle: ''
    }
  },
  mounted() {
    this.loadResults()
  },
  methods: {
    async loadResults() {
      this.loading = true
      try {
        const response = await api.getMatchResults()
        this.results = response.data
        this.filteredResults = [...this.results]
      } catch (error) {
        ElMessage.error('加载匹配结果失败')
      } finally {
        this.loading = false
      }
    },
    
    async deleteResult(result) {
      try {
        await ElMessageBox.confirm(
          `确定要删除"${result.job_title} - ${result.resume_filename}"的匹配结果吗？`,
          '确认删除',
          {
            confirmButtonText: '确定',
            cancelButtonText: '取消',
            type: 'warning'
          }
        )
        
        await api.deleteMatchResult(result.id)
        ElMessage.success('删除成功')
        this.loadResults() // 重新加载列表
      } catch (error) {
        if (error !== 'cancel') {
          ElMessage.error('删除失败')
        }
      }
    },
    
    async clearAllResults() {
      try {
        await ElMessageBox.confirm(
          '确定要清除所有匹配结果吗？此操作不可撤销。',
          '确认清除',
          {
            confirmButtonText: '确定',
            cancelButtonText: '取消',
            type: 'warning'
          }
        )
        
        this.clearing = true
        await api.clearAllMatchResults()
        ElMessage.success('所有匹配结果已清除')
        this.loadResults() // 重新加载列表
      } catch (error) {
        if (error !== 'cancel') {
          ElMessage.error('清除失败')
        }
      } finally {
        this.clearing = false
      }
    },
    
    viewDetail(result) {
      this.currentResult = result
      this.showDetail = true
    },
    
    getScoreColor(score) {
      if (score >= 80) return '#67C23A'
      if (score >= 60) return '#E6A23C'
      return '#F56C6C'
    },
    
    getScoreTagType(score) {
      if (score >= 80) return 'success'
      if (score >= 60) return 'warning'
      return 'danger'
    },
    
    getDimensionCardClass(score) {
      if (score >= 80) return 'dimension-card-high'
      if (score >= 60) return 'dimension-card-medium'
      return 'dimension-card-low'
    },
    
    // 按照匹配度降序排列
    sortByScore() {
      this.filteredResults.sort((a, b) => {
        return b.match_score - a.match_score
      })
      
      ElMessage.success('已按匹配度降序排列')
    },
    
    // 按岗位标题筛选
    filterResults() {
      if (!this.jobTitleFilter.trim()) {
        this.filteredResults = [...this.results]
        return
      }
      
      const filterText = this.jobTitleFilter.toLowerCase()
      this.filteredResults = this.results.filter(result => 
        result.job_title.toLowerCase().includes(filterText)
      )
    },
    
    // 清除筛选
    clearFilter() {
      this.jobTitleFilter = ''
      this.filteredResults = [...this.results]
    },
    
    // 查看PDF文件
    viewPdf(result) {
      this.currentPdfTitle = result.resume_filename
      // 构建PDF文件的完整URL
      this.currentPdfUrl = `http://localhost:5000/api/resume/pdf/${result.resume_filename}`
      this.showPdfDialog = true
    },
    
    // 下载PDF文件
    downloadPdf() {
      if (this.currentPdfUrl) {
        // 创建一个隐藏的a标签来触发下载
        const link = document.createElement('a')
        link.href = this.currentPdfUrl
        link.download = this.currentPdfTitle
        document.body.appendChild(link)
        link.click()
        document.body.removeChild(link)
      }
    }
  }
}
</script>

<style scoped>
.results-container {
  padding: 20px;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.header h2 {
  margin: 0;
}

.header-actions {
  display: flex;
  gap: 10px;
}

.table-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 15px;
}

.table-header h3 {
  margin: 0;
  color: #333;
}

.table-controls {
  display: flex;
  align-items: center;
  gap: 15px;
}

.filter-controls {
  display: flex;
  align-items: center;
}

.sort-controls {
  display: flex;
  gap: 10px;
}

.detail-header {
  margin-bottom: 20px;
  padding-bottom: 15px;
  border-bottom: 1px solid #eee;
}

.detail-header h3 {
  margin: 0 0 10px 0;
  color: #333;
}

.detail-header p {
  margin: 0;
  color: #666;
  font-size: 14px;
}

/* 总分展示样式 */
.total-score-section {
  margin-bottom: 25px;
}

.total-score-card {
  background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
  border-radius: 8px;
  padding: 20px;
}

.score-display {
  display: flex;
  align-items: center;
  gap: 20px;
}

.score-circle {
  position: relative;
  width: 80px;
  height: 80px;
  background: #fff;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.score-value {
  font-size: 24px;
  font-weight: bold;
  color: #409EFF;
}

.score-label {
  font-size: 14px;
  color: #666;
  margin-left: 2px;
}

.score-info h4 {
  margin: 0 0 10px 0;
  color: #409EFF;
  font-size: 18px;
}

.assessment-text {
  margin: 0;
  color: #666;
  line-height: 1.6;
  font-size: 15px;
  font-weight: 500;
}

/* 多维度分析样式 */
.dimension-analysis {
  margin-bottom: 25px;
}

.dimension-analysis h4 {
  margin-bottom: 15px;
  color: #333;
  font-size: 16px;
  border-left: 4px solid #409EFF;
  padding-left: 10px;
}

.dimension-cards {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 15px;
}

.dimension-card {
  background: #fff;
  border: 1px solid #e0e0e0;
  border-radius: 6px;
  padding: 15px;
  transition: all 0.3s ease;
}

.dimension-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.dimension-card.dimension-card-high {
  border-left: 4px solid #67C23A;
}

.dimension-card.dimension-card-medium {
  border-left: 4px solid #E6A23C;
}

.dimension-card.dimension-card-low {
  border-left: 4px solid #F56C6C;
}

.dimension-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
}

.dimension-name {
  font-weight: 600;
  color: #333;
  font-size: 14px;
}

.dimension-content {
  font-size: 13px;
  line-height: 1.5;
}

.dimension-reason,
.dimension-suggestion {
  margin-bottom: 8px;
  color: #666;
}

.dimension-reason strong,
.dimension-suggestion strong {
  color: #333;
  margin-right: 5px;
}

/* 改进建议样式 */
.improvement-suggestions {
  margin-bottom: 20px;
}

.improvement-suggestions h4 {
  margin-bottom: 15px;
  color: #333;
  font-size: 16px;
  border-left: 4px solid #E6A23C;
  padding-left: 10px;
}

.suggestion-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.suggestion-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px;
  background: #f8f9fa;
  border-radius: 4px;
  border-left: 3px solid #E6A23C;
}

.suggestion-item .el-icon {
  color: #E6A23C;
  font-size: 16px;
}

.suggestion-item span {
  color: #666;
  font-size: 14px;
}

/* PDF预览对话框样式 */
.pdf-container {
  width: 100%;
  height: 600px;
  display: flex;
  justify-content: center;
  align-items: center;
  background-color: #f5f5f5;
  border-radius: 4px;
  overflow: hidden;
}

.pdf-loading {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  color: #666;
}

.pdf-loading p {
  margin-top: 15px;
  font-size: 14px;
}
</style>