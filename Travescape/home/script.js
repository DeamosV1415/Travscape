var body = document.querySelector("body");

var img_arr = [
    { img: "./imgs/img1/1.avif" }, { img: "./imgs/img1/2.avif" },
    { img: "./imgs/img1/3.avif" }, { img: "./imgs/img1/4.avif" },
    { img: "./imgs/img1/5.avif" }, { img: "./imgs/img1/6.avif" },
    { img: "./imgs/img1/7.avif" }, { img: "./imgs/img1/8.avif" },
    { img: "./imgs/img1/9.avif" }, { img: "./imgs/img1/10.avif" },
    { img: "./imgs/img1/11.avif" }, { img: "./imgs/img1/12.avif" },
    { img: "./imgs/img1/13.avif" }, { img: "./imgs/img1/14.avif" }
]



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
let clutter = "";

img_arr.forEach(i => {
    clutter += `<img class="photo" src="${i.img}" alt="">`;
});

document.querySelector(".trip-photo").innerHTML = clutter + clutter;
function enableCardScroll() {

    const cards = document.querySelectorAll("#chatbot .card");

    cards.forEach(card => {

        /* --- touch swipe scrolling --- */
        let startY = 0;
        let scrollTop = 0;

        card.addEventListener("touchstart", e => {
            startY = e.touches[0].pageY;
            scrollTop = card.scrollTop;
        });

        card.addEventListener("touchmove", e => {
            const y = e.touches[0].pageY;
            const walk = startY - y;
            card.scrollTop = scrollTop + walk;
        });

        /* --- mouse wheel support --- */
        card.addEventListener("wheel", e => {
            card.scrollTop += e.deltaY;
            e.preventDefault();
        });

    });

}

document.addEventListener("DOMContentLoaded", enableCardScroll);
