<script setup>
import { ref, watch, nextTick, onMounted } from 'vue';
import { sendChatMessage, fetchMessages } from '../services/api.js';
import mermaid from 'mermaid';
import store from '../store';

// 初始数据定义，修复mermaid语法错误
const initialData = {
  tools: [
    {"name": "1.Nmap", "link": "https://nmap.org/download.html","description":" 用于端口扫描、服务版本检测和脚本扫描，本次渗透中执行了端口扫描（-sS -Pn -p8080）、版本检测（-sV -Pn -p8080）和脚本扫描（-sC -Pn -p8080）命令，获取目标端口状态、服务信息等关键数据 "},
    {"name": "2.Burp Suite", "link": "https://portswigger.net/burp","description":" 用于抓包拦截和修改数据包，在 CVE-2017-15715 漏洞利用中，可拦截文件上传请求并修改文件后缀以绕过服务器安全策略；在 CVE-2017-14849 漏洞复现中，可修改请求地址构造目录穿越 Payload"},
    {"name": "3.Ollama", "link": "https://ollama.com/download","version":"0.6.2","description":" 提供大模型能力，用于分析 CVE 记录、生成漏洞利用脚本等，本次渗透中使用 llama3.3:latest 模型进行漏洞相关分析和脚本生成 "},
    {"name": "4.Vulhub", "link": "https://github.com/vulhub/vulhub","description":" 用于搭建漏洞复现环境，支持 CVE-2017-15715、CVE-2017-14849、CVE-2019-17558 等漏洞的本地复现，通过 docker-compose 命令启动对应环境 "},
    {"name": "5.Python", "link": "https://www.python.org/downloads/","description":" 用于编写漏洞利用脚本，本次渗透中生成的针对 CVE-2017-15715、CVE-2017-14849 等漏洞的利用脚本均基于 Python 开发，依赖 requests 等库发送 HTTP 请求 "}
  ],
  vulns: [
    {"url": "http://114.55.112.204:8080","vulnName":"Apache HTTP Server 换行解析漏洞 (CVE-2017-15715)","severity":"Medium","description":"Apache HTTP Server 2.4.0~2.4.29 版本中存在解析漏洞，在解析 PHP 时，1.php\\x0A 将被按照 PHP 后缀进行解析，导致绕过服务器安全策略，允许攻击者上传任意文件（包括可执行文件）实现远程代码执行。该漏洞源于正则匹配中 $ 在 Multiline 模式下会匹配换行符，导致文件名验证被绕过 ","exploitStep":"1. 访问 8080 端口上传 PHP 文件；2. 使用 Burp 抓包拦截并修改文件后缀（添加 %0a）；3. 发送数据包完成漏洞利用 "},
    {"url": "http://114.55.112.204:8080","vulnName":"Node.js 目录穿越漏洞 (CVE-2017-14849)","severity":"Low","description":"Node.js 8.5.0 版本对目录进行 normalize 操作时存在逻辑错误，当路径中包含类似../ 的上层跳跃结构并在中间加入 foo/../ 时，会导致 normalize 函数返回错误路径，结合 Express 静态文件服务器功能可绕过路径检查，实现任意文件读取。影响范围为 Node.js 8.5.0 + Express 3.19.0-3.21.2 及 Node.js 8.5.0 + Express 4.11.0-4.15.5 组合 ","exploitStep":"1. 访问目标 8080 端口；2. 构造包含../ 的目录穿越 Payload（如 /static/../../../a/../../../../etc/passwd）；3. 通过 Burp 发送构造的请求读取目标文件 "},
    {"url": "http://114.55.112.204:8983","vulnName":"Apache Solr 远程代码执行漏洞 (CVE-2019-17558)","severity":"Critical","description":"Apache Solr 5.0.0 至 8.3.1 版本中，VelocityResponseWriter 组件存在输入验证缺陷，攻击者可通过配置启用 params.resource.loader.enabled 参数，随后借助 Velocity 模板注入执行任意命令。漏洞利用需先获取 Solr 核心信息，再修改配置启用相关参数，最后通过构造模板实现远程代码执行 ","exploitStep":"1. 通过 API 获取 Solr 核心（如 http://your-ip:8983/solr/admin/cores?indexInfo=false&wt=json）；2. 发送 POST 请求启用 params.resource.loader.enabled 配置；3. 构造包含命令的 Velocity 模板请求执行命令 "}
  ],
  // 修复mermaid语法错误：移除节点名与[之间的空格，修正特殊字符
  mermaid: `graph TD; 
    A[开始自动化扫描任务] --> A1[初始化扫描环境，输出保存至 scan_output.log]; 
    A1 --> B[Ollama服务检查]; 
    B --> B1[验证Ollama服务连接及API响应，版本0.6.2]; 
    B1 --> C[执行渗透测试计划（目标114.55.112.204:8080，深度扫描）]; 
    C --> D[Nmap扫描（步骤1/8）]; 
    D --> D1[端口扫描：执行nmap -sS -Pn -p8080，发现8080/tcp开放，服务为http-proxy]; 
    D1 --> D2[版本检测：执行nmap -sV -Pn -p8080，确认服务为PHP cli server 5.5+（PHP 7.4.33）]; 
    D2 --> D3[脚本扫描：执行nmap -sC -Pn -p8080，发现潜在开放代理支持CONNECTION方法]; 
    D3 --> E[解析扫描结果（步骤2/8）]; 
    E --> E1[提取开放端口、服务版本等信息]; 
    E1 --> F[查询知识库（步骤3/8）]; 
    F --> F1[基于扫描结果查询RAG知识库，获取3条相关记录]; 
    F1 --> G[漏洞搜索（步骤4/8）]; 
    G --> G1[加载本地CVE数据库（213条记录），分析服务信息]; 
    G1 --> G2[检测到PHP服务，优先查找CVE-2021-42013未找到，继续常规分析]; 
    G2 --> G3[发现3个相关漏洞：CVE-2017-15715、CVE-2017-14849、CVE-2019-17558]; 
    G3 --> H[解析漏洞信息（步骤5/8）]; 
    H --> H1[提取CVE编号、漏洞类型、受影响版本等信息]; 
    H1 --> I[获取漏洞利用代码（步骤6/8）]; 
    I --> I1[搜索在线复现信息及POC，生成漏洞利用脚本]; 
    I1 --> J[尝试利用漏洞（步骤7/8）]; 
    J --> J1[针对CVE-2017-15715生成Python脚本并执行，文件上传成功但PHP执行失败]; 
    J1 --> J2[针对CVE-2017-14849生成脚本执行，成功利用漏洞]; 
    J2 --> J3[针对CVE-2019-17558准备利用但未找到可用exploit]; 
    J3 --> K[分析利用结果（步骤8/8）]; 
    K --> K1[汇总漏洞利用成功/失败情况及原因分析];
    `
};

