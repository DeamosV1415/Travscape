var body = document.querySelector("body");
var login = document.querySelector("#log-btn");
var logincard = document.querySelector("#logincard");


function openOverlay(target) {
    closeAllOverlays();
    target.classList.add("show");
}

function closeAllOverlays() {
    logincard.classList.remove("show");
}

login.addEventListener("click", () => openOverlay(logincard));
logincard.addEventListener("click", (e) => {
    if (e.target === logincard) logincard.classList.remove("show");
});

