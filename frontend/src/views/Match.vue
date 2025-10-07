<template>
  <div class="match-container">
    <div class="header">
      <h2>简历匹配打分</h2>
    </div>

    <el-card>
      <template #header>
        <span>选择岗位和简历进行匹配分析</span>
      </template>

      <el-form :model="form" label-width="100px">
        <el-form-item label="选择岗位">
          <el-select v-model="form.job_id" placeholder="请选择岗位" style="width: 100%">
            <el-option
              v-for="job in jobs"
              :key="job.id"
              :label="job.title"
              :value="job.id"
            />
          </el-select>
        </el-form-item>

        <el-form-item label="选择简历">
          <el-select 
            v-model="form.resume_ids" 
            placeholder="请选择简历（可多选）" 
            style="width: 100%"
            multiple
            filterable
          >
            <el-option
              v-for="resume in resumes"
              :key="resume.id"
              :label="resume.filename"
              :value="resume.id"
            />
          </el-select>
        </el-form-item>

        <el-form-item>
          <el-button 
            type="primary" 
            @click="startMatch" 
            :disabled="!form.job_id || form.resume_ids.length === 0"
            :loading="matching"
          >
            开始批量匹配分析
          </el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 进度显示 -->
    <el-card v-if="matching" class="progress-card">
      <template #header>
        <span>匹配进度</span>
      </template>
      
      <div class="progress-content">
        <div class="progress-info">
          <el-progress 
            :percentage="Math.round((progress.current / progress.total) * 100)" 
            :status="progress.status === 'error' ? 'exception' : 'success'"
            :stroke-width="8"
          />
          <div class="progress-details">
            <p>状态: {{ getStatusText(progress.status) }}</p>
            <p>进度: {{ progress.current }}/{{ progress.total }}</p>
            <p v-if="progress.currentFilename">当前处理: {{ progress.currentFilename }}</p>
            <p v-if="progress.status === 'error'">错误: {{ progress.error }}</p>
          </div>
        </div>
        
        <!-- 已完成的匹配结果预览 -->
        <div v-if="progress.results.length > 0" class="completed-results">
          <h4>已完成匹配:</h4>
          <div class="result-preview">
            <el-tag 
              v-for="result in progress.results" 
              :key="result.resume_id"
              :type="result.success ? 'success' : 'danger'"
              class="result-tag"
            >
              {{ result.resume_filename }}: {{ result.success ? '成功' : '失败' }}
            </el-tag>
          </div>
        </div>
      </div>
    </el-card>

    <!-- 匹配结果 -->
    <div v-if="results.length > 0" class="results-container">
      <h3>批量匹配结果 ({{ results.filter(r => r.success).length }}/{{ results.length }} 成功)</h3>
      
      <el-card v-for="(result, index) in results" :key="index" class="result-card" style="margin-bottom: 20px;">
        <template #header>
          <div class="result-header">
            <span>{{ result.resume_filename }}</span>
            <el-tag :type="result.success ? 'success' : 'danger'">
              {{ result.success ? '匹配成功' : '匹配失败' }}
            </el-tag>
          </div>
        </template>

        <!-- 成功结果 -->
        <div v-if="result.success">
          <!-- 总分展示 -->
          <div class="total-score">
            <el-progress 
              type="dashboard" 
              :percentage="result.data.total_score" 
              :color="getScoreColor(result.data.total_score)"
              :width="120"
            />
            <div class="score-info">
              <h4>匹配度总分: {{ result.data.total_score }}%</h4>
              <p class="assessment-text">{{ result.data.overall_assessment }}</p>
            </div>
          </div>

          <!-- 各维度得分 -->
          <div class="dimension-scores" v-if="result.data.dimension_scores">
            <h5>各维度匹配分析</h5>
            
            <!-- 维度得分卡片 -->
            <div class="dimension-cards">
              <el-card 
                v-for="(dimension, key) in result.data.dimension_scores" 
                :key="key"
                class="dimension-card"
                :class="getDimensionCardClass(dimension.score)"
              >
                <template #header>
                  <div class="dimension-header">
                    <span class="dimension-name">{{ key }}</span>
                    <el-tag :type="getScoreTagType(dimension.score)" size="large">
                      {{ dimension.score }}%
                    </el-tag>
                  </div>
                </template>
                <div class="dimension-content">
                  <div class="dimension-reason">
                    <strong>打分原因:</strong> {{ dimension.reason }}
                  </div>
                  <div class="dimension-suggestion">
                    <strong>修改建议:</strong> {{ dimension.suggestion }}
                  </div>
                </div>
              </el-card>
            </div>

            <!-- 维度得分表格（详细视图） -->
            <el-collapse v-model="activeCollapse" class="dimension-table-collapse">
              <el-collapse-item title="详细维度分析表格" name="table">
                <el-table :data="getDimensionData(result.data.dimension_scores)" style="width: 100%" size="small" border>
                  <el-table-column prop="dimension" label="维度" width="150" align="center" />
                  <el-table-column prop="score" label="得分" width="100" align="center">
                    <template #default="scope">
                      <el-progress 
                        :percentage="scope.row.score" 
                        :show-text="false"
                        :color="getScoreColor(scope.row.score)"
                        style="width: 80px; margin: 0 auto;"
                      />
                      <span style="margin-left: 10px;">{{ scope.row.score }}%</span>
                    </template>
                  </el-table-column>
                  <el-table-column prop="reason" label="打分原因" min-width="200" :show-overflow-tooltip="true" />
                  <el-table-column prop="suggestion" label="修改建议" min-width="200" :show-overflow-tooltip="true" />
                </el-table>
              </el-collapse-item>
            </el-collapse>
          </div>

          <!-- 改进建议 -->
          <div class="improvement-suggestions" v-if="result.data.improvement_suggestions && result.data.improvement_suggestions.length > 0">
            <h5>整体改进建议</h5>
            <div class="suggestion-cards">
              <el-card 
                v-for="(suggestion, idx) in result.data.improvement_suggestions" 
                :key="idx"
                class="suggestion-card"
                shadow="hover"
              >
                <div class="suggestion-content">
                  <el-icon><InfoFilled /></el-icon>
                  <span>{{ suggestion }}</span>
                </div>
              </el-card>
            </div>
          </div>
        </div>

        <!-- 失败结果 -->
        <div v-else class="error-result">
          <el-alert
            :title="`匹配失败: ${result.error}`"
            type="error"
            :closable="false"
          />
        </div>
      </el-card>
    </div>
  </div>
