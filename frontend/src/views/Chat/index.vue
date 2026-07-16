<template>
  <div class="chat-page">
    <!-- Chat List Sidebar -->
    <aside class="chat-list">
      <div class="chat-list-header">
        <button class="btn-primary new-chat-btn" @click="store.makeNewChat">
          <svg width="16" height="26" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <line x1="12" y1="5" x2="12" y2="19"/>
            <line x1="5" y1="12" x2="19" y2="12"/>
          </svg>
          <span>新建对话</span>
        </button>
      </div>

      <div class="chat-list-body">
        <div
          v-for="chat in store.chatList"
          :key="chat.context_id"
          class="chat-item"
          :class="{ active: store.currentChatId === chat.context_id }"
          @click="store.selectChat(chat.context_id)"
        >
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="chat-item-icon">
            <path d="M21 15a2 2 0 01-2 2H7l-4 4V5a2 2 0 012-2h14a2 2 0 012 2z"/>
          </svg>
          <span class="chat-item-title">{{ chat.title }}</span>
          <div class="chat-item-actions">
            <button class="action-icon" @click.stop="startEditTitle(chat)" title="修改标题">
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M11 4H4a2 2 0 00-2 2v14a2 2 0 002 2h14a2 2 0 002-2v-7"/>
                <path d="M18.5 2.5a2.121 2.121 0 013 3L12 15l-4 1 1-4 9.5-9.5z"/>
              </svg>
            </button>
            <button class="action-icon" @click.stop="store.removeChat(chat.context_id)" title="删除">
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <line x1="18" y1="6" x2="6" y2="18"/>
                <line x1="6" y1="6" x2="18" y2="18"/>
              </svg>
            </button>
          </div>
        </div>
      </div>
    </aside>

    <!-- Chat Content -->
    <div class="chat-content">
      <!-- Header -->
      <div v-if="store.currentChatId || store.currentAgent" class="chat-top-bar">
        <div class="chat-top-left">
          <div v-if="store.currentAgent" class="agent-tag">
            <span class="agent-dot"></span>
            <span>智能体模式</span>
            <span class="agent-name">{{ store.currentAgent.agent_title }}</span>
            <button class="agent-clear" @click="store.currentAgent = null">×</button>
          </div>
        </div>
        <div class="chat-top-title">{{ store.currentChatTitle || '新对话' }}</div>
        <div class="chat-top-right"></div>
      </div>

      <!-- Welcome Screen -->
      <div v-if="!store.hasActiveChat || store.messages.length === 0" class="welcome-screen">
        <div v-if="store.currentAgent" class="agent-welcome">
          <div class="agent-welcome-icon">{{ store.currentAgent.icon || '🤖' }}</div>
          <div class="agent-welcome-title">{{ store.currentAgent.agent_title }}</div>
          <div class="agent-welcome-desc">{{ store.currentAgent.description || store.currentAgent.prompt }}</div>
        </div>
        <div v-else class="welcome-messages">
          <div class="welcome-msg">
            <div class="welcome-avatar">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M12 2a3 3 0 013 3v1h-6V5a3 3 0 013-3z"/>
                <path d="M19 13v-2a7 7 0 10-14 0v2"/>
                <path d="M12 11v10"/>
                <path d="M8 17h8"/>
              </svg>
            </div>
            <div class="welcome-bubble">
              <p>欢迎使用 AiSpace，支持知识库、模型 API、联网搜索、智能体等功能。</p>
            </div>
          </div>
        </div>

        <div class="quick-actions">
          <div class="quick-card" @click="store.makeNewChat">
            <div class="quick-icon">
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M21 15a2 2 0 01-2 2H7l-4 4V5a2 2 0 012-2h14a2 2 0 012 2z"/>
              </svg>
            </div>
            <div class="quick-text">开始新对话</div>
          </div>
          <div class="quick-card" @click="showModelSelect = true">
            <div class="quick-icon">
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <rect x="2" y="3" width="20" height="14" rx="2" ry="2"/>
                <line x1="8" y1="21" x2="16" y2="21"/>
                <line x1="12" y1="17" x2="12" y2="21"/>
              </svg>
            </div>
            <div class="quick-text">选择模型</div>
          </div>
          <div class="quick-card" @click="openFileKnowledgeModal">
            <div class="quick-icon">
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M4 19.5A2.5 2.5 0 016.5 17H20"/>
                <path d="M6.5 2H20v20H6.5A2.5 2.5 0 014 19.5v-15A2.5 2.5 0 016.5 2z"/>
              </svg>
            </div>
            <div class="quick-text">知识库</div>
          </div>
        </div>
      </div>

      <!-- Messages -->
      <template v-else>
        <div ref="messagesRef" class="messages-container">
          <div
            v-for="msg in store.messages"
            :key="msg.id"
            class="message-row"
            :class="msg.role"
          >
            <div class="message-avatar">
              <div v-if="msg.role === 'user'" class="avatar-user">我</div>
              <div v-else class="avatar-assistant">AI</div>
            </div>
            <div class="message-body">
              <!-- User files/images -->
              <div v-if="msg.role === 'user' && msg.files?.length" class="msg-files">
                <div v-for="(file, idx) in msg.files" :key="idx" class="msg-file-item">
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z"/>
                    <polyline points="14 2 14 8 20 8"/>
                  </svg>
                  <span>{{ file }}</span>
                </div>
              </div>
              <div v-if="msg.role === 'user' && msg.images?.length" class="msg-images">
                <img v-for="(img, idx) in msg.images" :key="idx" :src="img" class="msg-image-preview" />
              </div>

              <!-- Thinking block -->
              <div v-if="msg.thinking" class="thinking-block">
                <div class="thinking-header" @click="msg._thinkOpen = !msg._thinkOpen">
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" :class="{ rotate: msg._thinkOpen }">
                    <polyline points="6 9 12 15 18 9"/>
                  </svg>
                  <span>已深度思考</span>
                </div>
                <div v-show="msg._thinkOpen" class="thinking-content" v-html="renderMarkdown(msg.thinking)"></div>
              </div>

              <!-- Search results -->
              <div v-if="msg.search_result?.length" class="search-results">
                <div class="search-header">
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <circle cx="11" cy="11" r="8"/>
                    <line x1="21" y1="21" x2="16.65" y2="16.65"/>
                  </svg>
                  <span>联网搜索结果</span>
                </div>
                <div class="search-list">
                  <a v-for="(res, idx) in msg.search_result" :key="idx" :href="res.url" target="_blank" class="search-item">
                    <div class="search-title">{{ res.title }}</div>
                    <div class="search-snippet">{{ res.content }}</div>
                  </a>
                </div>
              </div>

              <!-- Tools results -->
              <div v-if="msg.tools_result?.length" class="tools-results">
                <div class="tools-header">
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M14.7 6.3a1 1 0 000 1.4l1.6 1.6a1 1 0 001.4 0l3.77-3.77a6 6 0 01-7.94 7.94l-6.91 6.91a2.12 2.12 0 01-3-3l6.91-6.91a6 6 0 017.94-7.94l-3.76 3.76z"/>
                  </svg>
                  <span>工具调用结果</span>
                </div>
                <div class="tools-list">
                  <div v-for="(tool, idx) in msg.tools_result" :key="idx" class="tool-item">
                    <pre>{{ JSON.stringify(tool, null, 2) }}</pre>
                  </div>
                </div>
              </div>

              <!-- Message content -->
              <div class="message-text" v-html="renderMarkdown(msg.content)"></div>

              <!-- Actions -->
              <div v-if="msg.role === 'assistant'" class="message-actions">
                <button class="action-btn" title="复制" @click="copyText(msg.content)">
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <rect x="9" y="9" width="13" height="13" rx="2" ry="2"/>
                    <path d="M5 15H4a2 2 0 01-2-2V4a2 2 0 012-2h9a2 2 0 012 2v1"/>
                  </svg>
                </button>
                <button class="action-btn" title="重新生成" @click="store.regenerate(msg.id)">
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <polyline points="23 4 23 10 17 10"/>
                    <path d="M20.49 15a9 9 0 11-2.12-9.36L23 10"/>
                  </svg>
                </button>
              </div>
            </div>
          </div>

          <!-- Loading indicator -->
          <div v-if="store.isLoading" class="message-row assistant">
            <div class="message-avatar">
              <div class="avatar-assistant">AI</div>
            </div>
            <div class="message-body">
              <div class="typing-indicator">
                <span></span>
                <span></span>
                <span></span>
              </div>
            </div>
          </div>
        </div>
      </template>

      <!-- Input Area -->
      <div class="input-wrapper" :class="{ 'has-mask': store.isLoading }">
        <!-- Uploaded files preview -->
        <div v-if="store.uploadedFiles.length || store.uploadedImages.length" class="uploaded-files-bar">
          <div v-for="(file, idx) in store.uploadedFiles" :key="'f'+idx" class="uploaded-chip">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z"/>
              <polyline points="14 2 14 8 20 8"/>
            </svg>
            <span class="chip-name">{{ file.name }}</span>
            <button class="chip-remove" @click="store.removeFile(idx)">
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <line x1="18" y1="6" x2="6" y2="18"/>
                <line x1="6" y1="6" x2="18" y2="18"/>
              </svg>
            </button>
          </div>
          <div v-for="(img, idx) in store.uploadedImages" :key="'i'+idx" class="uploaded-chip image-chip">
            <img :src="img" class="chip-thumb" />
            <button class="chip-remove" @click="store.removeImage(idx)">
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <line x1="18" y1="6" x2="6" y2="18"/>
                <line x1="6" y1="6" x2="18" y2="18"/>
              </svg>
            </button>
          </div>
        </div>

        <div class="input-area">
          <div class="input-box">
            <textarea
              ref="textareaRef"
              v-model="store.inputText"
              class="chat-textarea"
              rows="1"
              placeholder="输入消息..."
              @keydown.enter.prevent="handleEnter"
              @input="autoResize"
            ></textarea>
          </div>
          <div class="input-toolbar-bottom">
            <div class="toolbar-left">
              <button class="toolbar-btn" @click="store.makeNewChat" title="新的对话">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <line x1="12" y1="5" x2="12" y2="19"/>
                  <line x1="5" y1="12" x2="19" y2="12"/>
                </svg>
                <span>新的对话</span>
              </button>
              <button class="toolbar-btn" :class="{ active: store.enableSearch }" @click="store.enableSearch = !store.enableSearch" title="联网搜索">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <circle cx="11" cy="11" r="8"/>
                  <line x1="21" y1="21" x2="16.65" y2="16.65"/>
                </svg>
                <span>联网搜索</span>
              </button>
              <button class="toolbar-btn" :class="{ active: store.selectedMcp.length }" @click="openMcpSelect" title="MCP 工具">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M14.7 6.3a1 1 0 000 1.4l1.6 1.6a1 1 0 001.4 0l3.77-3.77a6 6 0 01-7.94 7.94l-6.91 6.91a2.12 2.12 0 01-3-3l6.91-6.91a6 6 0 017.94-7.94l-3.76 3.76z"/>
                </svg>
                <span>MCP{{ store.selectedMcp.length ? `(${store.selectedMcp.length})` : '' }}</span>
              </button>
              <button class="toolbar-btn" :class="{ active: store.uploadedFiles.length || store.uploadedImages.length || store.selectedKnowledge.length }" @click="openFileKnowledgeModal" title="文件、知识库引用">
                <div v-if="store.uploadedFiles.length || store.uploadedImages.length || store.selectedKnowledge.length" class="badge-counts">
                  <span v-if="store.uploadedFiles.length || store.uploadedImages.length" class="badge-item">
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                      <path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z"/>
                      <polyline points="14 2 14 8 20 8"/>
                    </svg>
                    <span>{{ store.uploadedFiles.length + store.uploadedImages.length }}</span>
                  </span>
                  <span v-if="store.selectedKnowledge.length" class="badge-item">
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                      <path d="M4 19.5A2.5 2.5 0 016.5 17H20"/>
                      <path d="M6.5 2H20v20H6.5A2.5 2.5 0 014 19.5v-15A2.5 2.5 0 016.5 2z"/>
                    </svg>
                    <span>{{ store.selectedKnowledge.length }}</span>
                  </span>
                </div>
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M21.44 11.05l-9.19 9.19a6 6 0 01-8.49-8.49l9.19-9.19a4 4 0 015.66 5.66l-9.2 9.19a2 2 0 01-2.83-2.83l8.49-8.48"/>
                </svg>
              </button>
            </div>
            <div class="toolbar-right">
              <button class="toolbar-btn" @click="showModelSelect = true" title="选择模型">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <rect x="2" y="3" width="20" height="14" rx="2" ry="2"/>
                  <line x1="8" y1="21" x2="16" y2="21"/>
                  <line x1="12" y1="17" x2="12" y2="21"/>
                </svg>
                <span>{{ store.currentModel || '选择模型' }}</span>
              </button>
              <button
                v-if="!store.isLoading"
                class="send-btn"
                :class="{ active: store.canSend }"
                :disabled="!store.canSend"
                @click="store.sendMessage"
              >
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <line x1="22" y1="2" x2="11" y2="13"/>
                  <polygon points="22 2 15 22 11 13 2 9 22 2"/>
                </svg>
              </button>
              <button v-else class="send-btn stop-btn" @click="store.stopGenerate">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <rect x="6" y="6" width="12" height="12" rx="2"/>
                </svg>
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Model Select Modal -->
    <div v-if="showModelSelect" class="modal-overlay" @click.self="showModelSelect = false">
      <div class="modal-panel">
        <div class="modal-header">
          <h3>选择模型</h3>
          <button class="close-btn" @click="showModelSelect = false">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <line x1="18" y1="6" x2="6" y2="18"/>
              <line x1="6" y1="6" x2="18" y2="18"/>
            </svg>
          </button>
        </div>
        <div class="modal-body">
          <div class="model-list">
            <div v-for="supplier in store.modelList" :key="supplier.name" class="supplier-group">
              <div class="supplier-name">{{ supplier.title || supplier.name }}</div>
              <div class="model-options">
                <div
                  v-for="model in supplier.models"
                  :key="model.model"
                  class="model-option"
                  :class="{ active: store.currentModel === model.model }"
                  @click="selectModel(model)"
                >
                  <span class="model-title">{{ model.title || model.model }}</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- File & Knowledge Modal -->
    <div v-if="showFileKnowledgeModal" class="modal-overlay" @click.self="showFileKnowledgeModal = false">
      <div class="modal-panel modal-file-knowledge">
        <div class="modal-header">
          <h3>文件、知识库引用</h3>
          <button class="close-btn" @click="showFileKnowledgeModal = false">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <line x1="18" y1="6" x2="6" y2="18"/>
              <line x1="6" y1="6" x2="18" y2="18"/>
            </svg>
          </button>
        </div>
        <div class="modal-body file-knowledge-body">
          <!-- 左侧：文件上传 -->
          <div class="file-section">
            <div class="section-title">上传</div>
            <div class="upload-area" @click="store.chooseFiles">
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4"/>
                <polyline points="17 8 12 3 7 8"/>
                <line x1="12" y1="3" x2="12" y2="15"/>
              </svg>
              <span class="upload-text">点击选择文件</span>
              <span class="upload-hint">支持上传PDF，DOC，TXT等文件和图片（最大不超过20MB）</span>
            </div>
            
            <div class="section-title">已上传</div>
            <div class="uploaded-list">
              <div v-if="store.uploadedFiles.length === 0 && store.uploadedImages.length === 0" class="empty-hint">
                暂无上传文件
              </div>
              <div v-for="(file, idx) in store.uploadedFiles" :key="'f'+idx" class="uploaded-item">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z"/>
                  <polyline points="14 2 14 8 20 8"/>
                </svg>
                <span class="file-name">{{ file.name }}</span>
                <button class="remove-btn" @click="store.removeFile(idx)">
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <line x1="18" y1="6" x2="6" y2="18"/>
                    <line x1="6" y1="6" x2="18" y2="18"/>
                  </svg>
                </button>
              </div>
              <div v-for="(img, idx) in store.uploadedImages" :key="'i'+idx" class="uploaded-item">
                <img :src="img" class="file-thumb" />
                <span class="file-name">图片 {{ idx + 1 }}</span>
                <button class="remove-btn" @click="store.removeImage(idx)">
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <line x1="18" y1="6" x2="6" y2="18"/>
                    <line x1="6" y1="6" x2="18" y2="18"/>
                  </svg>
                </button>
              </div>
            </div>
          </div>
          
          <!-- 分隔线 -->
          <div class="section-divider"></div>
          
          <!-- 右侧：知识库 -->
          <div class="knowledge-section">
            <div class="section-title">知识库引用</div>
            <div class="knowledge-list-modal">
              <div v-if="store.knowledgeList.length === 0" class="empty-state">
                <p>暂无知识库，请先创建</p>
              </div>
              <div v-else>
                <div
                  v-for="kg in store.knowledgeList"
                  :key="kg.ragName"
                  class="knowledge-item"
                  :class="{ active: store.selectedKnowledge.includes(kg.ragName) }"
                  @click="store.toggleKnowledge(kg.ragName)"
                >
                  <div class="knowledge-checkbox">
                    <svg v-if="store.selectedKnowledge.includes(kg.ragName)" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                      <polyline points="20 6 9 17 4 12"/>
                    </svg>
                  </div>
                  <div class="knowledge-info">
                    <div class="knowledge-name">{{ kg.ragName }}</div>
                    <div class="knowledge-desc">{{ kg.ragDesc || '暂无描述' }} · {{ kg.docCount || 0 }} 个文档</div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn-primary" @click="showFileKnowledgeModal = false">确认</button>
        </div>
      </div>
    </div>

    <!-- MCP Select Modal -->
    <div v-if="showMcpSelect" class="modal-overlay" @click.self="showMcpSelect = false">
      <div class="modal-panel">
        <div class="modal-header">
          <h3>选择 MCP 工具</h3>
          <button class="close-btn" @click="showMcpSelect = false">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <line x1="18" y1="6" x2="6" y2="18"/>
              <line x1="6" y1="6" x2="18" y2="18"/>
            </svg>
          </button>
        </div>
        <div class="modal-body">
          <div v-if="store.mcpList.length === 0" class="empty-state">
            <p>暂无 MCP 服务，请先配置</p>
          </div>
          <div v-else class="mcp-list">
            <div
              v-for="mcp in store.mcpList"
              :key="mcp.name"
              class="mcp-option"
              :class="{ active: store.selectedMcp.includes(mcp.name) }"
              @click="store.toggleMcp(mcp.name)"
            >
              <div class="mcp-name">{{ mcp.name }}</div>
              <div class="mcp-desc">{{ mcp.description || '暂无描述' }}</div>
              <div class="mcp-type">{{ mcp.type }}</div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Edit Title Modal -->
    <div v-if="showEditTitle" class="modal-overlay" @click.self="showEditTitle = false">
      <div class="modal-panel modal-sm">
        <div class="modal-header">
          <h3>修改标题</h3>
          <button class="close-btn" @click="showEditTitle = false">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <line x1="18" y1="6" x2="6" y2="18"/>
              <line x1="6" y1="6" x2="18" y2="18"/>
            </svg>
          </button>
        </div>
        <div class="modal-body">
          <input v-model="editTitleText" class="input" placeholder="输入新标题" @keydown.enter="confirmEditTitle" />
        </div>
        <div class="modal-footer">
          <button class="btn-secondary" @click="showEditTitle = false">取消</button>
          <button class="btn-primary" @click="confirmEditTitle">确认</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, nextTick, watch } from 'vue'
