const app = document.getElementById('app');
const termPanel = document.getElementById('term-panel');
const resizer = document.getElementById('resizer');
let isPinned = false;

// --- 1. 固定逻辑 ---
function togglePin() {
    isPinned = !isPinned;
    app.classList.toggle('is-pinned', isPinned);
}

// --- 右侧栏开关 ---
let term;
function toggleTerm(e) {
    // 误删！！！防止快速点击导致的拖蓝
    if (e) e.preventDefault();
    const isOpen = termPanel.classList.toggle('open');
    const fab = document.getElementById('fab');
    fab.classList.toggle('active');

    if (isOpen) {
        // 1. 计算最终宽度
        const finalWidth = '45vw';

        // 2. 立即准备内容（在动画开始前）
        // 初始化终端（仅第一次打开时且 Terminal 存在）
        if (!term && typeof Terminal !== 'undefined') {
            term = new Terminal({ cursorBlink: true, theme: { background: '#000' } });
            term.open(document.getElementById('terminal-box'));
            term.write('\x1b[34mAI-OS Terminal\x1b[0m\r\n$ ');
        }

        // 确保 iframe 正确加载
        const iframe = document.querySelector('.iframe-web-terminal');
        if (iframe && !iframe.src) {
            iframe.src = 'WebSHell';
        }

        // 3. 执行动画
        // 当面板打开时，先移除内联样式，再触发过渡
        termPanel.style.width = '';
        setTimeout(() => {
            // 强制重排，确保过渡效果正常触发
            termPanel.offsetHeight;
            termPanel.style.width = finalWidth;

            // 4. 动画完成后聚焦终端并确保内容适应
            setTimeout(() => {
                // 聚焦到终端（如果当前选中的是终端标签且终端存在）
                if (document.querySelector('.tab-btn.active').dataset.tab === 'terminal' && term) {
                    term?.focus();
                }

                // 确保终端适应新尺寸
                if (term && typeof Terminal !== 'undefined' && term.fit) term.fit();
            }, 600);
        }, 10);
    } else {
        // 当面板关闭时，先设置宽度为0，再移除内联样式
        termPanel.style.width = '0';
        setTimeout(() => {
            termPanel.style.width = '';
        }, 600);
    }
}

// --- 3. 选项卡切换逻辑 ---
const tabBtns = document.querySelectorAll('.tab-btn');
tabBtns.forEach(btn => {
    btn.addEventListener('click', () => {
        // 移除所有激活状态
        tabBtns.forEach(b => b.classList.remove('active'));
        document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));

        // 激活当前选项卡
        const tabName = btn.dataset.tab;
        btn.classList.add('active');
        document.getElementById(`${tabName}-content`).classList.add('active');

        // 如果切换到终端，聚焦终端
        if (tabName === 'terminal' && term && typeof Terminal !== 'undefined') {
            term.focus();
        }
    });
});

// --- 4. 核心拖拽逻辑 ---
let isDragging = false;
const iframe = document.querySelector('.iframe-web-terminal');

resizer.addEventListener('mousedown', (e) => {
    if (!termPanel.classList.contains('open')) return;
    e.preventDefault(); // 阻止默认行为，避免选择文本
    isDragging = true;
    resizer.classList.add('dragging');
    document.body.style.cursor = 'col-resize';
    document.body.style.userSelect = 'none'; // 禁止文本选择

    // 拖拽时降低 iframe 透明度，减少重绘开销
    if (iframe) {
        iframe.style.opacity = '0.5';
        iframe.style.pointerEvents = 'none'; // 禁用 iframe 交互
    }
});

document.addEventListener('mousemove', (e) => {
    if (!isDragging) return;

    // 使用 requestAnimationFrame 优化性能
    requestAnimationFrame(() => {
        // 计算面板宽度：屏幕总宽 - 鼠标当前位置
        let newWidth = window.innerWidth - e.clientX;

        // 限制最小/最大宽度
        if (newWidth > 200 && newWidth < window.innerWidth * 0.7) {
            termPanel.style.width = newWidth + 'px';
            // 通知 xterm 重新适配 (如果有 fit addon)
            if (term && term.fit) term.fit();
        }
    });
});

