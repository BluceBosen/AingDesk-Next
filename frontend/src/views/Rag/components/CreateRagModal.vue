<template>
  <div v-if="visible" class="modal-overlay" @click.self="close">
    <div class="modal-panel">
      <div class="modal-header">
        <h3>{{ editMode ? '编辑知识库' : '新建知识库' }}</h3>
        <button class="close-btn" @click="close">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <line x1="18" y1="6" x2="6" y2="18"/>
            <line x1="6" y1="6" x2="18" y2="18"/>
          </svg>
        </button>
      </div>
      <div class="modal-body">
        <div class="form-group">
          <label>名称 <span class="required">*</span></label>
          <input v-model="localForm.ragName" class="input" placeholder="请输入知识库名称" :disabled="editMode" />
        </div>
        <div class="form-group">
          <label>描述 <span class="required">*</span></label>
          <textarea v-model="localForm.ragDesc" class="textarea" rows="3" placeholder="请输入知识库描述" />
        </div>
        <div class="form-group">
          <label>嵌入模型 <span class="required">*</span></label>
          <select v-model="localForm.embeddingModel" class="select" :disabled="editMode" @change="onModelChange">
            <option value="" disabled>请选择嵌入模型</option>
            <option v-for="m in models" :key="m.model + m.supplierName" :value="m.model">
              {{ m.title }} ({{ m.supplierName }})
            </option>
          </select>
          <div v-if="!models.length" class="form-tip">暂无可用的嵌入模型，请先安装本地模型或配置第三方模型</div>
        </div>
        <div class="form-group">
          <label>最大召回数量 (topK)</label>
          <div class="slider-row">
            <input v-model.number="localForm.maxRecall" type="range" min="1" max="20" step="1" class="slider" />
            <span class="slider-value">{{ localForm.maxRecall }}</span>
          </div>
        </div>
      </div>
      <div class="modal-footer">
        <button class="btn-secondary" @click="close">取消</button>
        <button class="btn-primary" :disabled="submitting" @click="submit">{{ editMode ? '保存' : '创建' }}</button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import type { EmbeddingModelItem } from '@/types'

const props = defineProps<{
  visible: boolean
  editMode: boolean
  form: {
    ragName: string
    ragDesc: string
    embeddingModel: string
    supplierName: string
    maxRecall: number
  }
  models: EmbeddingModelItem[]
}>()

const emit = defineEmits<{
  (e: 'update:visible', val: boolean): void
  (e: 'submit', form: typeof localForm.value): void
}>()

const localForm = ref({ ...props.form })
const submitting = ref(false)

watch(
  () => props.visible,
  (val) => {
    if (val) {
      localForm.value = { ...props.form }
      if (!props.editMode) {
        const bge = props.models.find((m) => m.model?.includes('bge-m3'))
        const target = bge || props.models[0]
        if (target) {
          localForm.value.embeddingModel = target.model
          localForm.value.supplierName = target.supplierName
        }
      }
    }
  }
)

watch(
  () => props.form,
  (val) => {
    localForm.value = { ...val }
  },
  { deep: true }
)

const close = () => {
  emit('update:visible', false)
}

const onModelChange = () => {
  const model = props.models.find((m) => m.model === localForm.value.embeddingModel)
  localForm.value.supplierName = model?.supplierName || 'ollama'
}

const submit = () => {
  submitting.value = true
  emit('submit', localForm.value)
  setTimeout(() => {
    submitting.value = false
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

.input,
.textarea,
.select {
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

  &:disabled {
    background: var(--bg-disabled, var(--bg-secondary));
    color: var(--text-tertiary);
    cursor: not-allowed;
  }
}

.textarea {
  resize: vertical;
}

.form-tip {
  font-size: 12px;
  color: var(--warning-color, #f59e0b);
}

.slider-row {
  display: flex;
  align-items: center;
  gap: 12px;
}

.slider {
  flex: 1;
}

.slider-value {
  min-width: 24px;
  text-align: center;
  font-size: 13px;
  color: var(--text-secondary);
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
</style>