import { useRoute } from 'vue-router'
import MarkdownIt from 'markdown-it'
import hljs from 'highlight.js'
import { useChatStore } from '@/stores/chat'
import { agentApi } from '@/api/agent'
import type { AgentItem } from '@/types'

const store = useChatStore()
const route = useRoute()

const md: MarkdownIt = new MarkdownIt({
  html: true,
  linkify: true,
  typographer: true,
  highlight: (str: string, lang: string): string => {
    if (lang && hljs.getLanguage(lang)) {
      try {
        return `<pre class="hljs"><code class="language-${lang}">${hljs.highlight(str, { language: lang }).value}</code></pre>`
      } catch (e) {
        // ignore
      }
    }
    return `<pre class="hljs"><code>${md.utils.escapeHtml(str)}</code></pre>`
  },
})

const messagesRef = ref<HTMLElement>()
const textareaRef = ref<HTMLTextAreaElement>()

const showModelSelect = ref(false)
const showFileKnowledgeModal = ref(false)
const showMcpSelect = ref(false)
const showEditTitle = ref(false)
const editTitleText = ref('')
const editingContextId = ref('')

const renderMarkdown = (text: string) => {
  if (!text) return ''
  return md.render(text)
}

const autoResize = () => {
  nextTick(() => {
    const el = textareaRef.value
    if (!el) return
    el.style.height = 'auto'
    el.style.height = Math.min(el.scrollHeight, 200) + 'px'
  })
}

