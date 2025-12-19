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




async function getApiKey() {
    const res = await fetch("../api_key");
    if (!res.ok) throw new Error("API key file not found");
    return (await res.text()).trim();  // .trim() will remove any trailing period or whitespace
}

document.addEventListener("DOMContentLoaded", async () => {

    const newsGrid = document.getElementById("newsGrid");
    if (!newsGrid) return;

    try {
        const API_KEY = await getApiKey();

        const query = "travel tourism concerts";
        const url = `https://gnews.io/api/v4/search?q=${query}&lang=en&max=6&apikey=${API_KEY}`;

        const res = await fetch(url);
        const data = await res.json();

        if (!data.articles || data.articles.length === 0) {
            throw new Error("No articles found");
        }

        data.articles.forEach(article => {
            const card = document.createElement("div");
            card.className = "news-card";

            card.innerHTML = `
                <div class="news-tag">${article.source.name}</div>
                <div class="news-title">${article.title}</div>
                <div class="news-date">
                    ${new Date(article.publishedAt).toDateString()}
                </div>
            `;

            card.onclick = () => window.open(article.url, "_blank");

            newsGrid.appendChild(card);
        });

    } catch (err) {
        console.warn("API failed, using fallback data", err);

        const fallbackNews = [
            {
                category: "✈️ Travel & Tourism",
                title: "Travel demand continues to rise globally",
                date: "2025-01-10"
            },
            {
                category: "🎵 Concerts",
                title: "Major music tours drive travel bookings",
                date: "2025-01-06"
            }
        ];

        fallbackNews.forEach(item => {
            const card = document.createElement("div");
            card.className = "news-card";

            card.innerHTML = `
                <div class="news-tag">${item.category}</div>
                <div class="news-title">${item.title}</div>
                <div class="news-date">${new Date(item.date).toDateString()}</div>
            `;

            newsGrid.appendChild(card);
        });
    }

});
