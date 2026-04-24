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

function setupMobileZoomFix() {
  if (!window.visualViewport) return;

  const vv = window.visualViewport;
  const header = document.querySelector(".mobile-header");
  const nav = document.querySelector(".bottom-nav");
  if (!header && !nav) return;

  function resetEl(el) {
    el.style.width = "";
    el.style.top = "";
    el.style.left = "";
    el.style.bottom = "";
    el.style.transform = "";
    el.style.transformOrigin = "";
  }

  function sync() {
    const scale = vv.scale;

    if (scale <= 1.01) {
      if (header) resetEl(header);
      if (nav) resetEl(nav);
      return;
    }

    const inv = 1 / scale;
    const w = Math.round(vv.width * scale) + "px";
    const left = vv.offsetLeft + "px";

    if (header) {
      header.style.width = w;
      header.style.left = left;
      header.style.top = vv.offsetTop + "px";
      header.style.transformOrigin = "0 0";
      header.style.transform = `scale(${inv})`;
    }

    if (nav) {
      nav.style.width = w;
      nav.style.left = left;
      nav.style.bottom = Math.round(window.innerHeight - vv.offsetTop - vv.height) + "px";
      nav.style.transformOrigin = "0 100%";
      nav.style.transform = `scale(${inv})`;
    }
  }

  vv.addEventListener("resize", sync);
  vv.addEventListener("scroll", sync);
}

document.addEventListener("DOMContentLoaded", () => {
  if (localStorage.getItem("fullscreen") === "1") {
    document.body.classList.add("fullscreen-mode");
  }
  setupMobileZoomFix();
});
