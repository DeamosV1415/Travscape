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

        let optionAngle =
            angle + Math.abs(skewVal) + (90 - Math.abs(skewVal)) / 2;

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
// NEWS FETCHING & DISPLAY
// ===============================

const FALLBACK_IMAGE = "../home/card.jpg";

async function getApiKey() {
    try {
        const res = await fetch("../api_key");
        if (!res.ok) throw new Error("API key file not found");
        return (await res.text()).trim();
    } catch (error) {
        console.warn("Could not load API key:", error);
        return null;
    }
}

function createNewsCard(article) {
    const card = document.createElement("div");
    card.className = "news-card";

    // Use article image or fallback
    const imageUrl = article.image || FALLBACK_IMAGE;

    // Format date
    const date = new Date(article.publishedAt || article.date);
    const formattedDate = date.toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric'
    });

    card.innerHTML = `
        <img src="${imageUrl}" alt="${article.title}" class="news-card-image" onerror="this.src='${FALLBACK_IMAGE}'">
        <div class="news-card-content">
            <div class="news-card-source">${article.source?.name || article.category || 'Travel News'}</div>
            <h3 class="news-card-title">${article.title}</h3>
            <p class="news-card-description">${article.description || 'Click to read more about this story.'}</p>
            <div class="news-card-footer">
                <span class="news-card-date">${formattedDate}</span>
                <span class="news-card-read-more">
                    Read More <i class="ri-arrow-right-line"></i>
                </span>
            </div>
        </div>
    `;

    // Add click handler
    if (article.url) {
        card.onclick = () => window.open(article.url, "_blank");
    }

    return card;
}

document.addEventListener("DOMContentLoaded", async () => {

    const newsGrid = document.getElementById("newsGrid");
    const loadingState = document.getElementById("loadingState");

    if (!newsGrid) return;

    try {
        const API_KEY = await getApiKey();

        if (!API_KEY) {
            throw new Error("No API key available");
        }

        const query = "travel tourism destinations";
        const url = `https://gnews.io/api/v4/search?q=${query}&lang=en&max=9&apikey=${API_KEY}`;

        const res = await fetch(url);
        const data = await res.json();

        // Hide loading state
        if (loadingState) {
            loadingState.classList.add('hidden');
        }

        if (!data.articles || data.articles.length === 0) {
            throw new Error("No articles found");
        }

        // Add staggered animation delay
        data.articles.forEach((article, index) => {
            const card = createNewsCard(article);
            card.style.animationDelay = `${index * 0.1}s`;
            newsGrid.appendChild(card);
        });

    } catch (err) {
        console.warn("API failed, using fallback data", err);

        // Hide loading state
        if (loadingState) {
            loadingState.classList.add('hidden');
        }

        // Fallback news data
        const fallbackNews = [
            {
                category: "✈️ Travel & Tourism",
                title: "Global Travel Demand Surges to Record Highs in 2025",
                description: "International travel bookings have reached unprecedented levels as travelers seek new destinations and experiences around the world.",
                date: "2025-01-10",
                image: FALLBACK_IMAGE
            },
            {
                category: "🏝️ Destinations",
                title: "Top 10 Hidden Gems for Your Next Adventure",
                description: "Discover breathtaking destinations that remain off the beaten path, offering authentic experiences and stunning natural beauty.",
                date: "2025-01-08",
                image: FALLBACK_IMAGE
            },
            {
                category: "🎵 Events & Concerts",
                title: "Music Festivals Drive Tourism Boom Across Europe",
                description: "Major music tours and festivals are attracting millions of travelers, boosting local economies and creating unforgettable experiences.",
                date: "2025-01-06",
                image: FALLBACK_IMAGE
            },
            {
                category: "🌍 Sustainable Travel",
                title: "Eco-Friendly Travel Trends Reshaping the Industry",
                description: "More travelers are choosing sustainable options, from eco-lodges to carbon-neutral flights, as environmental awareness grows.",
                date: "2025-01-05",
                image: FALLBACK_IMAGE
            },
            {
                category: "🗺️ Travel Tips",
                title: "Expert Tips for Budget-Conscious Travelers in 2025",
                description: "Learn how to explore the world without breaking the bank with these insider tips from seasoned travelers and industry experts.",
                date: "2025-01-03",
                image: FALLBACK_IMAGE
            },
            {
                category: "🏨 Hospitality",
                title: "Luxury Hotels Unveil Innovative Guest Experiences",
                description: "The hospitality industry is embracing technology and personalization to create memorable stays for modern travelers.",
                date: "2025-01-01",
                image: FALLBACK_IMAGE
            }
        ];

        fallbackNews.forEach((item, index) => {
            const card = createNewsCard(item);
            card.style.animationDelay = `${index * 0.1}s`;
            newsGrid.appendChild(card);
        });
    }

});
