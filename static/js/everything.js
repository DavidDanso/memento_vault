// Toast notifications
document.addEventListener("DOMContentLoaded", function () {
  const toasts = document.querySelectorAll(".alert");
  toasts.forEach((toast, index) => {
    setTimeout(() => {
      toast.classList.add("show");
      setTimeout(() => {
        hideToast(toast.id);
      }, 6000);
    }, index * 200);
  });
});

function hideToast(toastId) {
  const toast = document.getElementById(toastId);
  if (toast) {
    toast.classList.add("hide");
    toast.classList.remove("show");
    setTimeout(() => {
      const container = toast.closest(".alert-container");
      if (container) {
        container.remove();
      }
    }, 300);
  }
}

// Search functionality
$(document).ready(function () {
  $(".live-search-box").on("keyup", function () {
    var searchTerm = $(this).val().toLowerCase();

    $(".masonry-item").each(function () {
      var searchStr = $(this).data("search-term");
      if (searchStr && searchStr.indexOf(searchTerm) !== -1) {
        $(this).show();
      } else {
        $(this).hide();
      }
    });
  });
});
