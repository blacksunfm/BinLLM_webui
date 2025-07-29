<script setup>
import { ref, watch, nextTick, onMounted, computed } from 'vue';
import { sendChatMessage, fetchMessages } from '../services/api.js';
import store from '../store';
import { marked } from 'marked';

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
  // 渗透测试报告模板
  report: `# 渗透测试报告

## 测试目标
- URL: http://114.55.112.204:8080
- 测试时间: 2025-03-23 12:10:35
- 测试类型: 深度扫描

## 扫描结果
- 开放端口: 8080/tcp
- 服务类型: PHP cli server 5.5+ (PHP 7.4.33)
- 发现漏洞: 3个

## 漏洞详情
1. Apache HTTP Server 换行解析漏洞 (CVE-2017-15715)
2. Node.js 目录穿越漏洞 (CVE-2017-14849)  
3. Apache Solr 远程代码执行漏洞 (CVE-2019-17558)

## 测试结论
目标系统存在多个安全漏洞，建议及时修复。`
};

// 响应式变量
const reportText = ref(initialData.report);
const tools = ref(initialData.tools);
const vulns = ref(initialData.vulns);

const props = defineProps({
  currentConversationId: {
    type: String,
    default: null
  }
});
const urlInput = ref('');
const loading = ref(false);
const errorMsg = ref('');

const renderedReport = computed(() => {
  if (!reportText.value) return '';
  try {
    return marked.parse(reportText.value);
  } catch (e) {
    return reportText.value;
  }
});