const handleEnter = (e: KeyboardEvent) => {
  if (e.shiftKey) {
    store.inputText += '\n'
    autoResize()
    return
  }
  store.sendMessage().then(() => {
    nextTick(() => {
      const el = textareaRef.value
      if (el) el.style.height = 'auto'
    })
  })
}

const openFileKnowledgeModal = () => {
  store.loadKnowledgeList()
  showFileKnowledgeModal.value = true
}

const scrollToBottom = () => {
  nextTick(() => {
    messagesRef.value?.scrollTo({ top: messagesRef.value.scrollHeight, behavior: 'smooth' })
  })
}

watch(() => store.messages.length, scrollToBottom)
watch(() => store.isLoading, scrollToBottom)
watch(() => store.messages, scrollToBottom, { deep: true, flush: 'post' })
watch(() => route.query.agent_name, bindAgentFromRoute)

const selectModel = (model: any) => {
  store.selectModel(model.model, model.supplierName || model.supplier_name || '')
  showModelSelect.value = false
}

const openMcpSelect = () => {
  store.loadMcpList()
  showMcpSelect.value = true
}

const startEditTitle = (chat: any) => {
  editingContextId.value = chat.context_id
  editTitleText.value = chat.title
  showEditTitle.value = true
}

const confirmEditTitle = () => {
  const title = editTitleText.value.trim()
  if (!title || !editingContextId.value) return
  store.modifyChatTitle(editingContextId.value, title)
  showEditTitle.value = false
  editingContextId.value = ''
}

