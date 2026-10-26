"use strict";
const button = document.createElement("button");
button.type = "button";
button.className = "btn back-to-top";
button.textContent = "↑ Наверх";
button.hidden = true;
button.addEventListener("click", () => window.scrollTo({ top: 0 }));
document.body.append(button);
window.addEventListener("scroll", () => {
  button.hidden = window.scrollY < 500;
}, { passive: true });
