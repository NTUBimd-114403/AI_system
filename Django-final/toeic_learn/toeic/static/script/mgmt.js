const menuToggle = document.getElementById("hamburgerbutton");
const sidebar = document.getElementById("sidebar");

menuToggle.addEventListener("click", () => {
  sidebar.classList.toggle("active");
});

document.querySelectorAll('.sidebar-toggle').forEach(toggle => {
    toggle.addEventListener('click', function() {
        const parent = this.parentElement;
        parent.classList.toggle('active');
    });
});