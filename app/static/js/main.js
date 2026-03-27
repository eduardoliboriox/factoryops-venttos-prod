function enterFullscreen() {
  document.body.classList.add("fullscreen-mode");
  localStorage.setItem("fullscreen", "1");
}

function exitFullscreen() {
  document.body.classList.remove("fullscreen-mode");
  localStorage.removeItem("fullscreen");
}

function toggleFullscreen() {
  if (document.body.classList.contains("fullscreen-mode")) {
    exitFullscreen();
  } else {
    enterFullscreen();
  }
}

document.addEventListener("DOMContentLoaded", () => {
  if (localStorage.getItem("fullscreen") === "1") {
    document.body.classList.add("fullscreen-mode");
  }
});
