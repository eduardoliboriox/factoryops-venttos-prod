function onlyDigits(value) {
  return value.replace(/\D/g, "");
}

function maskPhone(input) {
  input.addEventListener("input", () => {
    let v = onlyDigits(input.value).slice(0, 11);

    if (v.length > 6) {
      input.value = `(${v.slice(0, 2)}) ${v.slice(2, 7)}-${v.slice(7)}`;
    } else if (v.length > 2) {
      input.value = `(${v.slice(0, 2)}) ${v.slice(2)}`;
    } else if (v.length > 0) {
      input.value = `(${v}`;
    }
  });
}

function maskZip(input) {
  input.addEventListener("input", () => {
    let v = onlyDigits(input.value).slice(0, 8);

    if (v.length > 5) {
      input.value = `${v.slice(0, 5)}-${v.slice(5)}`;
    } else {
      input.value = v;
    }
  });
}

document.addEventListener("DOMContentLoaded", () => {
  document
    .querySelectorAll("[data-mask='phone']")
    .forEach(maskPhone);

  document
    .querySelectorAll("[data-mask='zip']")
    .forEach(maskZip);
});
