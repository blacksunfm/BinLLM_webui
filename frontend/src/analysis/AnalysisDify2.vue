<script setup>
import { ref, watch, nextTick, onMounted } from 'vue';
import { sendChatMessage } from '../services/api.js';
import mermaid from 'mermaid';

// 先定义 mermaidText，确保后续所有用到它的地方都已声明
const mermaidText = ref(`graph TD; A[请输入智能体曾渗透过的url]`); // 右侧区域显示内容

// 新增 mermaidKey 用于强制刷新 mermaid 容器
const mermaidKey = ref(0);

// 其他响应式数据
const props = defineProps({
  currentConversationId: {
    type: String,
    default: null
  }
});
const urlInput = ref('');
const loading = ref(false);
const errorMsg = ref('');
const tools = ref([]); // [{name, link}]
const vulns = ref([]); // [{url, vulnName}]

// mermaid 初始化和首次渲染
onMounted(() => {
  mermaid.initialize({
    startOnLoad: false,
    securityLevel: 'loose',
    theme: 'default'
  });
  try {
    mermaid.init(undefined, '.mermaid');
  } catch (e) {
    console.error('mermaid 渲染异常', e);
  }
});

// 监听 mermaidText 变化，动态渲染
watch(mermaidText, async () => {
  await nextTick();
  try {
    mermaid.init(undefined, '.mermaid');
  } catch (e) {
    console.error('mermaid 渲染异常', e);
  }
});

async function searchUrlHistory() {
  if (!urlInput.value.trim()) {
    errorMsg.value = '请输入URL';
    return;
  }
  errorMsg.value = '';
  loading.value = true;
  tools.value = [];
  vulns.value = [];
  mermaidText.value = '';
  try {
    const prompt = `请帮我在本次会话的历史聊天记录中，查找与URL "${urlInput.value.trim()}" 相关的渗透测试记录，并按如下格式返回：

请严格只返回如下 JSON 格式（不要有任何多余的文字、解释或代码块标记）：
{
  "tools": [
    {"name": "1.工具名1", "link": "下载链接1"},
    {"name": "2.工具名2", "link": "下载链接2"},
    {"name": "3.工具名3", "link": "下载链接3"},
  ],
  "vulns": [
    {"url": "http://example.com/vuln1", "vulnName": "漏洞名称1"}
  ],
  "mermaid": "graph TD; ...（mermaid流程图代码）"
  }
  还有要求就是mermaid图里面的文字一定要特别详细，都要用20个字以上的文字能够完全指引用户完成这步操作，以中文为主
  `;
    const stream = await sendChatMessage({
      query: prompt,
      conversationId: props.currentConversationId,
      model: 'dify2',
      user: 'vue-app-user',
      stream: true
    });
    const reader = stream.getReader();
    const decoder = new TextDecoder();
    let buffer = '';
    let allContent = '';
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value);
      let lines = buffer.split('\n');
      buffer = lines.pop(); // 可能有半条，留到下次
      for (const line of lines) {
        if (line.startsWith('data: ')) {
          try {
            const data = JSON.parse(line.slice(6));
            if (data.event === 'message' && data.answer) {
              allContent += data.answer;
            } else if (data.event === 'error') {
              errorMsg.value = data.message;
            }
          } catch (e) {
            // 不是JSON就跳过
          }
        }
      }
    }
    // 流结束后整体渲染
    let jsonStr = allContent.trim();
    // 去除代码块包裹
    jsonStr = jsonStr.replace(/^```[a-zA-Z]*\s*/, '').replace(/```$/, '').trim();
    try {
      const data = JSON.parse(jsonStr);
      tools.value = data.tools || [];
      vulns.value = data.vulns || [];
      mermaidText.value = '';
      await nextTick();
      mermaidText.value = data.mermaid || '';
      mermaidKey.value++;
      await nextTick();
      setTimeout(() => {
        try {
          mermaid.init(undefined, '.mermaid');
        } catch (e) {
          console.error('mermaid 渲染异常', e);
        }
      }, 0);
    } catch (e) {
      errorMsg.value = '模型回复不是有效的JSON格式';
      mermaidText.value = allContent; // 兜底显示原始内容
    }
  } catch (e) {
    errorMsg.value = e.message || '请求失败';
  } finally {
    loading.value = false;
  }
}
</script>