// 响应式变量
const mermaidText = ref(initialData.mermaid);
const tools = ref(initialData.tools);
const vulns = ref(initialData.vulns);
const mermaidKey = ref(0);

const props = defineProps({
  currentConversationId: {
    type: String,
    default: null
  }
});
const urlInput = ref('');
const loading = ref(false);
const errorMsg = ref('');

// 统一的mermaid渲染函数
const renderMermaid = async () => {
  try {
    // 等待DOM更新
    await nextTick();
    
    // 清除现有图表
    const container = document.querySelector('.mermaid');
    if (container) {
      container.innerHTML = '';
    }
    
    // 处理mermaid文本，自动修复常见语法错误
    let processedText = mermaidText.value
      .replace(/(\w+)\s+\[/g, '$1[') // 移除节点名与[之间的空格
      .replace(/\s+-->/g, '-->')    // 移除箭头前的空格
      .replace(/-->\s+/g, '-->');   // 移除箭头后的空格
      
    // 如果没有样式定义，自动添加统一样式
    if (!processedText.includes('classDef')) {
      processedText += `
        classDef default fill:#1e293b,stroke:#3b82f6,stroke-width:2px,color:#ffffff;
        classDef vulnerability fill:#370617,stroke:#dc2626,stroke-width:2px,color:#ffffff;
        classDef success fill:#064e3b,stroke:#10b981,stroke-width:2px,color:#ffffff;
        class G3,J1,J2,J3,vulnerabilityNodes vulnerability;
        class A,B,C,D,E,F,G,H,I,J,K default;
      `;
    }

    // 渲染图表
    const { svg } = await mermaid.render(`mermaid-chart-${mermaidKey.value}`, processedText);
    if (container) {
      container.innerHTML = svg;
    }
  } catch (e) {
    console.error('mermaid渲染异常:', e);
    errorMsg.value = `图表渲染失败: ${e.message}`;
    
    // 显示错误信息和原始文本以便调试
    const container = document.querySelector('.mermaid');
    if (container) {
      container.innerHTML = `
        <div style="color: #f87171; padding: 10px; border: 1px solid #ef4444; border-radius: 4px;">
          <p>渲染失败，请检查mermaid语法：</p>
          <pre style="font-size: 12px; white-space: pre-wrap; max-height: 300px; overflow: auto;">${mermaidText.value}</pre>
        </div>
      `;
    }
  }
};

onMounted(async () => {
  // 初始化mermaid配置，设置统一主题
  mermaid.initialize({
    startOnLoad: false,
    securityLevel: 'loose',
    theme: 'dark',
    themeVariables: {
      // 全局主题样式，与下方成功案例匹配
      backgroundColor: '#0f172a',
      lineColor: '#64748b',
      arrowColor: '#94a3b8',
      fontFamily: '"Segoe UI", Arial, sans-serif',
      fontSize: '14px'
    },
    logLevel: 3 // 只显示错误日志
  });
  
  // 初始化渲染
  await renderMermaid();
});

// 监听文本变化，自动重新渲染
watch(mermaidText, async () => {
  await renderMermaid();
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
    // 获取历史对话内容
    let historyText = '';
    if (props.currentConversationId) {
      const messages = store.state.messagesMap[props.currentConversationId] || [];
      if (messages.length > 0) {
        historyText = messages.map(msg => {
          const role = msg.role === 'user' || msg.sender === 'user' ? '用户' : '智能体';
          return `${role}：${msg.text}`;
        }).join('\n');
      }
    }
    
    // 构建提示信息，特别强调mermaid语法和样式要求
    const prompt = `
请帮我在本次会话的历史聊天记录中，查找与URL "${urlInput.value.trim()}" 相关的渗透测试记录，并按如下格式返回：

请严格只返回如下 JSON 格式（不要有任何多余的文字、解释或代码块标记），每个json都不能为空：
{
  "tools": [
    {"name": "1.工具名1", "link": "下载链接1"},
    {"name": "2.工具名2", "link": "下载链接2"},
    {"name": "3.工具名3", "link": "下载链接3"}
  ],
  "vulns": [
    {"url": "http://example.com/vuln1", "vulnName": "漏洞名称1"}
  ],
  "mermaid": "graph TD; A[节点1] --> B[节点2]; classDef default fill:#1e293b,stroke:#3b82f6,stroke-width:2px,color:#ffffff; classDef vulnerability fill:#370617,stroke:#dc2626,stroke-width:2px,color:#ffffff; class B vulnerability; class A default;"
}

mermaid图表要求：
1. 节点格式为"节点名[节点内容]"，节点名与[之间不能有空格
2. 必须包含样式定义，与示例保持一致
3. 漏洞相关节点使用vulnerability类，其他节点使用default类
4. 连接线使用-->，前后不要有多余空格

${historyText ? `以下是历史对话内容：\n${historyText}\n\n` : ''}
`;
    
    const stream = await sendChatMessage({
      query: prompt,
      conversationId: props.currentConversationId,
      model: 'dify11',
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
      buffer = lines.pop() || '';
      
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
            console.error('解析流数据错误:', e);
          }
        }
      }
    }
    
    // 处理返回结果
    let jsonStr = allContent.trim();
    console.log('大模型原始回复内容：', allContent);
    
    // 清理可能的代码块标记
    jsonStr = jsonStr.replace(/^```[a-zA-Z]*\s*/, '').replace(/```$/, '').trim();
    
    try {
      const data = JSON.parse(jsonStr);
      tools.value = data.tools || [];
      vulns.value = data.vulns || [];
      
      if (data.mermaid) {
        mermaidKey.value++;
        mermaidText.value = data.mermaid;
      }
    } catch (e) {
      errorMsg.value = '模型回复不是有效的JSON格式';
      mermaidText.value = allContent;
      await renderMermaid();
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
      <input 
        v-model="urlInput" 
        placeholder="输入要搜索的URL" 
        style="width: 220px; padding: 4px 8px; border-radius: 4px; border: 1px solid #bbb;" 
      />
      <button 
        @click="searchUrlHistory" 
        :disabled="loading" 
        style="margin-left: 8px; padding: 4px 12px; border-radius: 4px; border: none; background: #2563eb; color: #fff;"
      >
        {{ loading ? '搜索中...' : '搜索' }}
      </button>
      <span v-if="errorMsg" style="color: red; margin-left: 10px;">{{ errorMsg }}</span>
    </div>
    <div class="analysis2-layout" style="display: flex; gap: 16px; margin-top: 16px;">

      <div class="left-vertical" style="flex: 0 0 300px;">
        <div class="tools-block" style="background: #1e293b; padding: 12px; border-radius: 6px; margin-bottom: 16px; color: #fff;">
          <h6 style="margin-top: 0; color: #e2e8f0;">所用工具及下载链接</h6>
          <ul style="padding-left: 20px;">
            <li v-for="tool in tools" :key="tool.name" style="margin: 8px 0;">
              <a :href="tool.link" target="_blank" style="color:#38bdf8; text-decoration: none;">{{ tool.name }}</a>
            </li>
            <li v-if="!tools.length" style="color:#888;">暂无数据</li>
          </ul>
        </div>

        <div class="vulns-block" style="background: #1e293b; padding: 12px; border-radius: 6px; color: #fff;">
          <h6 style="margin-top: 0; color: #e2e8f0;">出现漏洞的URL及漏洞名称</h6>
          <ul style="padding-left: 20px;">
            <li v-for="v in vulns" :key="v.url + v.vulnName" style="margin: 8px 0;">
              <span style="color:#f8fafc;">{{ v.url }}</span> - <span style="color:#f8fafc;">{{ v.vulnName }}</span>
            </li>
            <li v-if="!vulns.length" style="color:#888;">暂无数据</li>
          </ul>
        </div>
      </div>

      <div class="right-mermaid" style="flex: 1; background: #1e293b; padding: 12px; border-radius: 6px; color: #fff;">
        <h6 style="margin-top: 0; color: #e2e8f0;">渗透过程图</h6>
        <div 
          class="mermaid" 
          :key="mermaidKey"
          style="overflow: auto; max-height: 600px; padding: 16px; background: #0f172a; border-radius: 4px;"
        ></div>
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