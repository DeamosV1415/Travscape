/**
 * Travescape AI Chat — Frontend Logic
 *
 * Handles:
 * - Firebase auth gating (login required)
 * - Real-time SSE streaming from /api/chat/stream
 * - Chat history (localStorage)
 * - Typewriter effect for AI responses
 */

// ==================== DOM ELEMENTS ====================

const authGate = document.getElementById('auth-gate');
const chatContainer = document.getElementById('chat-container');
const welcomeScreen = document.getElementById('welcome-screen');
const messagesContainer = document.getElementById('messages-container');
const messageInput = document.getElementById('message-input');
const sendBtn = document.getElementById('send-btn');
const typingIndicator = document.getElementById('typing-indicator');
const charCount = document.getElementById('char-count');
const newChatBtn = document.getElementById('new-chat-btn');
const historyList = document.getElementById('history-list');

// ==================== STATE ====================

let chats = JSON.parse(localStorage.getItem('travescape_chats')) || [];
let currentChatId = null;
let isStreaming = false;
let currentUserId = null;      // Firebase UID — set by auth check
let abortController = null;    // To cancel in-flight requests

// ==================== AUTH GATING ====================
// Wait for Firebase auth-handler.js to set window.currentUser()
// Poll until auth state is resolved (Firebase loads asynchronously)

let authCheckInterval = null;
let authCheckAttempts = 0;
const MAX_AUTH_CHECKS = 50; // 5 seconds max wait

function checkAuthState() {
  authCheckAttempts++;

  // window.currentUser is a function set by auth-handler.js
  if (typeof window.currentUser === 'function') {
    const user = window.currentUser();

    if (user) {
      // User is logged in — show chat
      currentUserId = user.uid;
      authGate.style.display = 'none';
      chatContainer.style.display = 'flex';
      messageInput.focus();
      clearInterval(authCheckInterval);
      return;
    }

    // If auth handler has loaded but user is null, they're not logged in.
    // But we need to wait a moment for Firebase to finish initializing.
    if (authCheckAttempts >= MAX_AUTH_CHECKS) {
      // Auth fully resolved — user is not logged in
      authGate.style.display = 'flex';
      chatContainer.style.display = 'none';
      clearInterval(authCheckInterval);
      return;
    }
  }

  // Auth handler hasn't loaded yet, or still initializing
  if (authCheckAttempts >= MAX_AUTH_CHECKS) {
    // Timeout — show login gate
    authGate.style.display = 'flex';
    chatContainer.style.display = 'none';
    clearInterval(authCheckInterval);
  }
}

// Start polling for auth state
authCheckInterval = setInterval(checkAuthState, 100);

// ==================== INPUT HANDLING ====================

messageInput.addEventListener('input', function () {
  this.style.height = 'auto';
  this.style.height = Math.min(this.scrollHeight, 150) + 'px';
  charCount.textContent = `${this.value.length}/2000`;
  sendBtn.disabled = this.value.trim().length === 0 || isStreaming;
});

messageInput.addEventListener('keydown', function (e) {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault();
    if (!isStreaming) sendMessage();
  }
});

sendBtn.addEventListener('click', () => {
  if (isStreaming) {
    // Stop generation
    if (abortController) abortController.abort();
  } else {
    sendMessage();
  }
});

function setStopMode() {
  sendBtn.disabled = false;
  sendBtn.innerHTML = '<i class="ri-stop-fill"></i>';
  sendBtn.classList.add('stop-mode');
}

function setSendMode() {
  sendBtn.innerHTML = '<i class="ri-send-plane-fill"></i>';
  sendBtn.classList.remove('stop-mode');
  sendBtn.disabled = messageInput.value.trim().length === 0;
}

// ==================== SUGGESTION BUTTONS ====================

document.querySelectorAll('.suggestion').forEach(btn => {
  btn.addEventListener('click', () => {
    messageInput.value = btn.dataset.query;
    messageInput.dispatchEvent(new Event('input'));
    if (!isStreaming) sendMessage();
  });
});

