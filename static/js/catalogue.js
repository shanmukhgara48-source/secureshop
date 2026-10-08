/* Local catalogue interactions. Never insert untrusted strings as HTML. */
$(function () {
  var status = $("#catalogue-status");
  $("#category-filter").on("change", function () {
    var category = $(this).val();
    var count = 0;
    $(".product-card").each(function () {
      var visible = !category || $(this).attr("data-category") === category;
      $(this).toggle(visible);
      if (visible) count += 1;
    });
    $("#search-result-count").attr("data-result-count", count)
      .text(count + (count === 1 ? " essential" : " essentials") + (category ? " in " + category : ""));
  });

  function showFeedback(html, fallback) {
    // Parse server-escaped markup in an inert document; only text enters the live page.
    var documentFragment = new DOMParser().parseFromString(html, "text/html");
    var feedback = documentFragment.querySelector("#cart-feedback");
    status.text(feedback ? feedback.textContent : fallback);
    if (feedback) {
      $("[data-cart-count]").text(feedback.getAttribute("data-cart-count"));
    }
  }

  $(".add-to-cart-form").on("submit", function (event) {
    event.preventDefault();
    var form = $(this);
    var action = new URL(form.attr("action"), window.location.href);
    if (action.origin !== "http://127.0.0.1:8080") {
      status.text("This action is available on the local lab server only.");
      return;
    }
    var button = form.find("button[type=submit]");
    button.prop("disabled", true);
    $.ajax({
      url: action.pathname,
      method: "POST",
      data: form.serialize(),
      dataType: "html",
      headers: {"X-CSRFToken": $("meta[name=csrf-token]").attr("content")}
    }).done(function (html) {
      showFeedback(html, "Added to your cart.");
    }).fail(function (response) {
      if (response.status === 401) {
        status.text("Your session ended. Sign in again to add products.");
      } else {
        showFeedback(response.responseText || "", "Could not add this item. Reload the page and try again.");
      }
    }).always(function () {
      button.prop("disabled", false);
    });
  });
});