<template>
  <div>
    <h5>渗透测试智能体分析界面</h5>
    <div style="margin-bottom: 12px;">
      <input v-model="urlInput" placeholder="输入要搜索的URL" style="width: 220px; padding: 4px 8px; border-radius: 4px; border: 1px solid #bbb;" />
      <button @click="searchUrlHistory" :disabled="loading" style="margin-left: 8px; padding: 4px 12px; border-radius: 4px; border: none; background: #2563eb; color: #fff;">{{ loading ? '搜索中...' : '搜索' }}</button>
      <span v-if="errorMsg" style="color: red; margin-left: 10px;">{{ errorMsg }}</span>
    </div>
    <div class="analysis2-layout">
      <!-- 左侧上下结构 -->
      <div class="left-vertical">
        <!-- 工具及下载链接 -->
        <div class="tools-block">
          <h6>所用工具及下载链接</h6>
          <ul>
            <li v-for="tool in tools" :key="tool.name">
              <a :href="tool.link" target="_blank" style="color:#fff;">{{ tool.name }}</a>
            </li>
            <li v-if="!tools.length" style="color:#888;">暂无数据</li>
          </ul>
        </div>
        <!-- 漏洞URL及名称 -->
        <div class="vulns-block">
          <h6>出现漏洞的URL及漏洞名称</h6>
          <ul>
            <li v-for="v in vulns" :key="v.url + v.vulnName">
              <span style="color:#fff;">{{ v.url }}</span> - <span style="color:#fff;">{{ v.vulnName }}</span>
            </li>
            <li v-if="!vulns.length" style="color:#888;">暂无数据</li>
          </ul>
        </div>
      </div>
      <!-- 右侧mermaid图 -->
      <div class="right-mermaid">
        <h6>渗透过程图</h6>
        <div class="mermaid" v-html="mermaidText" :key="mermaidKey"></div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.analysis2-layout {
  display: flex;
  flex-direction: row;
  gap: 18px;
  min-height: 320px;
  height: 800px;
  align-items: stretch;
  box-sizing: border-box;
}
.left-vertical, .right-mermaid {
  flex: 1;
  height: 100%;
  min-height: 0;
  box-sizing: border-box;
}
.left-vertical {
  display: flex;
  flex-direction: column;
  gap: 18px;
}
.tools-block, .vulns-block {
  flex: 1;
  background: #23272f;
  border-radius: 6px;
  padding: 12px 16px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.08);
  color: #e0e6ef;
  overflow-y: auto;
  scrollbar-width: none;
  -ms-overflow-style: none;
  min-height: 0;
  box-sizing: border-box;
}
.tools-block::-webkit-scrollbar, .vulns-block::-webkit-scrollbar {
  display: none;
}
.right-mermaid {
  background: #23272f;
  border-radius: 6px;
  padding: 12px 16px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.08);
  display: flex;
  flex-direction: column;
  color: #e0e6ef;
  overflow-y: auto;
  scrollbar-width: none;
  -ms-overflow-style: none;
  min-height: 0;
  box-sizing: border-box;
}
.right-mermaid::-webkit-scrollbar {
  display: none;
}
.right-mermaid h6, .tools-block h6, .vulns-block h6 {
  color: #8ab4f8;
  margin-bottom: 12px;
}
.mermaid {
  min-height: 200px;
  background: transparent;
  color: #e0e6ef;
  margin: 0;
  padding: 0;
}
ul {
  padding-left: 18px;
}
li {
  color: #e0e6ef;
}
</style>