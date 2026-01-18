document.addEventListener("DOMContentLoaded", () => {
  let sectors = document.querySelectorAll(".sector");
  let options = document.querySelectorAll(".option");
  const menuBtn = document.querySelector("#menu");
  const menuOverlay = document.querySelector("#menuOverlay");

  // ✅ SAFETY CHECK
  if (!menuBtn || !menuOverlay) {
    console.error("Menu button or overlay not found!");
    return;
  }

  const totalSectors = sectors.length;
  const skewVal = 360 / totalSectors - 90;

  let deviation = 0;
  if ((totalSectors / 2) % 2 !== 0) {
    deviation = 360 / totalSectors / 2;
  }

  sectors.forEach((sector, index) => {
    const angle = (360 / totalSectors) * (index + 1) - deviation;

    let optionAngle = angle + Math.abs(skewVal) + (90 - Math.abs(skewVal)) / 2;

    options[index].style.transform =
      `rotateZ(${optionAngle}deg) translateY(-140px) rotate(-${optionAngle}deg)`;

    sector.style.transform = `rotate(${angle}deg) skew(${skewVal}deg)`;
  });

  // ✅ OPEN MENU
  menuBtn.addEventListener("click", (e) => {
    e.stopPropagation();
    menuOverlay.classList.add("show");
  });

  // ✅ CLOSE MENU ON OUTSIDE CLICK
  menuOverlay.addEventListener("click", (e) => {
    if (e.target === menuOverlay) {
      menuOverlay.classList.remove("show");
    }
  });

  // ✅ ESC KEY CLOSE
  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape") {
      menuOverlay.classList.remove("show");
    }
  });
});

// ===============================
// CHAT INPUT BEHAVIOR & STREAMING
// ===============================

const textarea = document.getElementById("userInput");
const sendBtn = document.getElementById("sendBtn");
const chatbox = document.querySelector(".chatbox");
const welcomeSection = document.querySelector(".welcome");

// ⭐ Generate a unique user ID (persists across page refreshes)
let userId = localStorage.getItem("trav_user_id");
if (!userId) {
  userId = "user_" + Math.random().toString(36).substring(2, 15);
  localStorage.setItem("trav_user_id", userId);
}
console.log("User ID:", userId);

if (textarea) {
  textarea.addEventListener("input", () => {
    textarea.style.height = "auto";
    textarea.style.height = textarea.scrollHeight + "px";
  });

  textarea.addEventListener("keydown", (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  });
}

if (sendBtn) {
  sendBtn.addEventListener("click", sendMessage);
}

function appendMessage(role, content = "") {
  // Hide welcome section on first message
  if (welcomeSection && welcomeSection.style.display !== "none") {
    welcomeSection.style.display = "none";
  }

  const msgDiv = document.createElement("div");
  msgDiv.className = `message ${role}-message`;

  const contentDiv = document.createElement("div");
  contentDiv.className = "message-content";
  contentDiv.innerText = content;

  msgDiv.appendChild(contentDiv);

  // Insert before the input wrapper to keep input at the bottom
  const inputWrapper = document.querySelector(".chat-input-wrapper");
  chatbox.insertBefore(msgDiv, inputWrapper);

  // Scroll to bottom
  chatbox.scrollTop = chatbox.scrollHeight;

  return contentDiv;
}

async function sendMessage() {
  const message = textarea.value.trim();
  if (!message) return;

  // Disable input while processing
  textarea.disabled = true;
  sendBtn.disabled = true;

  // Add user message to UI
  appendMessage("user", message);

  // Clear input
  textarea.value = "";
  textarea.style.height = "auto";

  // Add placeholder for AI response
  const aiContentDiv = appendMessage("ai", "");
  let fullResponse = "";

  try {
    // ⭐ Connect to FastAPI streaming endpoint
    const response = await fetch("http://localhost:8000/chat/stream", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        message: message,
        user_id: userId, // ⭐ Use persistent user ID
      }),
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder();

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      const chunk = decoder.decode(value, { stream: true });
      const lines = chunk.split("\n");

      for (const line of lines) {
        if (line.startsWith("data: ")) {
          const data = line.slice(6).trim();

          // Skip empty data
          if (!data) continue;

          try {
            const parsed = JSON.parse(data);

            // ⭐ Check for content (changed from 'token' to 'content')
            if (parsed.content) {
              fullResponse += parsed.content;
              aiContentDiv.innerText = fullResponse;

              // Keep scrolling to bottom as text grows
              chatbox.scrollTop = chatbox.scrollHeight;
            }

            // ⭐ Check if streaming is done
            if (parsed.done) {
              break;
            }

            // ⭐ Handle errors from backend
            if (parsed.error) {
              throw new Error(parsed.error);
            }
          } catch (parseError) {
            console.warn("Failed to parse SSE data:", data, parseError);
          }
        }
      }
    }

    // If no response was received, show a message
    if (!fullResponse.trim()) {
      aiContentDiv.innerText = "No response received from the agent.";
    }
  } catch (error) {
    console.error("Streaming error:", error);
    aiContentDiv.innerText = `Error: ${error.message}. Please check if the backend is running on http://localhost:8000`;
  } finally {
    // Re-enable input
    textarea.disabled = false;
    sendBtn.disabled = false;
    textarea.focus();
  }
}

// ⭐ Optional: Add a reset button functionality
function resetConversation() {
  // Clear the chat
  const messages = chatbox.querySelectorAll(".message");
  messages.forEach((msg) => msg.remove());

  // Show welcome section again
  if (welcomeSection) {
    welcomeSection.style.display = "flex";
  }

  // Call backend reset endpoint
  fetch(`http://localhost:8000/reset/${userId}`, {
    method: "POST",
  })
    .then((response) => response.json())
    .then((data) => console.log("Conversation reset:", data))
    .catch((error) => console.error("Reset error:", error));
}