// ==================== SEND MESSAGE ====================

async function sendMessage() {
  const text = messageInput.value.trim();
  if (!text || !currentUserId) return;

  // Hide welcome, show messages
  welcomeScreen.classList.add('hidden');
  messagesContainer.classList.add('active');

  // Create chat if needed
  if (!currentChatId) {
    currentChatId = Date.now();
    chats.unshift({
      id: currentChatId,
      title: text.substring(0, 30) + (text.length > 30 ? '...' : ''),
      messages: []
    });
  }

  // Add user message to UI
  addMessage(text, 'user');
  saveMessage(text, 'user');

  // Clear input
  messageInput.value = '';
  messageInput.style.height = 'auto';
  charCount.textContent = '0/2000';
  isStreaming = true;
  setStopMode();

  // Show typing indicator with reset text
  const typingText = document.getElementById('typing-text');
  if (typingText) typingText.textContent = 'Trav is thinking...';
  typingIndicator.classList.add('active');
  scrollToBottom();

  // Stream AI response
  await streamAIResponse(text);
}

// ==================== SSE STREAMING ====================

async function streamAIResponse(userMessage) {
  let fullResponse = '';
  let msg = null;
  let bubble = null;
  abortController = new AbortController();

  // Status text cycling while waiting
  const typingTextEl = document.getElementById('typing-text');
  const statusMessages = ['Trav is thinking...', 'Searching for the best options...', 'Almost there...'];
  let statusIdx = 0;
  const statusInterval = setInterval(() => {
    statusIdx = Math.min(statusIdx + 1, statusMessages.length - 1);
    if (typingTextEl) typingTextEl.textContent = statusMessages[statusIdx];
  }, 5000);

  try {
    const response = await fetch('/api/chat/stream', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        message: userMessage,
        user_id: currentUserId
      }),
      signal: abortController.signal
    });

    if (!response.ok) {
      throw new Error(`Server error: ${response.status}`);
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = '';

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });

      // Process complete SSE lines from buffer
      const lines = buffer.split('\n');
      buffer = lines.pop() || '';

      for (const line of lines) {
        const trimmed = line.trim();
        if (!trimmed.startsWith('data: ')) continue;

        try {
          const data = JSON.parse(trimmed.substring(6));

          if (data.error) {
            fullResponse += `\n\n⚠️ Error: ${data.error}`;
            break;
          }

          if (data.done) break;

          if (data.content) {
            // Create the assistant bubble on FIRST content (not before)
            if (!msg) {
              clearInterval(statusInterval);
              typingIndicator.classList.remove('active');

              msg = document.createElement('div');
              msg.className = 'message assistant';
              msg.innerHTML = `
                <div class="message-avatar">
                  <i class="ri-compass-3-fill"></i>
                </div>
                <div class="message-content">
                  <div class="message-bubble"></div>
                  <div class="message-time">${getTime()}</div>
                </div>
              `;
              messagesContainer.appendChild(msg);
              bubble = msg.querySelector('.message-bubble');
            }

            fullResponse += data.content;

            // During streaming: hide everything from [FLIGHTS_START] onwards
            // (the JSON data is still arriving, don't show partial markers)
            let displayText = fullResponse;
            const markerIdx = displayText.indexOf('[FLIGHTS_START]');
            if (markerIdx !== -1) {
              displayText = displayText.substring(0, markerIdx);
            }

            bubble.innerHTML = formatResponse(displayText);
            scrollToBottom();
          }
        } catch (parseErr) {
          console.warn('Skipping malformed SSE line:', trimmed);
        }
      }
    }

    // FINAL render: now the full text is complete, process flight cards
    if (bubble && fullResponse) {
      bubble.innerHTML = formatResponse(fullResponse);
      scrollToBottom();
    }

    // If we never received content, hide the indicator
    if (!msg) {
      clearInterval(statusInterval);
      typingIndicator.classList.remove('active');
    }
  } catch (err) {
    clearInterval(statusInterval);
    typingIndicator.classList.remove('active');

    if (err.name === 'AbortError') {
      fullResponse += '\n\n_(Response cancelled)_';
    } else {
      console.error('Stream error:', err);
      fullResponse = fullResponse || `⚠️ Connection error. Please try again.\n\n_${err.message}_`;
    }

    // Create bubble for error if it doesn't exist
    if (!msg) {
      msg = document.createElement('div');
      msg.className = 'message assistant';
      msg.innerHTML = `
        <div class="message-avatar">
          <i class="ri-compass-3-fill"></i>
        </div>
        <div class="message-content">
          <div class="message-bubble"></div>
          <div class="message-time">${getTime()}</div>
        </div>
      `;
      messagesContainer.appendChild(msg);
      bubble = msg.querySelector('.message-bubble');
    }
    bubble.innerHTML = formatResponse(fullResponse);
  } finally {
    if (fullResponse) {
      saveMessage(fullResponse, 'assistant');
    }

    isStreaming = false;
    abortController = null;
    setSendMode();
    scrollToBottom();
  }
}

