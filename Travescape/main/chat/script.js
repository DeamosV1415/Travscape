document.addEventListener("DOMContentLoaded", () => {
  const sectors = document.querySelectorAll(".sector");
  const options = document.querySelectorAll(".option");
  const menuBtn = document.querySelector("#menu");
  const menuOverlay = document.querySelector("#menuOverlay");

  // ✅ SAFETY CHECK
  if (!menuBtn || !menuOverlay) {
    console.error("Menu button or overlay not found!");
    return;
  }

  // ✅ CALCULATE SECTOR POSITIONS
  const totalSectors = sectors.length;
  const skewVal = 360 / totalSectors - 90;

  let deviation = 0;
  if ((totalSectors / 2) % 2 !== 0) {
    deviation = 360 / totalSectors / 2;
  }

  sectors.forEach((sector, index) => {
    const angle = (360 / totalSectors) * (index + 1) - deviation;
    const optionAngle = angle + Math.abs(skewVal) + (90 - Math.abs(skewVal)) / 2;

    options[index].style.transform =
      `rotateZ(${optionAngle}deg) translateY(-140px) rotate(-${optionAngle}deg)`;

    sector.style.transform = `rotate(${angle}deg) skew(${skewVal}deg)`;
  });

  // ✅ TOGGLE MENU ON HAMBURGER CLICK
  menuBtn.addEventListener("click", (e) => {
    e.stopPropagation();
    menuOverlay.classList.toggle("show");
  });

  // ✅ CLOSE MENU ON OVERLAY CLICK (OUTSIDE THE CIRCULAR MENU)
  menuOverlay.addEventListener("click", (e) => {
    // Close only if clicking the dark overlay, not the menu itself
    if (e.target === menuOverlay) {
      menuOverlay.classList.remove("show");
    }
  });

  // ✅ CLOSE MENU ON ESC KEY
  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape" && menuOverlay.classList.contains("show")) {
      menuOverlay.classList.remove("show");
    }
  });

  // ✅ CLOSE MENU WHEN ANY MENU LINK IS CLICKED
  const menuLinks = menuOverlay.querySelectorAll(".menu a");
  menuLinks.forEach(link => {
    link.addEventListener("click", () => {
      menuOverlay.classList.remove("show");
    });
  });
});

// ============================================
// CHAT DROPDOWN FUNCTIONALITY
// ============================================

let chats = JSON.parse(localStorage.getItem('chats')) || [];
let currentChatId = null;

// ✅ TOGGLE CHAT DROPDOWN
function toggleChatMenu() {
  const chatMenu = document.getElementById('chatMenu');

  if (chatMenu.classList.contains('active')) {
    chatMenu.classList.remove('active');
    chatMenu.classList.add('hide');

    setTimeout(() => {
      chatMenu.classList.remove('hide');
    }, 400);
  } else {
    chatMenu.classList.add('active');
    loadPreviousChats();
  }
}

// ✅ CREATE NEW CHAT
function newChat() {
  const chatId = Date.now();
  const newChatObj = {
    id: chatId,
    title: `Chat ${chats.length + 1}`,
    timestamp: new Date().toISOString(),
    messages: []
  };

  chats.unshift(newChatObj);
  localStorage.setItem('chats', JSON.stringify(chats));

  currentChatId = chatId;
  loadPreviousChats();

  // You can add your logic here to clear the chat interface
  console.log('New chat created:', chatId);
}

// ✅ LOAD PREVIOUS CHATS INTO DROPDOWN
function loadPreviousChats() {
  const prevChatsContainer = document.getElementById('prevChats');
  prevChatsContainer.innerHTML = '';

  chats.forEach(chat => {
    const li = document.createElement('li');
    li.className = 'chat-item';
    li.innerHTML = `
            <span onclick="loadChat(${chat.id})">${chat.title}</span>
            <i class="ri-delete-bin-line del" onclick="deleteChat(${chat.id})"></i>
        `;
    prevChatsContainer.appendChild(li);
  });
}

// ✅ LOAD SPECIFIC CHAT
function loadChat(chatId) {
  currentChatId = chatId;
  const chat = chats.find(c => c.id === chatId);

  if (chat) {
    console.log('Loading chat:', chat);
    // Add your logic here to display the chat messages
    toggleChatMenu(); // Close the dropdown
  }
}

// ✅ DELETE CHAT
function deleteChat(chatId) {
  event.stopPropagation();

  chats = chats.filter(c => c.id !== chatId);
  localStorage.setItem('chats', JSON.stringify(chats));

  if (currentChatId === chatId) {
    currentChatId = null;
  }

  loadPreviousChats();
}

