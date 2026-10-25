document.addEventListener("DOMContentLoaded", () => {
  const toggle = document.getElementById("menuToggle");
  const nav = document.getElementById("navLinks");
  if (toggle && nav) {
    toggle.addEventListener("click", () => nav.classList.toggle("nav-open"));
  }
  document.querySelectorAll(".flash").forEach((item) => {
    window.setTimeout(() => {
      item.style.opacity = "0";
      item.style.transform = "translateY(-5px)";
      window.setTimeout(() => item.remove(), 300);
    }, 5000);
  });
});
