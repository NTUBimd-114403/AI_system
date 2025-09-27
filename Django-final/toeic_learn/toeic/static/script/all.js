// 獲取當前頁面的網址
const currentPage = window.location.pathname.split("/").pop();
    
// 選取所有導航按鈕
const navLinks = document.querySelectorAll(".nav-buttons a");

navLinks.forEach(link => {
    // 取得按鈕的 href
    const page = link.getAttribute("href");
    if (page === currentPage) {
        link.querySelector(".nav-btn").classList.add("current");
    }
});

document.addEventListener("DOMContentLoaded", function () {
    const carouselImages = document.getElementById("carousel-images");
    const images = document.querySelectorAll(".carousel-image");
    const prevBtn = document.getElementById("prevBtn");
    const nextBtn = document.getElementById("nextBtn");

    let currentIndex = 0;
    const totalImages = images.length;
    const imageWidth = images[0].clientWidth; // 取得圖片寬度

    function updateCarousel() {
        carouselImages.style.transform = `translateX(${-currentIndex * imageWidth}px)`;
    }

    function nextSlide() {
        currentIndex = (currentIndex + 1) % totalImages;
        updateCarousel();
    }

    function prevSlide() {
        currentIndex = (currentIndex - 1 + totalImages) % totalImages;
        updateCarousel();
    }

    // 自動輪播
    let autoPlay = setInterval(nextSlide, 3000);

    // 按鈕點擊事件
    nextBtn.addEventListener("click", function () {
        clearInterval(autoPlay); // 停止自動輪播
        nextSlide();
        autoPlay = setInterval(nextSlide, 1000); // 重新啟動輪播
    });

    prevBtn.addEventListener("click", function () {
        clearInterval(autoPlay); // 停止自動輪播
        prevSlide();
        autoPlay = setInterval(nextSlide, 1000); // 重新啟動輪播
    });

    // 當視窗大小改變時，更新圖片寬度
    window.addEventListener("resize", function () {
        imageWidth = images[0].clientWidth;
        updateCarousel();
    });

    updateCarousel();
});

// 顯示彈跳視窗
function showModal() {
    document.getElementById("successModal").style.display = "flex";
}

// 隱藏彈跳視窗
function closeModal() {
    document.getElementById("successModal").style.display = "none";
}

// 在註冊成功後顯示彈跳視窗

