"use strict";

// Filtering changes only the visible cards; it makes no network requests.
const filters = document.querySelector(".filters");
const buttons = document.querySelectorAll("[data-filter]");
const cards = document.querySelectorAll("[data-category]");
const count = document.querySelector("#menu-count");

buttons.forEach((button) => {
  button.addEventListener("click", () => {
    const category = button.dataset.filter;
    let visibleCount = 0;
    cards.forEach((card) => {
      card.hidden = category !== "All" && card.dataset.category !== category;
      if (!card.hidden) visibleCount += 1;
    });
    buttons.forEach((otherButton) => {
      const selected = otherButton === button;
      otherButton.classList.toggle("active", selected);
      otherButton.setAttribute("aria-pressed", String(selected));
    });
    count.textContent = `${visibleCount} items · All prices in USD`;
  });
});

// With JavaScript disabled the complete menu still works.
filters.hidden = false;