document.addEventListener('mouseup', () => {
    if (isDragging) {
        isDragging = false;
        resizer.classList.remove('dragging');
        document.body.style.cursor = 'default';
        document.body.style.userSelect = ''; // 恢复文本选择

        // 拖拽结束后恢复 iframe
        if (iframe) {
            iframe.style.opacity = '1';
            iframe.style.pointerEvents = 'auto';
        }
    }
});

// 处理鼠标离开窗口的情况
document.addEventListener('mouseleave', () => {
    if (isDragging) {
        isDragging = false;
        resizer.classList.remove('dragging');
        document.body.style.cursor = 'default';
        document.body.style.userSelect = '';

        // 拖拽结束后恢复 iframe
        if (iframe) {
            iframe.style.opacity = '1';
            iframe.style.pointerEvents = 'auto';
        }
    }
});


//  监听来自iframe的消息
window.addEventListener('message', function (event) {
    if (event.data && event.data.type === 'loginSuccess') {
        //  更新终端标签文本
        const terminalTab = document.querySelector('.tab-btn[data-tab="terminal"]');
        if (terminalTab) {
            //  保留关闭按钮，只更新文本部分
            const tabContent = terminalTab.innerHTML;
            const newTabContent = tabContent.replace(/[^<]+(?=\s*<span class="tab-close">)/, event.data.terminalName);
            terminalTab.innerHTML = newTabContent;
        }
    }
});

// ==== 2.聊天功能 ====
const userInput = document.getElementById('userInput');
const sendBtn = document.getElementById('sendBtn');
const chatMain = document.querySelector('.chat-main');

// dbug：检查元素是否存在
// console.log('聊天功能初始化:');
// console.log('userInput:', userInput);
// console.log('sendBtn:', sendBtn);
// console.log('chatMain:', chatMain);

// --- 2.1 聊天功能base ---
// 滚动条显示逻辑
let scrollTimeout;

chatMain.addEventListener('scroll', () => {
    // 显示滚动条
    chatMain.classList.add('scrolling');

    // 清除之前的定时器
    clearTimeout(scrollTimeout);

    // 300毫秒后隐藏滚动条
    scrollTimeout = setTimeout(() => {
        chatMain.classList.remove('scrolling');
    }, 300);
});

// 滚动到底部
function scrollToBottom() {
    chatMain.scrollTop = chatMain.scrollHeight;
}

// HTML转义，防止XSS攻击
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// --- 2.2 胶囊渲染 ---
// 添加用户消息到聊天界面
// function addUserMessage(message) {
//     const messageContainer = document.createElement('div');
//     messageContainer.className = 'message-container';
//     messageContainer.innerHTML = `<div class="user-msg">${escapeHtml(message)}</div>`;
//     chatMain.appendChild(messageContainer);
//     scrollToBottom();
// }

// 渲染AI回复渲染
function addAIMessage(message) {
    const messageContainer = document.createElement('div');
    messageContainer.className = 'message-container';
    messageContainer.innerHTML = `<div class="ai-msg">${message}</div>`;
    chatMain.appendChild(messageContainer);
    scrollToBottom();
}

//  渲染用户胶囊
function addUserMessage(message) {
    const chatMain = document.querySelector('.chat-main');
    const messageContainer = document.createElement('div');
    messageContainer.className = 'message-container';
    messageContainer.style.display = 'flex';
    messageContainer.style.justifyContent = 'flex-end';

    const userMsgWrapper = document.createElement('div');
    userMsgWrapper.style.maxWidth = '80%';

    const userMsg = document.createElement('div');
    userMsg.className = 'user-msg';
    userMsg.textContent = message;

    userMsgWrapper.appendChild(userMsg);
    messageContainer.appendChild(userMsgWrapper);
    chatMain.appendChild(messageContainer);
}

//--- 2.3 对话逻辑 ---
//  发送消息逻辑
document.getElementById('sendBtn').addEventListener('click', sendMessage);
document.getElementById('userInput').addEventListener('keypress', function (e) {
    if (e.key === 'Enter') {
        sendMessage();
    }
});