</template>

<script>
import { ElMessage } from 'element-plus'
import { InfoFilled } from '@element-plus/icons-vue'
import api from '../api'

export default {
  name: 'Match',
  components: {
    InfoFilled
  },
  data() {
    return {
      jobs: [],
      resumes: [],
      matching: false,
      results: [], // 改为数组存储多个结果
      activeCollapse: ['table'], // 默认展开详细表格
      form: {
        job_id: '',
        resume_ids: [] // 改为数组存储多个简历ID
      },
      currentTaskId: null,
      progress: {
        current: 0,
        total: 0,
        status: '', // starting, processing, completed, error
        currentFilename: '',
        results: []
      },
      progressInterval: null
    }
  },
  mounted() {
    this.loadData()
  },
  methods: {
    async loadData() {
      try {
        const [jobsRes, resumesRes] = await Promise.all([
          api.getJobs(),
          api.getResumes()
        ])
        this.jobs = jobsRes.data
        this.resumes = resumesRes.data
      } catch (error) {
        ElMessage.error('加载数据失败')
      }
    },
    async startMatch() {
      this.matching = true
      this.results = []
      
      try {
        // 启动批量匹配任务
        const response = await api.batchMatchResumes({
          job_id: this.form.job_id,
          resume_ids: this.form.resume_ids
        })
        
        // 获取任务ID
        this.currentTaskId = response.data.task_id
        this.progress.total = response.data.total
        this.progress.status = 'starting'
        
        // 开始轮询进度
        this.startProgressPolling()
        
      } catch (error) {
        console.error('启动批量匹配错误:', error)
        ElMessage.error(`启动批量匹配失败: ${error.message || '未知错误'}`)
        this.matching = false
      }
    },
    
    startProgressPolling() {
      // 清除之前的轮询
      if (this.progressInterval) {
        clearInterval(this.progressInterval)
      }
      
      // 开始新的轮询
      this.progressInterval = setInterval(async () => {
        try {
          const response = await api.getMatchProgress(this.currentTaskId)
          this.progress = response.data
          
          // 更新显示结果
          this.results = this.progress.results.map(result => {
            if (result.success) {
              return {
                success: true,
                resume_filename: result.resume_filename || `简历ID: ${result.resume_id}`,
                data: result.data
              }
            } else {
              return {
                success: false,
                resume_filename: result.resume_filename || `简历ID: ${result.resume_id}`,
                error: result.error || '匹配失败'
              }
            }
          })
          
          // 检查任务状态
          if (this.progress.status === 'completed' || this.progress.status === 'error') {
            this.stopProgressPolling()
            this.matching = false
            
            if (this.progress.status === 'completed') {
              const successCount = this.results.filter(r => r.success).length
              ElMessage.success(`批量匹配完成，成功 ${successCount}/${this.progress.total} 份简历`)
            } else {
              ElMessage.error(`批量匹配失败: ${this.progress.error || '未知错误'}`)
            }
          }
        } catch (error) {
          console.error('获取进度错误:', error)
          // 如果获取进度失败，可能是任务已完成或不存在
          this.stopProgressPolling()
          this.matching = false
          ElMessage.error('获取匹配进度失败，请刷新页面查看结果')
        }
      }, 2000) // 每2秒轮询一次
    },
    
    stopProgressPolling() {
      if (this.progressInterval) {
        clearInterval(this.progressInterval)
        this.progressInterval = null
      }
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
    getDimensionData(dimensionScores) {
      return Object.keys(dimensionScores).map(dimension => ({
        dimension: dimension,
        score: dimensionScores[dimension].score,
        reason: dimensionScores[dimension].reason,
        suggestion: dimensionScores[dimension].suggestion
      }))
    },
    getDimensionCardClass(score) {
      if (score >= 80) return 'dimension-card-high'
      if (score >= 60) return 'dimension-card-medium'
      return 'dimension-card-low'
    },
    
    getStatusText(status) {
      const statusMap = {
        'starting': '任务启动中',
        'processing': '处理中',
        'completed': '已完成',
        'error': '错误'
      }
      return statusMap[status] || status
    }
  },
  
  beforeUnmount() {
    // 组件销毁时清理轮询
    this.stopProgressPolling()
  }
}
</script>

<style scoped>
.match-container {
  padding: 20px;
}

.header {
  margin-bottom: 20px;
}

/* 进度显示样式 */
.progress-card {
  margin-top: 20px;
}

.progress-content {
  padding: 0 10px;
}

.progress-info {
  margin-bottom: 20px;
}

.progress-details {
  margin-top: 15px;
  padding: 15px;
  background-color: #f8f9fa;
  border-radius: 6px;
  border-left: 4px solid #409EFF;
}

.progress-details p {
  margin: 5px 0;
  color: #666;
  font-size: 14px;
}

.completed-results {
  margin-top: 20px;
  padding-top: 20px;
  border-top: 1px solid #e0e0e0;
}

.completed-results h4 {
  margin-bottom: 10px;
  color: #333;
  font-size: 16px;
}

.result-preview {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.result-tag {
  margin: 2px;
}

.results-container {
    margin-top: 20px;
    
    h3 {
      margin-bottom: 15px;
      color: #333;
    }
    
    .result-card {
      .result-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
      }
      
      .total-score {
        display: flex;
        align-items: center;
        gap: 20px;
        margin-bottom: 30px;
        padding: 20px;
        background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
        border-radius: 8px;
        
        .score-info {
          flex: 1;
          
          h4 {
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
        }
      }
      
      .dimension-scores {
        margin-bottom: 25px;
        
        h5 {
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
          margin-bottom: 20px;
          
          .dimension-card {
            transition: all 0.3s ease;
            border: 1px solid #e0e0e0;
            
            &:hover {
              transform: translateY(-2px);
              box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
            }
            
            &.dimension-card-high {
              border-left: 4px solid #67C23A;
            }
            
            &.dimension-card-medium {
              border-left: 4px solid #E6A23C;
            }
            
            &.dimension-card-low {
              border-left: 4px solid #F56C6C;
            }
            
            .dimension-header {
              display: flex;
              justify-content: space-between;
              align-items: center;
              
              .dimension-name {
                font-weight: 600;
                color: #333;
                font-size: 14px;
              }
            }
            
            .dimension-content {
              .dimension-reason,
              .dimension-suggestion {
                margin-bottom: 10px;
                line-height: 1.5;
                font-size: 13px;
                color: #666;
                
                strong {
                  color: #333;
                  margin-right: 5px;
                }
              }
            }
          }
        }
        
        .dimension-table-collapse {
          margin-top: 15px;
        }
      }
      
      .improvement-suggestions {
        h5 {
          margin-bottom: 15px;
          color: #333;
          font-size: 16px;
          border-left: 4px solid #E6A23C;
          padding-left: 10px;
        }
        
        .suggestion-cards {
          display: grid;
          grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
          gap: 12px;
          
          .suggestion-card {
            border: 1px solid #f0f0f0;
            
            .suggestion-content {
              display: flex;
              align-items: center;
              gap: 8px;
              color: #666;
              font-size: 14px;
              line-height: 1.5;
              
              .el-icon {
                color: #E6A23C;
                font-size: 16px;
              }
            }
          }
        }
      }
      
      .error-result {
        text-align: center;
        padding: 30px 0;
        
        .el-alert {
          max-width: 500px;
          margin: 0 auto;
        }
      }
    }
  }
</style>