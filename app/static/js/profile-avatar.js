(function () {
  "use strict";

  let cropper = null;

  const fileInput = document.getElementById("avatar-file-input");
  const editBtn = document.getElementById("avatar-edit-btn");
  const avatarImg = document.getElementById("profile-avatar-img");
  const cropImage = document.getElementById("crop-image");
  const confirmBtn = document.getElementById("crop-confirm-btn");
  const confirmLabel = document.getElementById("crop-confirm-label");
  const confirmSpinner = document.getElementById("crop-confirm-spinner");
  const feedback = document.getElementById("avatar-feedback");
  const cropModalEl = document.getElementById("cropModal");

  if (!cropModalEl) return;

  const cropModal = new bootstrap.Modal(cropModalEl);

  editBtn.addEventListener("click", () => fileInput.click());

  fileInput.addEventListener("change", () => {
    const file = fileInput.files[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = (e) => {
      cropImage.src = e.target.result;
      cropModal.show();
    };
    reader.readAsDataURL(file);
    fileInput.value = "";
  });

  cropModalEl.addEventListener("shown.bs.modal", () => {
    if (cropper) {
      cropper.destroy();
      cropper = null;
    }
    cropper = new Cropper(cropImage, {
      aspectRatio: 1,
      viewMode: 1,
      dragMode: "move",
      autoCropArea: 0.85,
      restore: false,
      guides: true,
      center: true,
      highlight: false,
      cropBoxMovable: false,
      cropBoxResizable: false,
      toggleDragModeOnDblclick: false,
    });
  });

  cropModalEl.addEventListener("hidden.bs.modal", () => {
    if (cropper) {
      cropper.destroy();
      cropper = null;
    }
  });

  confirmBtn.addEventListener("click", () => {
    if (!cropper) return;

    const canvas = cropper.getCroppedCanvas({ width: 400, height: 400 });
    if (!canvas) return;

    setLoading(true);

    canvas.toBlob(async (blob) => {
      const formData = new FormData();
      formData.append("avatar", blob, "avatar.jpg");

      try {
        const resp = await fetch("/api/profile/avatar", {
          method: "POST",
          headers: { "X-Requested-With": "XMLHttpRequest" },
          body: formData,
        });
        const data = await resp.json();

        if (data.sucesso) {
          avatarImg.src = data.url + "?t=" + Date.now();
          cropModal.hide();
          showFeedback("Foto atualizada com sucesso!", "success");
        } else {
          showFeedback(data.erro || "Erro ao salvar foto.", "danger");
        }
      } catch {
        showFeedback("Erro de conexão. Tente novamente.", "danger");
      } finally {
        setLoading(false);
      }
    }, "image/jpeg", 0.92);
  });

  function setLoading(loading) {
    confirmBtn.disabled = loading;
    confirmLabel.textContent = loading ? "Salvando..." : "Confirmar";
    confirmSpinner.classList.toggle("d-none", !loading);
  }

  function showFeedback(msg, type) {
    feedback.textContent = msg;
    feedback.className = "avatar-feedback alert alert-" + type + " mt-2 py-2 px-3";
    setTimeout(() => {
      feedback.textContent = "";
      feedback.className = "avatar-feedback";
    }, 4000);
  }
})();