const copyText = async (text: string) => {
  try {
    await navigator.clipboard.writeText(text)
  } catch (e) {
    console.error('复制失败', e)
  }
}

// 智能体绑定
async function bindAgentFromRoute() {
  const agentName = route.query.agent_name as string
  if (!agentName) return
  try {
    const res = await agentApi.getAgentInfo(agentName)
    if (res) {
      store.bindAgent(res as AgentItem)
    }
  } catch (e) {
    console.error('加载智能体失败', e)
  }
}

onMounted(() => {
  store.loadChatList()
  store.loadModels()
  store.loadKnowledgeList()
  store.loadMcpList()
  bindAgentFromRoute()
})
</script>

<style scoped lang="scss">
.chat-page {
  display: flex;
  width: 100%;
  height: 100%;
  overflow: hidden;
}

.chat-list {
  width: 260px;
  height: 100%;
  background: var(--bg-secondary);
  border-right: 1px solid var(--border-color);
  display: flex;
  flex-direction: column;
  flex-shrink: 0;
}

.chat-list-header {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px;
}

.new-chat-btn {
  flex: 1;
  padding: 26px;
}

.chat-list-body {
  flex: 1;
  overflow-y: auto;
  padding: 8px;
}

.chat-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 12px;
  border-radius: var(--radius-md);
  cursor: pointer;
  color: var(--text-secondary);
  font-size: 13px;
  transition: all 0.2s;
  position: relative;

  &:hover {
    background: var(--bg-hover);
    color: var(--text-primary);

    .chat-item-actions {
      opacity: 1;
    }
  }

  &.active {
    background: var(--bg-active);
    color: var(--accent-color);
  }
}

