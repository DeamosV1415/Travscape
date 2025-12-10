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