async function processBatchAnalysis() {
  if (!urlInput.value.trim()) {
    errorMsg.value = '请输入 URL';
    return;
  }
  const targetUrl = urlInput.value.trim();

  loading.value = true;
  tools.value = [];
  vulns.value = [];
  reportText.value = '';
  
  try {
    // 1. 取历史消息
    let messages = [];
    if (props.currentConversationId) {
      messages = store.state.messagesMap[props.currentConversationId] || [];
    }
    if (!messages.length) {
      errorMsg.value = '没有找到历史对话记录';
      return;
    }
    
    // 2. 找到包含 URL 的第一条用户消息
    const urlIndex = messages.findIndex(m =>
      (m.role === 'user' || m.sender === 'user') && m.text?.includes(targetUrl)
    );
    if (urlIndex === -1) {
      errorMsg.value = `未找到包含 ${targetUrl} 的历史消息`;
      return;
    }
    
    // 3. 取后续所有消息
    const penetrationMessages = messages.slice(urlIndex + 1);
    if (!penetrationMessages.length) {
      errorMsg.value = '未找到渗透测试过程记录';
      return;
    }
    
    // 4. 分批
    const maxChars = 40000;
    const batches = splitMessagesIntoBatches(penetrationMessages, maxChars);
    
    // 5. ✅ 第一次请求用 null，让 Dify 创建新会话
    let conversationId = null;
    
    // 6. ✅ 发送初始提示，并获取 Dify 返回的 conversationId
    console.log('发送初始提示...');
    const initRes = await sendAndWait({
      query: `我将分批发送关于 ${targetUrl} 的渗透测试历史记录，请全部记住，最后生成 JSON 报告。收到请回复"OK"。`,
      conversationId
    });
    conversationId = initRes.conversationId; // ✅ 更新为 Dify 返回的 ID
    console.log('✅ 已获取 Dify 会话ID:', conversationId);
    
    // 7. ✅ 逐批发送（都用同一个 conversationId）
    // 存储每批次的结果
    const allBatchResults = {
      tools: new Set(),
      vulns: new Set(),
      reports: []
    };
    
    for (let i = 0; i < batches.length; i++) {
      
      const batchText = batches[i]
        .map(m => `${m.role === 'user' || m.sender === 'user' ? '用户' : '智能体'}：${m.text}`)
        .join('\n\n');
      
      const prompt = `第 ${i + 1}/${batches.length} 批历史记录：\n\n${batchText}\n\n请分析这批历史记录，按以下格式返回（不要包含\`\`\`json标记）：

工具：发现的工具1，工具2，工具3
漏洞：发现的漏洞1，漏洞2，漏洞3
报告：对这批记录的分析报告

注意：工具和漏洞每个都至少包含yi个，报告至少100字。`;
      
      const batchResponse = await sendAndWait({ query: prompt, conversationId });
      
      try {
        // 解析每批次的字符串结果
        let batchText = batchResponse.text.replace(/^```json\s*/, '').replace(/```$/, '').trim();
        
        // 如果是JSON格式，尝试修复不完整的JSON
        if (batchText.startsWith('{')) {
          console.log(`批次 ${i + 1} 检测到JSON格式，尝试修复:`, batchText);
          
          // 尝试找到完整的JSON
          const jsonMatch = batchText.match(/\{[\s\S]*\}/);
          if (jsonMatch) {
            batchText = jsonMatch[0];
          }
          
          // 如果JSON不完整，尝试手动修复
          if (!batchText.endsWith('}')) {
            // 查找最后一个完整的属性
            const lastCompleteMatch = batchText.match(/"report":\s*"([^"]*)"\s*$/);
            if (lastCompleteMatch) {
              batchText = batchText.substring(0, batchText.lastIndexOf('"') + 1) + '}';
            } else {
              // 如果连report都没有，添加默认的结束
              batchText = batchText + '"report": "分析报告" }';
            }
          }
          
          try {
            const batchResult = JSON.parse(batchText);
            
            // 合并工具和漏洞（使用Set去重）
            if (batchResult.tools && Array.isArray(batchResult.tools)) {
              batchResult.tools.forEach(tool => allBatchResults.tools.add(tool));
            }
            
            if (batchResult.vulns && Array.isArray(batchResult.vulns)) {
              batchResult.vulns.forEach(vuln => allBatchResults.vulns.add(vuln));
            }
            
            // 添加报告
            if (batchResult.report) {
              allBatchResults.reports.push(`批次${i + 1}报告: ${batchResult.report}`);
            }
            
            console.log(`批次 ${i + 1} JSON解析成功:`, batchResult);
            continue; // 成功解析JSON，跳过字符串解析
          } catch (jsonError) {
            console.warn(`批次 ${i + 1} JSON解析失败，尝试字符串解析:`, jsonError);
          }
        }
        
        // 字符串格式解析
        // 提取工具
        const toolsMatch = batchText.match(/工具：(.+?)(?=\n|$)/);
        if (toolsMatch) {
          const tools = toolsMatch[1].split('，').map(t => t.trim()).filter(t => t);
          tools.forEach(tool => allBatchResults.tools.add(tool));
        }
        
        // 提取漏洞
        const vulnsMatch = batchText.match(/漏洞：(.+?)(?=\n|$)/);
        if (vulnsMatch) {
          const vulns = vulnsMatch[1].split('，').map(v => v.trim()).filter(v => v);
          vulns.forEach(vuln => allBatchResults.vulns.add(vuln));
        }
        
        // 提取报告
        const reportMatch = batchText.match(/报告：(.+?)(?=\n|$)/);
        if (reportMatch) {
          allBatchResults.reports.push(`批次${i + 1}报告: ${reportMatch[1].trim()}`);
    }
    
        console.log(`批次 ${i + 1} 字符串解析结果:`, batchText);
      } catch (e) {
        console.error(`批次 ${i + 1} 结果解析失败:`, e);
      }
    }

    // 8. ✅ 请求最终 JSON
    
    // 准备合并后的数据
    const mergedTools = Array.from(allBatchResults.tools);
    const mergedVulns = Array.from(allBatchResults.vulns);
    const mergedReports = allBatchResults.reports.join('\n\n');
    
    const finalPrompt = `请根据以下已收集的信息，整合并返回最终的渗透测试报告JSON：

各批次报告:
${mergedReports}

请整合上述信息，返回严格的JSON格式
{
  "tools": [
    {"name": "1.Nmap", "link": "https://nmap.org/download.html", "description": "用于端口扫描、服务版本检测和脚本扫描"},
    {"name": "2.Burp Suite", "link": "https://portswigger.net/burp", "description": "用于抓包拦截和修改数据包"},
    {"name": "3.Metasploit", "link": "https://www.metasploit.com/download", "description": "漏洞利用框架"}
  ],
  "vulns": [
    {"url": "http://target:8080", "vulnName": "CVE-2017-15715", "severity": "Medium", "description": "Apache HTTP Server 换行解析漏洞"},
    {"url": "http://target:8080", "vulnName": "CVE-2017-14849", "severity": "Low", "description": "Node.js 目录穿越漏洞"},
    {"url": "http://target:8983", "vulnName": "CVE-2019-17558", "severity": "Critical", "description": "Apache Solr 远程代码执行漏洞"}
  ],
  "report": "完整的综合报告，至少200字"
}

要求：
1. 只能返回JSON，其他文字一律不要
2. tools和vulns数组每个至少包含5个元素
3. report至少400字，使用markdown格式
4. 确保JSON格式正确，可以被JSON.parse()解析
`;
    
    const finalResponse = await sendAndWait({ query: finalPrompt, conversationId });
    let finalJsonStr = finalResponse.text;

    try {

      finalJsonStr = finalJsonStr.replace(/^```json\s*/, '').replace(/```$/, '').trim();
      
      // 如果JSON不完整，尝试修复
      if (!finalJsonStr.startsWith('{') || !finalJsonStr.endsWith('}')) {
        console.warn('最终JSON不完整，尝试修复:', finalJsonStr);
    
        // 尝试找到完整的JSON结构
        const jsonMatch = finalJsonStr.match(/\{[\s\S]*\}/);
        if (jsonMatch) {
          finalJsonStr = jsonMatch[0];
        } else {
          // 如果连基本的JSON结构都找不到，尝试手动修复
          if (finalJsonStr.includes('"report":')) {
            // 找到report字段的开始位置
            const reportStart = finalJsonStr.indexOf('"report":');
            if (reportStart !== -1) {
              // 提取report字段的内容，并手动添加结束
              const reportContent = finalJsonStr.substring(reportStart);
              // 找到最后一个完整的引号位置
              const lastQuoteIndex = reportContent.lastIndexOf('"');
              if (lastQuoteIndex !== -1) {
                finalJsonStr = finalJsonStr.substring(0, reportStart + lastQuoteIndex + 1) + '}';
    } else {
                // 如果连引号都找不到，添加默认的结束
                finalJsonStr = finalJsonStr + '"报告内容" }';
              }
            }
          }
        }
      }
      
      const res = JSON.parse(finalJsonStr);
      console.log('最终JSON解析成功:', res);
      
      tools.value = res.tools || [];
      vulns.value = res.vulns || [];
      reportText.value = res.report || '';
      
      console.log('数据已赋值到前端:', {
        tools: tools.value,
        vulns: vulns.value,
        reportLength: reportText.value.length
      });
    } catch (e) {
      console.error('最终JSON解析失败:', e);
      console.error('原始JSON字符串:', finalJsonStr);
      
      // 如果JSON解析失败，使用收集的数据作为备选
      tools.value = Array.from(allBatchResults.tools);
      vulns.value = Array.from(allBatchResults.vulns);
      reportText.value = allBatchResults.reports.join('\n\n');
      
      console.log('使用备选数据:', {
        tools: tools.value,
        vulns: vulns.value,
        reportLength: reportText.value.length
      });
    }
    
  } catch (e) {
    console.error(e);
    errorMsg.value = e.message || '处理失败';
  } finally {
    loading.value = false;
  }
}
// 发送消息并等待完整回复
// ✅ 修改后的 sendAndWait - 返回 { text, conversationId }
async function sendAndWait(opts) {
  const { query, conversationId: inputId } = opts;
  let finalConversationId = inputId;

  try {
    console.log(`发送消息（会话ID: ${inputId || 'null（新会话）'}）`);

    const stream = await sendChatMessage({
      query,
      conversationId: inputId,
      model: 'dify11',
      user: 'vue-app-user',
      stream: true
    });

    let response = '';
    const reader = stream.getReader();
    const decoder = new TextDecoder('utf-8');
    let buffer = '';

    let startTime = Date.now();
    const maxWaitTime = 1200000; // 增加到120秒，给AI更多时间生成完整报告
    
    let messageEndReceived = false;
    
    while (true) {
      const { done, value } = await reader.read();
      if (done) {
        console.log('✅ ReadableStream结束');
        break;
      }

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split('\n\n');
      buffer = lines.pop() || '';

      for (const line of lines) {
        if (line.startsWith('data:')) {
          const dataStr = line.slice(6).trim();
          if (!dataStr) continue;

          try {
            const data = JSON.parse(dataStr);
            if (data.event === 'message' && data.answer) {
              response += data.answer;
              console.log('AI回复片段:', data.answer);
            } else if (data.event === 'message_end') {
              messageEndReceived = true;
              if (data.conversation_id) {
                finalConversationId = data.conversation_id;
              }
              console.log('✅ 收到message_end事件，Dify输出结束，conversationId:', finalConversationId);
              // ✅ 收到message_end事件后，可以安全地结束循环
              break;
            } else if (data.event === 'error') {
              throw new Error(data.message);
            }
          } catch {
            // 忽略无效 JSON 行
          }
        }
      }
      
      // 如果已经收到message_end事件，退出外层循环
      if (messageEndReceived) {
        break;
      }
      
      // 检查超时
      if (Date.now() - startTime > maxWaitTime) {
        console.log('等待超时，强制结束');
        break;
      }
    }

    console.log('✅ 最终响应长度:', response.length);
    console.log('✅ 最终conversationId:', finalConversationId);
    
    if (!response.trim()) {
      throw new Error('AI 返回为空');
    }

    return { text: response.trim(), conversationId: finalConversationId };
  } catch (error) {
    console.error('sendAndWait 错误:', error);
    throw error;
  }
}
// 将消息分批
function splitMessagesIntoBatches(messages, maxCharsPerBatch) {
  const batches = [];
  let currentBatch = [];
  let currentBatchChars = 0;
  
  console.log(`开始分批处理，总消息数：${messages.length}，每批次最大字符数：${maxCharsPerBatch}`);
  
  for (let i = 0; i < messages.length; i++) {
    const message = messages[i];
    const messageText = message.text || '';
    const messageChars = messageText.length;
    
    console.log(`处理第${i + 1}条消息：${messageChars}字符，当前批次字符数：${currentBatchChars}`);
    
    // 如果单条消息就超过限制，需要分割处理
    if (messageChars > maxCharsPerBatch) {
      // 如果当前批次不为空，先保存当前批次
      if (currentBatch.length > 0) {
        batches.push([...currentBatch]);
        console.log(`保存批次${batches.length}：${currentBatch.length}条消息，${currentBatchChars}字符`);
        currentBatch = [];
        currentBatchChars = 0;
      }
      
      // 分割超长消息
      const messageChunks = splitLongMessage(message, maxCharsPerBatch);
      console.log(`超长消息分割为${messageChunks.length}个块`);
      
      // 将每个块作为一个批次
      for (let j = 0; j < messageChunks.length; j++) {
        batches.push([messageChunks[j]]);
        console.log(`超长消息块${j + 1}成批次${batches.length}：1条消息，${messageChunks[j].text.length}字符`);
      }
      continue;
    }
    
    // 检查添加这条消息是否会超出限制
    const wouldExceed = currentBatchChars + messageChars > maxCharsPerBatch;
    console.log(`添加后字符数：${currentBatchChars + messageChars}，限制：${maxCharsPerBatch}，会超出：${wouldExceed}`);
    
    if (wouldExceed && currentBatch.length > 0) {
      // 会超出限制且当前批次不为空，先保存当前批次
      batches.push([...currentBatch]);
      console.log(`保存批次${batches.length}：${currentBatch.length}条消息，${currentBatchChars}字符`);
      currentBatch = [];
      currentBatchChars = 0;
    }
    
    // 添加到当前批次（无论是新批次还是继续当前批次）
      currentBatch.push(message);
      currentBatchChars += messageChars;
    console.log(`添加到当前批次，当前总字符：${currentBatchChars}，批次消息数：${currentBatch.length}`);
  }
  
  // 添加最后一个批次
  if (currentBatch.length > 0) {
    batches.push(currentBatch);
    console.log(`保存最后批次${batches.length}：${currentBatch.length}条消息，${currentBatchChars}字符`);
  }
  
  console.log(`分批结果：${batches.length}个批次，总消息数：${messages.length}`);
  batches.forEach((batch, index) => {
    const totalChars = batch.reduce((sum, msg) => sum + (msg.text?.length || 0), 0);
    console.log(`批次${index + 1}：${batch.length}条消息，${totalChars}字符`);
    
    // 验证每个批次是否真的在限制内
    if (totalChars > maxCharsPerBatch) {
      console.warn(`警告：批次${index + 1}超出限制！${totalChars} > ${maxCharsPerBatch}`);
    }
  });
  
  return batches;
}

