document.addEventListener("DOMContentLoaded", () => {
  const loader = document.getElementById("appLoader");
  if (loader) {
    setTimeout(() => loader.classList.add("hide"), 350);
  }

  if (window.AOS) {
    window.AOS.init({
      duration: 650,
      once: true,
      easing: "ease-out-cubic",
    });
  }

  const sidebar = document.getElementById("appSidebar");
  const toggle = document.getElementById("sidebarToggle");
  if (sidebar && toggle) {
    toggle.addEventListener("click", () => sidebar.classList.toggle("open"));
  }
});
