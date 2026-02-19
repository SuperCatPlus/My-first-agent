function addMessage(role, content) {
    const chatMessages = document.getElementById('chat-messages');
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${role}-message`;
    
    const now = new Date();
    const timeString = now.toLocaleTimeString();
    
    messageDiv.innerHTML = `
        <div class="message-content">${content}</div>
        <div class="message-time">${timeString}</div>
    `;
    
    chatMessages.appendChild(messageDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}



// 发送消息到后端API
// async function sendMessage(message) {
//     console.log('sendMessage 被调用，参数:', message);
//     console.log('message.trim():', message.trim());
//     if (!message.trim()) {
//         console.log('消息为空，返回');
//         return;
//     }

//     // 显示用户消息
//     addUserMessage(message);
//     userInput.value = '';
//     console.log("用户消息:"+ message)
//     try {
//         // 调用聊天API
//         const response = await fetch('/api/chat', {
//             method: 'POST',
//             headers: {
//                 'Content-Type': 'application/json'
//             },
//             body: JSON.stringify({ message: message })
//         });

//         if (!response.ok) {
//             throw new Error(`HTTP error! status: ${response.status}`);
//         }

//         const data = await response.json();

//         // 显示AI回复
//         if (data.error) {
//             addAIMessage(`❌ 错误: ${data.error}`);
//         } else {
//             addAIMessage(data.response);
//         }
//     } catch (error) {
//         console.error('发送消息失败:', error);
//         addAIMessage(`❌ 发送消息失败: ${error.message}`);
//     }
// }

// // 监听发送按钮点击
// if (sendBtn) {
//     sendBtn.addEventListener('click', () => {
//         console.log('发送按钮被点击，输入值:', userInput.value);
//         sendMessage(userInput.value);
//     });
// } else {
//     console.error('sendBtn 元素未找到！');
// }

// // 监听回车键发送（Shift+Enter换行）
// if (userInput) {
//     userInput.addEventListener('keydown', (e) => {
//         console.log('键盘事件:', e.key);
//         if (e.key === 'Enter' && !e.shiftKey) {
//             e.preventDefault();
//             console.log('回车键被按下，输入值:', userInput.value);
//             sendMessage(userInput.value);
//         }
//     });
// } else {
//     console.error('userInput 元素未找到！');
// }

function Dom_sendMessage() {
    const input = document.getElementById('userInput');
    const message = input.value.trim();

    if (message) {
        // 创建用户对话胶囊
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

        // 模拟生成文档（示例：将用户输入作为文档内容）
        renderAIDocument(`<h2>AI 生成文档</h2><p>生成时间：${new Date().toLocaleString()}</p><p>用户提问：${message}</p><p>这是 AI 根据你的提问生成的文档内容，你可以替换为实际的 AI 生成结果。</p>`);

        // 清空输入框
        input.value = '';

        // 滚动到底部
        chatMain.scrollTop = chatMain.scrollHeight;
    }
}