// ✅ CLOSE CHAT MENU WHEN CLICKING OUTSIDE
document.addEventListener('click', (e) => {
  const chatMenu = document.getElementById('chatMenu');
  const chatBtn = document.getElementById('n1_h2');

  if (chatMenu && chatBtn &&
    !chatMenu.contains(e.target) &&
    !chatBtn.contains(e.target) &&
    chatMenu.classList.contains('active')) {
    toggleChatMenu();
  }
});

// ============================================
// CHAT INTERFACE FUNCTIONALITY
// ============================================

const messageInput = document.getElementById('messageInput');
const sendBtn = document.getElementById('sendBtn');
const messagesContainer = document.getElementById('messagesContainer');
const welcomeScreen = document.getElementById('welcomeScreen');
const typingIndicator = document.getElementById('typingIndicator');
const charCount = document.getElementById('charCount');

// ✅ AUTO-RESIZE TEXTAREA
messageInput?.addEventListener('input', function () {
  this.style.height = 'auto';
  this.style.height = Math.min(this.scrollHeight, 150) + 'px';

  // Update character count
  if (charCount) {
    charCount.textContent = `${this.value.length}/2000`;
  }

  // Enable/disable send button
  if (sendBtn) {
    sendBtn.disabled = this.value.trim().length === 0;
  }
});

// ✅ SEND MESSAGE ON ENTER (Shift+Enter for new line)
messageInput?.addEventListener('keydown', function (e) {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault();
    sendMessage();
  }
});

// ✅ SEND MESSAGE FUNCTION
function sendMessage() {
  const message = messageInput?.value.trim();

  if (!message) return;

  // Hide welcome screen on first message
  if (welcomeScreen && !welcomeScreen.classList.contains('hidden')) {
    welcomeScreen.classList.add('hidden');
  }

  // Add user message
  addMessage(message, 'user');

  // Clear input
  messageInput.value = '';
  messageInput.style.height = 'auto';
  if (charCount) charCount.textContent = '0/2000';
  if (sendBtn) sendBtn.disabled = true;

  // Show typing indicator
  showTypingIndicator();

  // Simulate AI response (replace with actual API call)
  setTimeout(() => {
    hideTypingIndicator();
    const responses = [
      "That's a great question! Let me help you plan the perfect trip. 🌍",
      "I'd be happy to assist you with that! Here are some recommendations...",
      "Excellent choice! Let me share some insider tips for your journey.",
      "I can definitely help you with that. Here's what I suggest...",
      "Great idea! Let me provide you with some detailed information."
    ];
    const randomResponse = responses[Math.floor(Math.random() * responses.length)];
    addMessage(randomResponse, 'assistant');
  }, 1500 + Math.random() * 1000);
}

// ✅ ADD MESSAGE TO CHAT
function addMessage(text, sender) {
  if (!messagesContainer) return;

  const messageDiv = document.createElement('div');
  messageDiv.className = `message ${sender}`;

  const avatar = document.createElement('div');
  avatar.className = 'message-avatar';
  avatar.innerHTML = sender === 'user'
    ? '<i class="ri-user-3-fill"></i>'
    : '<i class="ri-robot-2-fill"></i>';

  const contentDiv = document.createElement('div');
  contentDiv.className = 'message-content';

  const bubble = document.createElement('div');
  bubble.className = 'message-bubble';
  bubble.textContent = text;

  const time = document.createElement('div');
  time.className = 'message-time';
  time.textContent = getCurrentTime();

  contentDiv.appendChild(bubble);
  contentDiv.appendChild(time);
  messageDiv.appendChild(avatar);
  messageDiv.appendChild(contentDiv);

  messagesContainer.appendChild(messageDiv);

  // Smooth scroll to bottom
  setTimeout(() => {
    messagesContainer.scrollTo({
      top: messagesContainer.scrollHeight,
      behavior: 'smooth'
    });
  }, 100);
}

// ✅ SHOW TYPING INDICATOR
function showTypingIndicator() {
  if (typingIndicator) {
    typingIndicator.classList.add('active');

    // Scroll to show typing indicator
    setTimeout(() => {
      if (messagesContainer) {
        messagesContainer.scrollTo({
          top: messagesContainer.scrollHeight,
          behavior: 'smooth'
        });
      }
    }, 100);
  }
}

// ✅ HIDE TYPING INDICATOR
function hideTypingIndicator() {
  if (typingIndicator) {
    typingIndicator.classList.remove('active');
  }
}

// ✅ GET CURRENT TIME
function getCurrentTime() {
  const now = new Date();
  return now.toLocaleTimeString('en-US', {
    hour: '2-digit',
    minute: '2-digit',
    hour12: true
  });
}


// ✅ INITIALIZE SEND BUTTON STATE
if (sendBtn) {
  sendBtn.disabled = true;
}

// ✅ FOCUS INPUT ON LOAD
window.addEventListener('load', () => {
  if (messageInput) {
    messageInput.focus();
  }
});
