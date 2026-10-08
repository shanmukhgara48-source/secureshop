/* Catalogue interactions intentionally use the local jQuery baseline. */
$(function () {
  "use strict";

  var status = $("#catalogue-status");
  var filter = $("#category-filter");
  var cards = $(".product-card");
  var countLabel = $("#search-result-count");
  var initialCountLabel = countLabel.text();
  var emptyState = document.getElementById("filter-empty-state");
  var parameters = new URLSearchParams(window.location.search);
  var requestedCategory = parameters.get("category") || "";
  var categories = filter.find("option").map(function () { return this.value; }).get();

  function applyFilter(updateAddress) {
    var category = filter.val() || "";
    var count = 0;
    cards.each(function () {
      var visible = !category || $(this).attr("data-category") === category;
      $(this).toggle(visible);
      if (visible) count += 1;
    });
    countLabel.attr("data-result-count", count).text(category
      ? count + (count === 1 ? " essential" : " essentials") + " in " + category
      : initialCountLabel);
    if (emptyState) emptyState.hidden = count !== 0;
    if (updateAddress) {
      var address = new URL(window.location.href);
      if (category) address.searchParams.set("category", category);
      else address.searchParams.delete("category");
      window.history.replaceState(null, "", address.pathname + address.search + address.hash);
    }
  }

  if (categories.indexOf(requestedCategory) !== -1) filter.val(requestedCategory);
  applyFilter(false);
  filter.on("change", function () { applyFilter(true); });

  function showFeedback(html, fallback, failed) {
    // Parse escaped server markup in an inert document; only text enters the page.
    var fragment = new DOMParser().parseFromString(html, "text/html");
    var feedback = fragment.querySelector("#cart-feedback");
    var message = feedback ? feedback.textContent : fallback;
    status.toggleClass("is-error", Boolean(failed)).text(message);
    if (feedback) {
      var count = feedback.getAttribute("data-cart-count");
      $("[data-cart-count]").attr("data-cart-count", count).text(count);
    }
  }

  $(".add-to-cart-form").on("submit", function (event) {
    event.preventDefault();
    var form = $(this);
    var action = new URL(form.attr("action"), window.location.href);
    if (action.origin !== "http://127.0.0.1:8080") {
      status.addClass("is-error").text("This action is available on the local lab server only.");
      return;
    }
    var button = form.find("button[type=submit]");
    button.prop("disabled", true).attr("aria-busy", "true");
    status.removeClass("is-error").text("Adding this essential to your cart…");
    $.ajax({
      url: action.pathname,
      method: "POST",
      data: form.serialize(),
      dataType: "html",
      headers: {"X-CSRFToken": $("meta[name=csrf-token]").attr("content")}
    }).done(function (html) {
      showFeedback(html, "Added to your cart.", false);
    }).fail(function (response) {
      if (response.status === 401) {
        status.addClass("is-error").text("Your session ended. Sign in again to add products.");
      } else {
        showFeedback(response.responseText || "", "Could not add this item. Reload the page and try again.", true);
      }
    }).always(function () {
      button.prop("disabled", false).removeAttr("aria-busy");
    });
  });
});