// ==================== MESSAGE RENDERING ====================

function addMessage(text, sender) {
  const msg = document.createElement('div');
  msg.className = `message ${sender}`;
  msg.innerHTML = `
    <div class="message-avatar">
      <i class="${sender === 'user' ? 'ri-user-3-fill' : 'ri-compass-3-fill'}"></i>
    </div>
    <div class="message-content">
      <div class="message-bubble">${formatResponse(text)}</div>
      <div class="message-time">${getTime()}</div>
    </div>
  `;
  messagesContainer.appendChild(msg);
  scrollToBottom();
}

/**
 * Strip leaked JSON state blocks from response text.
 * These come from structured output schemas leaking into chat.
 */
function stripJsonState(text) {
  const stateKeys = ['"user_request"', '"chatbot_reply"', '"need_clarification"', '"needs_clarification"'];
  let result = [];
  let i = 0;
  while (i < text.length) {
    if (text[i] === '{') {
      let depth = 1;
      let j = i + 1;
      while (j < text.length && depth > 0) {
        if (text[j] === '{') depth++;
        else if (text[j] === '}') depth--;
        j++;
      }
      const block = text.substring(i, j);
      if (stateKeys.some(k => block.includes(k))) {
        i = j;
        while (i < text.length && '\n\r '.includes(text[i])) i++;
        continue;
      } else {
        result.push(text[i]);
        i++;
      }
    } else {
      result.push(text[i]);
      i++;
    }
  }
  return result.join('').trim();
}

/**
 * Render flight cards from structured flight data.
 */
