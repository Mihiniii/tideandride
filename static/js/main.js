(function () {
  "use strict";

  // Mobile menu
  var toggle = document.querySelector(".nav-toggle");
  var menu = document.getElementById("nav-menu");
  if (toggle && menu) {
    toggle.addEventListener("click", function () {
      var open = menu.classList.toggle("is-open");
      toggle.setAttribute("aria-expanded", open ? "true" : "false");
    });
  }

  // Keep "return" date on or after "pickup" wherever the pair appears
  function pairDates(startSel, endSel) {
    var start = document.querySelector(startSel);
    var end = document.querySelector(endSel);
    if (!start || !end) return;
    function sync() {
      if (!start.value) return;
      end.min = start.value;
      if (end.value && end.value < start.value) end.value = start.value;
    }
    start.addEventListener("change", sync);
    sync();
  }
  pairDates("#id_pickup", "#id_dropoff");
  pairDates("#id_pickup_date", "#id_return_date");

  // Booking form: hotel field + live price
  var form = document.querySelector(".bookform");
  if (form) {
    var price = parseFloat(form.dataset.price || "0");
    var currency = form.dataset.currency || "";
    var pickup = form.querySelector("#id_pickup_date");
    var ret = form.querySelector("#id_return_date");
    var daysEl = form.querySelector("[data-sum-days]");
    var totalEl = form.querySelector("[data-sum-total]");
    var hotel = form.querySelector(".hotel-field");
    var radios = form.querySelectorAll('input[name="handover"]');

    var fmt = function (n) {
      return currency + " " + Math.round(n).toLocaleString("en-US");
    };

    function updateTotal() {
      if (!pickup.value || !ret.value) {
        daysEl.textContent = "Choose dates";
        totalEl.textContent = "";
        return;
      }
      var a = new Date(pickup.value + "T00:00:00");
      var b = new Date(ret.value + "T00:00:00");
      var days = Math.round((b - a) / 86400000);
      if (days < 0) {
        daysEl.textContent = "Return is before pickup";
        totalEl.textContent = "";
        return;
      }
      days = Math.max(days, 1);
      daysEl.textContent = days + (days === 1 ? " day" : " days");
      totalEl.textContent = fmt(days * price);
    }

    function updateHotel() {
      if (!hotel) return;
      var checked = form.querySelector('input[name="handover"]:checked');
      var show = checked && checked.value === "hotel";
      hotel.hidden = !show;
    }

    [pickup, ret].forEach(function (el) {
      el.addEventListener("change", updateTotal);
      el.addEventListener("input", updateTotal);
    });
    radios.forEach(function (r) { r.addEventListener("change", updateHotel); });
    updateTotal();
    updateHotel();
  }

  // Confirm destructive forms (cancel booking)
  document.querySelectorAll("form[data-confirm]").forEach(function (f) {
    f.addEventListener("submit", function (e) {
      if (!window.confirm(f.dataset.confirm)) e.preventDefault();
    });
  });
})();