// 分割超长消息
function splitLongMessage(message, maxCharsPerBatch) {
  const messageText = message.text || '';
  const chunks = [];
  
  // 按句子分割，尽量保持语义完整性
  const sentences = messageText.split(/(?<=[。！？\n])/);
  let currentChunk = '';
  let currentChunkText = '';
      
  for (const sentence of sentences) {
    // 如果当前句子加上现有内容会超出限制
    if (currentChunkText.length + sentence.length > maxCharsPerBatch && currentChunkText.length > 0) {
      // 保存当前块
      chunks.push({
        ...message,
        text: currentChunkText.trim(),
        id: `${message.id}_chunk_${chunks.length + 1}`
      });
      currentChunkText = sentence;
    } else {
      // 添加到当前块
      currentChunkText += sentence;
    }
  }
  
  // 添加最后一个块
  if (currentChunkText.trim()) {
    chunks.push({
      ...message,
      text: currentChunkText.trim(),
      id: `${message.id}_chunk_${chunks.length + 1}`
    });
  }
  
  console.log(`消息分割为${chunks.length}个块，原长度：${messageText.length}`);
  chunks.forEach((chunk, index) => {
    console.log(`块${index + 1}：${chunk.text.length}字符`);
  });
  
  return chunks;
  }


onMounted(async () => {
  // 组件初始化
  console.log('渗透测试分析组件已加载');
});

