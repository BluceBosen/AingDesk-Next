<template>
  <div v-if="visible" class="modal-overlay" @click.self="close">
    <div class="modal-panel">
      <div class="modal-header">
        <h3>上传文档</h3>
        <button class="close-btn" @click="close">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <line x1="18" y1="6" x2="6" y2="18"/>
            <line x1="6" y1="6" x2="18" y2="18"/>
          </svg>
        </button>
      </div>
      <div class="modal-body">
        <!-- 文件选择 -->
        <div class="form-group">
          <label>选择文件 <span class="required">*</span></label>
          <div class="file-picker">
            <input ref="fileInput" type="file" hidden @change="onFileChange" />
            <button class="btn-secondary" @click="fileInput?.click()">选择文件</button>
            <span class="file-name">{{ selectedFile?.name || '未选择文件' }}</span>
          </div>
          <div class="form-tip">单个文件最大 20MB</div>
        </div>

        <!-- 同文件处理 -->
        <div class="form-group">
          <label>同名文件处理</label>
          <div class="radio-group">
            <label class="radio-item">
              <input v-model="overSameFile" type="radio" :value="null" />
              <span>覆盖</span>
            </label>
            <label class="radio-item">
              <input v-model="overSameFile" type="radio" :value="1" />
              <span>不覆盖</span>
            </label>
            <label class="radio-item">
              <input v-model="overSameFile" type="radio" :value="2" />
              <span>重命名</span>
            </label>
          </div>
        </div>

        <!-- 分片配置 -->
        <div class="divider" />
        <div class="form-group">
          <label>分片设置</label>
          <div class="chunk-row">
            <span class="chunk-label">分块大小</span>
            <input v-model.number="localChunkForm.chunkSize" type="number" min="100" max="8000" class="input" />
          </div>
          <div class="chunk-row">
            <span class="chunk-label">重叠大小</span>
            <input v-model.number="localChunkForm.overlapSize" type="number" min="0" max="2000" class="input" />
          </div>
        </div>

        <div class="form-group">
          <label class="checkbox-label">
            <input v-model="localChunkForm.customSeparators" type="checkbox" />
            <span>自定义分隔符</span>
          </label>
          <div v-if="localChunkForm.customSeparators" class="separators-input">
            <input v-model="separatorsText" class="input" placeholder="输入分隔符，用逗号分隔，例如：\n\n,\n, " />
          </div>
        </div>
      </div>
      <div class="modal-footer">
        <button class="btn-secondary" @click="close">取消</button>
        <button class="btn-primary" :disabled="!selectedFile || uploading" @click="submit">
          <span v-if="uploading" class="spin-wrap">
            <svg class="spin" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M21 12a9 9 0 11-6.219-8.56"/>
            </svg>
            上传中...
          </span>
          <span v-else>确认上传</span>
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'

const props = defineProps<{
  visible: boolean
  ragName: string
  chunkForm: {
    chunkSize: number
    overlapSize: number
    separators: string[]
    customSeparators: boolean
  }
}>()

const emit = defineEmits<{
  (e: 'update:visible', val: boolean): void
  (e: 'submit', payload: { file: File; overSameFile: number | null; chunkForm: typeof localChunkForm.value }): void
}>()

const fileInput = ref<HTMLInputElement | null>(null)
const selectedFile = ref<File | null>(null)
const uploading = ref(false)
const overSameFile = ref<number | null>(null)
const localChunkForm = ref({ ...props.chunkForm })
const separatorsText = ref(props.chunkForm.separators.join(','))

watch(
  () => props.visible,
  (val) => {
    if (val) {
      selectedFile.value = null
      overSameFile.value = null
      localChunkForm.value = { ...props.chunkForm }
      separatorsText.value = props.chunkForm.separators.join(',')
      if (fileInput.value) fileInput.value.value = ''
    }
  }
)

