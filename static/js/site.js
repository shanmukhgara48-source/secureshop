/* Shared, progressively enhanced controls; all core forms work without JS. */
(function () {
  "use strict";

  var menuButton = document.getElementById("menu-toggle");
  var navigation = document.getElementById("primary-nav");

  function closeMenu(returnFocus) {
    if (!menuButton || !navigation) return;
    navigation.classList.remove("is-open");
    menuButton.setAttribute("aria-expanded", "false");
    if (returnFocus) menuButton.focus();
  }

  if (menuButton && navigation) {
    menuButton.addEventListener("click", function () {
      var expanded = menuButton.getAttribute("aria-expanded") !== "true";
      menuButton.setAttribute("aria-expanded", String(expanded));
      navigation.classList.toggle("is-open", expanded);
    });
    document.addEventListener("keydown", function (event) {
      if (event.key === "Escape" && menuButton.getAttribute("aria-expanded") === "true") {
        closeMenu(true);
      }
    });
    document.addEventListener("click", function (event) {
      if (!navigation.contains(event.target) && !menuButton.contains(event.target)) {
        closeMenu(false);
      }
    });
    window.matchMedia("(min-width: 861px)").addEventListener("change", function () {
      closeMenu(false);
    });
  }

  document.querySelectorAll("[data-password-target]").forEach(function (button) {
    var input = document.getElementById(button.getAttribute("data-password-target"));
    if (!input) return;
    button.setAttribute("aria-controls", input.id);
    button.setAttribute("aria-pressed", "false");
    button.addEventListener("click", function () {
      var reveal = input.type === "password";
      input.type = reveal ? "text" : "password";
      button.setAttribute("aria-pressed", String(reveal));
      button.setAttribute("aria-label", reveal ? "Hide password" : "Show password");
    });
  });

  document.querySelectorAll("form[data-confirm]").forEach(function (form) {
    form.addEventListener("submit", function (event) {
      if (!window.confirm(form.getAttribute("data-confirm"))) event.preventDefault();
    });
  });
})();