// 搜索URL历史记录
async function searchUrlHistory() {
  await processBatchAnalysis();
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
        {{ loading ? '分析中...' : '搜索' }}
      </button>
      <span v-if="errorMsg" style="color: red; margin-left: 10px;">{{ errorMsg }}</span>
      
    </div>
    <div class="analysis2-layout" style="display: flex; gap: 16px; margin-top: 16px;">

      <div class="left-vertical" style="flex: 0 0 380px;">
        <div class="tools-block" style="background: #1e293b; padding: 12px; border-radius: 6px; margin-bottom: 16px; color: #fff;">
          <h6 style="margin-top: 0; color: #e2e8f0; font-size: 20px;">所用工具及下载链接</h6>
          <ul style="padding-left: 20px;">
            <li v-for="tool in tools" :key="tool.name" style="margin: 8px 0;">
              <a :href="tool.link" target="_blank" style="color:#38bdf8; text-decoration: none;">{{ tool.name }}</a>
            </li>
            <li v-if="!tools.length" style="color:#888;">暂无数据</li>
          </ul>
        </div>

        <div class="vulns-block" style="background: #1e293b; padding: 12px; border-radius: 6px; color: #fff;">
          <h6 style="margin-top: 0; color: #e2e8f0; font-size: 20px;">出现漏洞的URL及漏洞名称</h6>
          <ul style="padding-left: 20px;">
            <li v-for="v in vulns" :key="v.url + v.vulnName" style="margin: 8px 0;">
              <span style="color:#f8fafc;">{{ v.url }}</span> - <span style="color:#f8fafc;">{{ v.vulnName }}</span>
            </li>
            <li v-if="!vulns.length" style="color:#888;">暂无数据</li>
          </ul>
        </div>
      </div>

      <div class="right-report" style="flex: 1; min-width: 0; background: #1e293b; padding: 12px; border-radius: 6px; color: #fff;">
        <h6 style="margin-top: 0; color: #e2e8f0; font-size: 20px;">渗透测试报告</h6>
        <div 
          class="report-content markdown-content"
          style="overflow: auto; max-height: 600px; padding: 16px; background: #0f172a; border-radius: 4px; white-space: pre-wrap; font-family: 'Courier New', monospace; font-size: 14px; line-height: 1.5;"
          v-html="renderedReport || '暂无渗透测试报告，请输入URL并搜索相关历史记录'"
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
.left-vertical {
  flex: 0 0 380px;
  display: flex;
  flex-direction: column;
  gap: 18px;
}
.right-report {
  flex: 1;
  min-width: 0;
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
  box-sizing: border-box;
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
.right-report::-webkit-scrollbar {
  display: none;
}
.right-report h6, .tools-block h6, .vulns-block h6 {
  color: #8ab4f8;
  margin-bottom: 12px;
}
.report-content {
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
.markdown-content {
  color: #e2e8f0;
  line-height: 1.6;
  font-family: 'Consolas', monospace;
}
.markdown-content h1,
.markdown-content h2,
.markdown-content h3,
.markdown-content h4,
.markdown-content h5,
.markdown-content h6 {
  color: #60a5fa;
  margin: 10px 0 5px 0;
  font-size: 1.25rem;
  font-weight: bold;
}
.markdown-content p {
  margin: 5px 0;
}
.markdown-content code {
  background-color: #2d3748;
  padding: 2px 4px;
  border-radius: 3px;
  font-family: 'Consolas', monospace;
}
.markdown-content pre {
  background-color: #2d3748;
  padding: 10px;
  border-radius: 5px;
  overflow-x: auto;
  margin: 10px 0;
}
.markdown-content pre code {
  background-color: transparent;
  padding: 0;
}
.markdown-content ul,
.markdown-content ol {
  margin: 5px 0;
  padding-left: 20px;
}
.markdown-content li {
  margin: 2px 0;
}
.markdown-content blockquote {
  border-left: 3px solid #60a5fa;
  padding-left: 10px;
  margin: 10px 0;
  color: #a0aec0;
}
</style>