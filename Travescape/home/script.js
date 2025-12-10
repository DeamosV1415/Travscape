var body = document.querySelector("body");
var login = document.querySelector("#login");
var logincard = document.querySelector("#logincard");
var cross = document.querySelector("#cross");
var lbtn=document.querySelector("#l-btn");
var menubtn=document.querySelector("#icon");
var menu=document.querySelector("#menubar");
const scrollBox = document.getElementById("child2");
const leftArrow = document.getElementById("aleft");
const rightArrow = document.getElementById("aright");
var img1=[{img:"./imgs/img1/1.avif"},
    {img:"./imgs/img1/2.avif"},
    {img:"./imgs/img1/3.avif"},
    {img:"./imgs/img1/4.avif"},
    {img:"./imgs/img1/5.avif"},
    {img:"./imgs/img1/6.avif"},
    {img:"./imgs/img1/7.avif"},
    {img:"./imgs/img1/8.avif"},
    {img:"./imgs/img1/14.avif"},
    {img:"./imgs/img1/12.avif"},
    {img:"./imgs/img1/13.avif"},
    {img:"./imgs/img1/10.avif"},
    {img:"./imgs/img1/9.avif"},
    {img:"./imgs/img1/16.avif"},
    {img:"./imgs/img1/11.avif"},
    {img:"./imgs/img1/15.avif"}
];



function openOverlay(target) {
    closeAllOverlays();
    target.classList.add("show");
}

function closeAllOverlays() {
    menu.classList.remove("show");
    logincard.classList.remove("show");
}

login.addEventListener("click", () => openOverlay(logincard));
lbtn.addEventListener("click", () => {
    logincard.classList.add("show");  // show login
    // do NOT close menu
});
menubtn.addEventListener("click", () => openOverlay(menu));
cross.addEventListener("click", () => logincard.classList.remove("show"));
logincard.addEventListener("click", (e) => {
    if (e.target === logincard) logincard.classList.remove("show");
});
menu.addEventListener("click", (e) => {
    if (e.target === menu) menu.classList.remove("show");
});

function addimg(){
    var clutter="";
    img1.forEach(i => {
        clutter+=`<div class="card"><img src="${i.img}" alt=""></div>`
                  
    });
    console.log(clutter)

    document.querySelector(".group").innerHTML=clutter;
}
addimg();

function scrollbar(){
    let scrollInterval = null;

    function startScroll(direction) {
        scrollInterval = setInterval(() => {
            scrollBox.scrollLeft += direction * 18;
        }, 20);
    }

    function stopScroll() {
        clearInterval(scrollInterval);
        scrollInterval = null;
    }


    leftArrow.addEventListener("mousedown", () => startScroll(-1));
    rightArrow.addEventListener("mousedown", () => startScroll(1));

    document.addEventListener("mouseup", stopScroll);

    leftArrow.addEventListener("touchstart", () => startScroll(-1));
    rightArrow.addEventListener("touchstart", () => startScroll(1));

    document.addEventListener("touchend", stopScroll);


    const leftGlow = document.querySelector(".left-glow");
    const rightGlow = document.querySelector(".right-glow");

    function updateGlow() {
        const maxScroll = scrollBox.scrollWidth - scrollBox.clientWidth;

        if (scrollBox.scrollLeft <= 5) {
            leftGlow.style.opacity = "0";
        } else {
            leftGlow.style.opacity = "1";
        }

        if (scrollBox.scrollLeft >= maxScroll - 5) {
            rightGlow.style.opacity = "0";
        } else {
            rightGlow.style.opacity = "1";
        }
    }

    // Run on scroll
    scrollBox.addEventListener("scroll", updateGlow);

    // Run on load
    updateGlow();
}
scrollbar();