function renderFlightCards(flightsJson) {
  try {
    const itineraries = JSON.parse(flightsJson);
    if (!Array.isArray(itineraries) || itineraries.length === 0) return '';

    let html = '<div class="flight-cards-container">';
    html += '<div class="flight-cards-header"><i class="ri-flight-takeoff-line"></i> Available Flights</div>';

    itineraries.forEach((itin, idx) => {
      const flights = itin.flights || [];
      const firstFlight = flights[0] || {};
      const lastFlight = flights[flights.length - 1] || firstFlight;

      const airline = firstFlight.airline || 'Airline';
      const airlineLogo = firstFlight.airline_logo || '';
      const depCode = firstFlight.departure_airport_code || '---';
      const depTime = itin.departure_time || firstFlight.departure_time || '--:--';
      const arrCode = lastFlight.arrival_airport_code || '---';
      const arrTime = itin.arrival_time || lastFlight.arrival_time || '--:--';
      const duration = itin.duration_text || firstFlight.leg_duration_text || '';
      const price = itin.price;
      const stops = itin.stops;
      const flightNum = firstFlight.flight_number || '';

      // Format stops text
      let stopsText = 'Non-stop';
      if (stops === 1) stopsText = '1 stop';
      else if (stops > 1) stopsText = `${stops} stops`;

      // Format price
      let priceText = '';
      if (price != null) {
        priceText = typeof price === 'number'
          ? '₹' + price.toLocaleString('en-IN')
          : String(price);
      }

      // Multi-airline logos for connecting flights
      const airlineLogos = flights
        .map(f => f.airline_logo)
        .filter((v, i, a) => v && a.indexOf(v) === i);

      html += `
        <div class="flight-card" style="animation-delay: ${idx * 0.08}s">
          <div class="flight-card-top">
            <div class="flight-airline">
              ${airlineLogos.length > 0
                ? airlineLogos.map(logo => `<img src="${logo}" alt="" class="airline-logo" onerror="this.style.display='none'">`).join('')
                : '<i class="ri-plane-line airline-logo-fallback"></i>'}
              <div>
                <span class="airline-name">${airline}</span>
                ${flightNum ? `<span class="flight-number">${flightNum}</span>` : ''}
              </div>
            </div>
            ${priceText ? `<div class="flight-price">${priceText}</div>` : ''}
          </div>
          <div class="flight-route">
            <div class="flight-endpoint">
              <span class="flight-time">${depTime}</span>
              <span class="flight-code">${depCode}</span>
            </div>
            <div class="flight-path">
              <div class="flight-path-line">
                <span class="path-dot"></span>
                <span class="path-line-bar"></span>
                <i class="ri-plane-fill path-plane"></i>
                <span class="path-line-bar"></span>
                <span class="path-dot"></span>
              </div>
              <div class="flight-duration">${duration}</div>
              <div class="flight-stops ${stops === 0 ? 'nonstop' : ''}">${stopsText}</div>
            </div>
            <div class="flight-endpoint">
              <span class="flight-time">${arrTime}</span>
              <span class="flight-code">${arrCode}</span>
            </div>
          </div>
        </div>
      `;
    });

    html += '</div>';
    return html;
  } catch (e) {
    console.warn('Failed to render flight cards:', e);
    return '';
  }
}

/**
 * Format AI response text for display.
 * Proper markdown to HTML renderer for beautiful chat output.
 * Handles headers, dividers, lists, bold, italic, links, and flight cards.
 */