.chat-item-icon {
  flex-shrink: 0;
}

.chat-item-title {
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.chat-item-actions {
  opacity: 0;
  display: flex;
  gap: 4px;
  transition: opacity 0.2s;
}

.action-icon {
  width: 20px;
  height: 20px;
  border-radius: var(--radius-sm);
  border: none;
  background: transparent;
  color: var(--text-tertiary);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;

  &:hover {
    background: var(--bg-tertiary);
    color: var(--text-primary);
  }
}

.chat-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-width: 0;
  background: var(--bg-primary);
  position: relative;
}

.chat-top-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 20px;
  border-bottom: 1px solid var(--border-color);
  flex-shrink: 0;
}

.chat-top-left {
  flex: 1;
  min-width: 0;
}

.chat-top-title {
  flex: 1;
  text-align: center;
  font-size: 14px;
  font-weight: 500;
  color: var(--text-primary);
}

.chat-top-right {
  flex: 1;
}

.agent-tag {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 4px 10px;
  border-radius: var(--radius-md);
  background: rgba(59, 130, 246, 0.1);
  color: var(--accent-color);
  font-size: 12px;
  border: 1px solid rgba(59, 130, 246, 0.2);
}

.agent-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--accent-color);
}

.agent-name {
  font-weight: 600;
}

