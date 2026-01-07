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