function formatResponse(text) {
  if (!text) return '';

  // Strip leaked JSON state blocks
  text = stripJsonState(text);

  // Extract and render flight data blocks
  let flightCardsHtml = '';
  text = text.replace(/\[FLIGHTS_START\]([\s\S]*?)\[FLIGHTS_END\]/g, (match, json) => {
    flightCardsHtml += renderFlightCards(json.trim());
    return '';
  });

  // Process line by line for block-level elements
  const lines = text.split('\n');
  let html = '';
  let inList = false;
  let listType = '';

  for (let i = 0; i < lines.length; i++) {
    let line = lines[i];

    // Horizontal rule: ---
    if (/^-{3,}\s*$/.test(line.trim())) {
      if (inList) { html += '</' + listType + '>'; inList = false; }
      html += '<hr>';
      continue;
    }

    // Headers: #### h4, ### h3, ## h2
    const h4Match = line.match(/^####\s+(.+)/);
    if (h4Match) {
      if (inList) { html += '</' + listType + '>'; inList = false; }
      html += '<h4>' + inlineFormat(h4Match[1]) + '</h4>';
      continue;
    }
    const h3Match = line.match(/^###\s+(.+)/);
    if (h3Match) {
      if (inList) { html += '</' + listType + '>'; inList = false; }
      html += '<h3>' + inlineFormat(h3Match[1]) + '</h3>';
      continue;
    }
    const h2Match = line.match(/^##\s+(.+)/);
    if (h2Match) {
      if (inList) { html += '</' + listType + '>'; inList = false; }
      html += '<h2>' + inlineFormat(h2Match[1]) + '</h2>';
      continue;
    }

    // Bullet list items: • or - at start
    const bulletMatch = line.match(/^\s*[•\-]\s+(.+)/);
    if (bulletMatch) {
      if (!inList || listType !== 'ul') {
        if (inList) html += '</' + listType + '>';
        html += '<ul>';
        inList = true;
        listType = 'ul';
      }
      html += '<li>' + inlineFormat(bulletMatch[1]) + '</li>';
      continue;
    }

    // Numbered list: 1. text
    const numMatch = line.match(/^\s*(\d+)\.\s+(.+)/);
    if (numMatch) {
      if (!inList || listType !== 'ol') {
        if (inList) html += '</' + listType + '>';
        html += '<ol>';
        inList = true;
        listType = 'ol';
      }
      html += '<li>' + inlineFormat(numMatch[2]) + '</li>';
      continue;
    }

    // Not a list item: close any open list
    if (inList) {
      html += '</' + listType + '>';
      inList = false;
    }

    // Empty line = spacing
    if (line.trim() === '') {
      html += '<br>';
      continue;
    }

    // Regular text
    html += '<p>' + inlineFormat(line) + '</p>';
  }

  if (inList) html += '</' + listType + '>';

  // Clean up excessive breaks and empty tags
  html = html.replace(/(<br>\s*){3,}/g, '<br>');
  html = html.replace(/<p>\s*<\/p>/g, '');

  return html + flightCardsHtml;
}

/**
 * Inline formatting: bold, italic, code, links.
 */
function inlineFormat(text) {
  return text
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    .replace(/(?<!\w)_(.*?)_(?!\w)/g, '<em>$1</em>')
    .replace(/`([^`]+)`/g, '<code>$1</code>')
    .replace(/\[([^\]]+)\]\((https?:\/\/[^\)]+)\)/g, '<a href="$2" target="_blank" rel="noopener">$1</a>');
}

// ==================== CHAT HISTORY ====================

function saveMessage(text, sender) {
  const chat = chats.find(c => c.id === currentChatId);
  if (chat) {
    chat.messages.push({ text, sender, time: new Date().toISOString() });
    localStorage.setItem('travescape_chats', JSON.stringify(chats));
    loadChatHistory();
  }
}

function loadChatHistory() {
  historyList.innerHTML = '';
  chats.forEach(chat => {
    const item = document.createElement('div');
    item.className = 'history-item';
    item.innerHTML = `
      <span>${chat.title}</span>
      <button class="delete-btn" data-id="${chat.id}"><i class="ri-delete-bin-line"></i></button>
    `;
    item.addEventListener('click', (e) => {
      if (!e.target.closest('.delete-btn')) loadChat(chat.id);
    });
    item.querySelector('.delete-btn').addEventListener('click', () => deleteChat(chat.id));
    historyList.appendChild(item);
  });
}

function loadChat(id) {
  const chat = chats.find(c => c.id === id);
  if (!chat) return;

  // Cancel any in-flight stream
  if (abortController) {
    abortController.abort();
  }

  currentChatId = id;
  welcomeScreen.classList.add('hidden');
  messagesContainer.classList.add('active');
  messagesContainer.innerHTML = '';

  chat.messages.forEach(m => addMessage(m.text, m.sender));
}

function deleteChat(id) {
  chats = chats.filter(c => c.id !== id);
  localStorage.setItem('travescape_chats', JSON.stringify(chats));
  if (currentChatId === id) {
    // Cancel any in-flight stream
    if (abortController) {
      abortController.abort();
    }
    currentChatId = null;
    messagesContainer.innerHTML = '';
    messagesContainer.classList.remove('active');
    welcomeScreen.classList.remove('hidden');
  }
  loadChatHistory();
}

// ==================== NEW CHAT ====================

newChatBtn.addEventListener('click', () => {
  // Cancel any in-flight stream
  if (abortController) {
    abortController.abort();
  }
  currentChatId = null;
  isStreaming = false;
  messagesContainer.innerHTML = '';
  messagesContainer.classList.remove('active');
  welcomeScreen.classList.remove('hidden');
  typingIndicator.classList.remove('active');
});

// ==================== UTILITIES ====================

function getTime() {
  return new Date().toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' });
}

function scrollToBottom() {
  setTimeout(() => {
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
  }, 50);
}

// ==================== INITIALIZE ====================

loadChatHistory();