.agent-clear {
  width: 14px;
  height: 14px;
  border: none;
  background: transparent;
  color: var(--accent-color);
  cursor: pointer;
  padding: 0;
  font-size: 14px;
  line-height: 1;
}

/* Welcome Screen */
.welcome-screen {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 32px;
  padding: 40px;
  overflow-y: auto;
}

.agent-welcome {
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  gap: 12px;
}

.agent-welcome-icon {
  width: 72px;
  height: 72px;
  border-radius: 50%;
  background: linear-gradient(135deg, var(--accent-color), #8b5cf6);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 36px;
  color: #fff;
}

.agent-welcome-title {
  font-size: 24px;
  font-weight: 700;
  color: var(--text-primary);
}

.agent-welcome-desc {
  font-size: 14px;
  color: var(--text-secondary);
  max-width: 500px;
  line-height: 1.5;
}

.welcome-messages {
  display: flex;
  flex-direction: column;
  gap: 16px;
  max-width: 560px;
}

.welcome-msg {
  display: flex;
  gap: 12px;
  align-items: flex-start;
}

.welcome-avatar {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background: linear-gradient(135deg, var(--accent-color), #8b5cf6);
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.welcome-bubble {
  padding: 14px 18px;
  background: var(--bg-secondary);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-lg);
  color: var(--text-primary);
  font-size: 14px;
  line-height: 1.6;
}

.quick-actions {
  display: flex;
  gap: 16px;
  flex-wrap: wrap;
  justify-content: center;
}

.quick-card {
  width: 160px;
  padding: 20px;
  background: var(--bg-secondary);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-lg);
  cursor: pointer;
  transition: all 0.2s;
  text-align: center;

  &:hover {
    border-color: var(--accent-color);
    transform: translateY(-2px);
  }
}

.quick-icon {
  width: 48px;
  height: 48px;
  margin: 0 auto 12px;
  border-radius: 50%;
  background: var(--bg-active);
  color: var(--accent-color);
  display: flex;
  align-items: center;
  justify-content: center;
}

.quick-text {
  font-size: 14px;
  font-weight: 500;
  color: var(--text-primary);
}

/* Messages */
.messages-container {
  flex: 1;
  overflow-y: auto;
  padding: 20px 28px;
}

.message-row {
  display: flex;
  gap: 14px;
  margin-bottom: 24px;

  &.user {
    flex-direction: row-reverse;

    .message-body {
      align-items: flex-end;
      background: var(--bg-active);
      color: var(--text-primary);
      border: 1px solid var(--border-color);
      border-radius: var(--radius-lg);
      border-top-right-radius: 4px;
    }
  }

  &.assistant .message-body {
    background: var(--bg-secondary);
    color: var(--text-primary);
    border: 1px solid var(--border-color);
    border-radius: var(--radius-lg);
    border-top-left-radius: 4px;
  }
}

.message-avatar {
  flex-shrink: 0;

  .avatar-user,
  .avatar-assistant {
    width: 34px;
    height: 34px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 12px;
    font-weight: 600;
  }

  .avatar-user {
    background: var(--accent-color);
    color: #fff;
  }

  .avatar-assistant {
    background: var(--bg-active);
    color: var(--accent-color);
  }
}

.message-body {
  max-width: 80%;
  padding: 14px 18px;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.message-text {
  font-size: 14px;
  line-height: 1.7;
  word-break: break-word;
}

.msg-files {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.msg-file-item {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 4px 10px;
  border-radius: var(--radius-md);
  background: var(--bg-primary);
  font-size: 12px;
  color: var(--text-secondary);
}

.msg-images {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.msg-image-preview {
  max-width: 200px;
  max-height: 160px;
  border-radius: var(--radius-md);
  object-fit: cover;
}

.thinking-block {
  border: 1px solid var(--border-color);
  border-radius: var(--radius-md);
  overflow: hidden;
}

.thinking-header {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 12px;
  background: var(--bg-primary);
  cursor: pointer;
  font-size: 12px;
  color: var(--text-secondary);

  svg {
    transition: transform 0.2s;

    &.rotate {
      transform: rotate(180deg);
    }
  }
}

.thinking-content {
  padding: 12px;
  font-size: 13px;
  color: var(--text-secondary);
  background: var(--bg-primary);
  line-height: 1.6;
}

.search-results,
.tools-results {
  border: 1px solid var(--border-color);
  border-radius: var(--radius-md);
  overflow: hidden;
}

.search-header,
.tools-header {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 12px;
  background: var(--bg-primary);
  font-size: 12px;
  font-weight: 500;
  color: var(--text-secondary);
}

.search-list,
.tools-list {
  padding: 8px 12px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.search-item {
  padding: 8px;
  border-radius: var(--radius-md);
  background: var(--bg-primary);
  text-decoration: none;
  transition: background 0.2s;

  &:hover {
    background: var(--bg-hover);
  }
}

.search-title {
  font-size: 13px;
  font-weight: 500;
  color: var(--accent-color);
  margin-bottom: 2px;
}

.search-snippet {
  font-size: 12px;
  color: var(--text-secondary);
  line-height: 1.4;
}

.tool-item {
  padding: 8px;
  border-radius: var(--radius-md);
  background: var(--bg-primary);

  pre {
    margin: 0;
    font-size: 12px;
    white-space: pre-wrap;
    word-break: break-word;
  }
}

.message-actions {
  display: flex;
  gap: 8px;
  margin-top: 4px;
}

.action-btn {
  width: 26px;
  height: 26px;
  border-radius: var(--radius-sm);
  border: none;
  background: transparent;
  color: var(--text-tertiary);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;

  &:hover {
    background: var(--bg-hover);
    color: var(--accent-color);
  }
}

.typing-indicator {
  display: flex;
  gap: 4px;
  padding: 8px 0;

  span {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background: var(--text-tertiary);
    animation: typing 1.4s infinite ease-in-out both;

    &:nth-child(1) { animation-delay: -0.32s; }
    &:nth-child(2) { animation-delay: -0.16s; }
  }
}

@keyframes typing {
  0%, 80%, 100% { transform: scale(0); }
  40% { transform: scale(1); }
}

/* Input */
.input-wrapper {
  padding: 16px 28px 24px;
  flex-shrink: 0;
  background: var(--bg-primary);
  border-top: 1px solid var(--border-color);
}

.uploaded-files-bar {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 10px;
}

.uploaded-chip {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 4px 8px;
  border-radius: var(--radius-md);
  background: var(--bg-secondary);
  border: 1px solid var(--border-color);
  font-size: 12px;
  color: var(--text-primary);
}

.image-chip {
  padding: 2px 2px 2px 8px;
}

.chip-thumb {
  width: 28px;
  height: 28px;
  border-radius: var(--radius-sm);
  object-fit: cover;
}

.chip-name {
  max-width: 120px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.chip-remove {
  width: 16px;
  height: 16px;
  border-radius: 50%;
  border: none;
  background: transparent;
  color: var(--text-tertiary);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;

  &:hover {
    background: var(--bg-hover);
    color: #ef4444;
  }
}

.input-area {
  background: var(--bg-secondary);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-lg);
  padding: 10px 12px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.input-box {
  width: 100%;
}

.chat-textarea {
  width: 100%;
  border: none;
  background: transparent;
  color: var(--text-primary);
  font-size: 14px;
  line-height: 1.5;
  resize: none;
  outline: none;
  max-height: 200px;
  min-height: 50px;
  padding: 4px 0;
  box-sizing: border-box;

  &::placeholder {
    color: var(--text-tertiary);
  }
}

.input-toolbar-bottom {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
}

.toolbar-left {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.toolbar-right {
  display: flex;
  align-items: center;
  gap: 8px;
}

.toolbar-btn {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 5px 10px;
  border-radius: var(--radius-md);
  border: 1px solid var(--border-color);
  background: var(--bg-primary);
  color: var(--text-secondary);
  font-size: 12px;
  cursor: pointer;
  transition: all 0.2s;

  &:hover {
    border-color: var(--accent-color);
    color: var(--accent-color);
  }

  &.active {
    border-color: var(--accent-color);
    color: var(--accent-color);
    background: rgba(59, 130, 246, 0.08);
  }
}

.attach-btn {
  width: 32px;
  height: 32px;
  border-radius: var(--radius-md);
  border: none;
  background: transparent;
  color: var(--text-secondary);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;

  &:hover {
    background: var(--bg-hover);
    color: var(--accent-color);
  }
}

.send-btn {
  width: 34px;
  height: 34px;
  border-radius: 50%;
  border: none;
  background: var(--bg-tertiary);
  color: var(--text-tertiary);
  cursor: not-allowed;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  transition: all 0.2s;

  &.active {
    background: var(--accent-color);
    color: #fff;
    cursor: pointer;

    &:hover {
      opacity: 0.9;
    }
  }

  &.stop-btn {
    background: #ef4444;
    color: #fff;
    cursor: pointer;
  }
}

/* Modals */
.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.45);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 100;
  backdrop-filter: blur(2px);
}

.modal-panel {
  width: 520px;
  max-height: 80vh;
  display: flex;
  flex-direction: column;
  background: var(--bg-primary);
  border-radius: var(--radius-lg);
  border: 1px solid var(--border-color);
  box-shadow: var(--shadow-lg);
}

.modal-sm {
  width: 400px;
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
  flex: 1;
  overflow-y: auto;
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  padding: 12px 20px;
  border-top: 1px solid var(--border-color);
}

.model-list,
.knowledge-list,
.mcp-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.supplier-group {
  border: 1px solid var(--border-color);
  border-radius: var(--radius-md);
  overflow: hidden;
}

.supplier-name {
  padding: 10px 14px;
  background: var(--bg-secondary);
  font-size: 13px;
  font-weight: 600;
  color: var(--text-primary);
}

.model-options {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(140px, 1fr));
  gap: 8px;
  padding: 12px;
}

.model-option {
  padding: 8px 12px;
  border-radius: var(--radius-md);
  border: 1px solid var(--border-color);
  background: var(--bg-secondary);
  cursor: pointer;
  font-size: 13px;
  color: var(--text-primary);
  text-align: center;
  transition: all 0.2s;

  &:hover {
    border-color: var(--accent-color);
  }

  &.active {
    border-color: var(--accent-color);
    background: rgba(59, 130, 246, 0.08);
    color: var(--accent-color);
  }
}

.knowledge-option,
.mcp-option {
  padding: 12px;
  border-radius: var(--radius-md);
  border: 1px solid var(--border-color);
  background: var(--bg-secondary);
  cursor: pointer;
  transition: all 0.2s;

  &:hover {
    border-color: var(--accent-color);
  }

  &.active {
    border-color: var(--accent-color);
    background: rgba(59, 130, 246, 0.08);
  }
}

.knowledge-name,
.mcp-name {
  font-size: 14px;
  font-weight: 500;
  color: var(--text-primary);
  margin-bottom: 4px;
}

.knowledge-desc,
.mcp-desc {
  font-size: 12px;
  color: var(--text-secondary);
}

.mcp-type {
  display: inline-block;
  margin-top: 6px;
  padding: 2px 8px;
  border-radius: 10px;
  font-size: 11px;
  background: var(--bg-active);
  color: var(--text-secondary);
}

.empty-state {
  text-align: center;
  padding: 40px;
  color: var(--text-tertiary);
}

.input {
  width: 100%;
  padding: 9px 12px;
  border: 1px solid var(--border-color);
  border-radius: var(--radius-md);
  background: var(--bg-secondary);
  color: var(--text-primary);
  font-size: 14px;
  outline: none;

  &:focus {
    border-color: var(--accent-color);
  }
}

.btn-primary,
.btn-secondary {
  padding: 7px 16px;
  border-radius: var(--radius-md);
  border: none;
  font-size: 14px;
  cursor: pointer;
}

.btn-primary {
  background: var(--accent-color);
  color: #fff;
}

.btn-secondary {
  background: var(--bg-secondary);
  color: var(--text-primary);
  border: 1px solid var(--border-color);
}

// File & Knowledge Modal
.modal-file-knowledge {
  width: 800px;
}

.file-knowledge-body {
  display: flex;
  gap: 20px;
  min-height: 400px;
}

.file-section {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.knowledge-section {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.section-title {
  font-size: 15px;
  font-weight: 600;
  color: var(--text-primary);
}

.section-divider {
  width: 1px;
  background: var(--border-color);
  flex-shrink: 0;
}

.upload-area {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 40px 16px;
  border: 1px dashed var(--border-color);
  border-radius: var(--radius-md);
  background: var(--bg-secondary);
  cursor: pointer;
  color: var(--text-secondary);
  transition: border-color 0.2s;

  &:hover {
    border-color: var(--accent-color);
  }

  .upload-text {
    font-size: 13px;
  }

  .upload-hint {
    font-size: 11px;
    color: var(--text-tertiary);
  }
}

.uploaded-list {
  flex: 1;
  overflow-y: auto;
  max-height: 240px;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.empty-hint {
  text-align: center;
  padding: 30px;
  color: var(--text-tertiary);
  font-size: 13px;
}

.uploaded-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 10px;
  border-radius: var(--radius-sm);
  color: var(--text-primary);
  font-size: 12px;

  &:hover {
    background: var(--bg-hover);

    .remove-btn {
      opacity: 1;
    }
  }
}

.file-name {
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.file-thumb {
  width: 20px;
  height: 20px;
  border-radius: 3px;
  object-fit: cover;
}

.remove-btn {
  flex-shrink: 0;
  width: 20px;
  height: 20px;
  border: none;
  background: transparent;
  color: var(--text-tertiary);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: var(--radius-sm);
  opacity: 0;
  transition: opacity 0.2s;

  &:hover {
    color: var(--danger-color, #ef4444);
  }
}

.knowledge-list-modal {
  flex: 1;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.knowledge-item {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  padding: 10px 12px;
  border-radius: var(--radius-md);
  cursor: pointer;
  transition: background 0.2s;

  &:hover {
    background: var(--bg-hover);
  }

  &.active {
    background: rgba(59, 130, 246, 0.08);
  }
}

.knowledge-checkbox {
  width: 18px;
  height: 18px;
  border: 1.5px solid var(--border-color);
  border-radius: 4px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  margin-top: 1px;
  color: var(--accent-color);

  .active & {
    border-color: var(--accent-color);
    background: var(--accent-color);
    color: #fff;
  }
}

.knowledge-info {
  flex: 1;
  min-width: 0;
}

.knowledge-info .knowledge-name {
  margin-bottom: 2px;
}

.knowledge-info .knowledge-desc {
  margin-bottom: 0;
}

// Badge counts on toolbar button
.badge-counts {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-right: 6px;
}

.badge-item {
  display: flex;
  align-items: center;
  gap: 2px;
  font-size: 11px;
  color: var(--text-primary);
}
</style>