//  发送消息逻辑
function sendMessage() {
    const input = document.getElementById('userInput');
    const sendButton = document.getElementById('sendBtn');
    const message = input.value.trim();

    if (message) {
        addUserMessage(message);
        
        // 模拟生成文档（示例：将用户输入作为文档内容）
        // renderAIDocument(`<h2>AI 生成文档</h2><p>生成时间：${new Date().toLocaleString()}</p><p>用户提问：${message}</p><p>这是 AI 根据你的提问生成的文档内容，你可以替换为实际的 AI 生成结果。</p>`);

        // 清空输入框
        input.value = '';

        // 禁用发送按钮，防止重复发送
        sendButton.disabled = true;
        sendButton.textContent = '发送中...';

        fetch('/api/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ 
                message: message
            })
        })
        .then(response => response.json())
        .then(data => {
            // 添加助手回复到界面
            addAIMessage(data.response);
            
            // 检查是否有终端命令需要执行
            if (data.terminal_commands && data.terminal_commands.length > 0) {
                console.log('收到终端命令:', data.terminal_commands);
                
                // 依次执行终端命令
                executeTerminalCommands(data.terminal_commands);
            }
        })
        .catch(error => {
            console.error('Error:', error);
            addAIMessage('抱歉，处理请求时出错了。');
        })
        .finally(() => {
            // 启用发送按钮
            sendButton.disabled = false;
            sendButton.textContent = '发送';
        });
        
        // 滚动到底部
        chatMain.scrollTop = chatMain.scrollHeight;
    }
}



// --- 新增：渲染AI文档的函数 ---
function renderAIDocument(content) {
    const docContent = document.querySelector('.document-content');
    docContent.innerHTML = content;

    // 自动切换到文档标签（可选）
    // tabBtns[1].click();
}

// --- 5. 终端控制功能 ---
/**
 * 向终端输入命令（模拟打字）
 * @param {string} command - 要输入的命令文本
 * @param {Object} options - 配置选项
 * @param {number} options.speed - 打字速度（毫秒/字符），默认为30ms
 * @param {boolean} options.enter - 是否自动按回车键执行命令，默认为true
 * @returns {boolean} 是否成功发送指令
 * 
 * @example
 * // 基本用法：输入命令并自动执行
 * typeToTerminal('ls -la');
 * 
 * @example
 * // 自定义打字速度，不自动执行
 * typeToTerminal('echo hello', { speed: 100, enter: false });
 * 
 * @example
 * // 快速输入
 * typeToTerminal('cat file.txt', { speed: 10 });
 */
function typeToTerminal(command, options = {}) {
    const { speed = 30, enter = true } = options;

    const iframe = document.querySelector('.iframe-web-terminal');
    if (iframe && iframe.contentWindow) {
        iframe.contentWindow.postMessage({
            type: 'typeCommand',
            text: command,
            speed: speed,
            enter: enter
        }, '*');
        return true;
    } else {
        console.error('未找到终端iframe');
        return false;
    }
}

/**
 * 向终端发送特殊按键
 * @param {string} key - 按键名称，支持：'Enter', 'Ctrl+C', 'Ctrl+D', 'Ctrl+Z'
 * @returns {boolean} 是否成功发送
 * 
 * @example
 * // 按回车键
 * sendKeyToTerminal('Enter');
 * 
 * @example
 * // 中断当前命令
 * sendKeyToTerminal('Ctrl+C');
 */
function sendKeyToTerminal(key) {
    const iframe = document.querySelector('.iframe-web-terminal');
    if (iframe && iframe.contentWindow) {
        iframe.contentWindow.postMessage({
            type: 'sendKey',
            key: key
        }, '*');
        return true;
    } else {
        console.error('未找到终端iframe');
        return false;
    }
}

// 导出到全局作用域，方便大模型调用
window.typeToTerminal = typeToTerminal;
window.sendKeyToTerminal = sendKeyToTerminal;

// --- 6. 终端命令执行 ---
/**
 * 执行终端命令列表
 * @param {Array} commands - 终端命令列表
 */
async function executeTerminalCommands(commands) {
    for (const cmd of commands) {
        if (cmd.type === 'command') {
            typeToTerminal(cmd.text, {
                speed: cmd.speed || 30,
                enter: cmd.enter !== false
            });
            console.log(`执行命令: ${cmd.text}`);
        } else if (cmd.type === 'key') {
            sendKeyToTerminal(cmd.key);
            console.log(`发送按键: ${cmd.key}`);
        }
        
        // 命令之间添加延迟，避免执行过快
        await new Promise(resolve => setTimeout(resolve, 500));
    }
}