watch(
  () => props.chunkForm,
  (val) => {
    localChunkForm.value = { ...val }
    separatorsText.value = val.separators.join(',')
  },
  { deep: true }
)

const onFileChange = (e: Event) => {
  const target = e.target as HTMLInputElement
  const file = target.files?.[0]
  if (file) {
    selectedFile.value = file
  }
}

const close = () => {
  emit('update:visible', false)
}

const submit = () => {
  if (!selectedFile.value) return
  // 解析自定义分隔符
  if (localChunkForm.value.customSeparators) {
    const parts = separatorsText.value.split(',').map((s) => s.replace(/\\n/g, '\n').trim())
    localChunkForm.value.separators = parts.filter(Boolean).length ? parts.filter(Boolean) : ['\n\n', '\n', ' ']
  } else {
    localChunkForm.value.separators = ['\n\n', '\n', ' ']
  }
  uploading.value = true
  emit('submit', { file: selectedFile.value, overSameFile: overSameFile.value, chunkForm: localChunkForm.value })
  setTimeout(() => {
    uploading.value = false
    close()
  }, 300)
}
</script>

<style scoped lang="scss">
.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.4);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 100;
}

.modal-panel {
  width: 460px;
  background: var(--bg-primary);
  border-radius: var(--radius-lg);
  border: 1px solid var(--border-color);
  box-shadow: var(--shadow-lg);
  overflow: hidden;
}

.modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 20px;
  border-bottom: 1px solid var(--border-color);

  h3 {
    font-size: 16px;
    font-weight: 600;
    color: var(--text-primary);
  }
}

.close-btn {
  width: 28px;
  height: 28px;
  border-radius: var(--radius-sm);
  border: none;
  background: transparent;
  color: var(--text-secondary);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;

  &:hover {
    background: var(--bg-hover);
  }
}

.modal-body {
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 6px;

  label {
    font-size: 13px;
    font-weight: 500;
    color: var(--text-secondary);
  }
}

.required {
  color: var(--danger-color, #ef4444);
}

.file-picker {
  display: flex;
  align-items: center;
  gap: 12px;
}

.file-name {
  font-size: 13px;
  color: var(--text-secondary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  flex: 1;
}

.form-tip {
  font-size: 12px;
  color: var(--text-tertiary);
}

.radio-group {
  display: flex;
  gap: 16px;
}

.radio-item {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 13px;
  color: var(--text-primary);
  cursor: pointer;
}

.divider {
  height: 1px;
  background: var(--border-color);
}

.chunk-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;

  .chunk-label {
    font-size: 13px;
    color: var(--text-secondary);
  }

  .input {
    width: 120px;
  }
}

.checkbox-label {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  cursor: pointer;
  font-size: 13px;
  color: var(--text-primary);
}

.separators-input {
  margin-top: 4px;
}

.input {
  padding: 8px 12px;
  border-radius: var(--radius-md);
  border: 1px solid var(--border-color);
  background: var(--bg-primary);
  color: var(--text-primary);
  font-size: 14px;
  outline: none;

  &:focus {
    border-color: var(--accent-color);
  }
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  padding: 14px 20px;
  border-top: 1px solid var(--border-color);
}

.btn-secondary {
  padding: 8px 16px;
  border-radius: var(--radius-md);
  border: 1px solid var(--border-color);
  background: var(--bg-primary);
  color: var(--text-primary);
  font-size: 13px;
  cursor: pointer;

  &:hover {
    background: var(--bg-hover);
  }
}

.btn-primary {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  padding: 8px 16px;
  border-radius: var(--radius-md);
  border: none;
  background: var(--accent-color);
  color: #fff;
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;

  &:hover {
    opacity: 0.9;
  }

  &:disabled {
    opacity: 0.6;
    cursor: not-allowed;
  }
}

.spin-wrap {
  display: inline-flex;
  align-items: center;
  gap: 4px;
}

.spin {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}
</style>
