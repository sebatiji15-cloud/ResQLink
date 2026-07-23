/* ResQLink – main.js */
document.addEventListener('DOMContentLoaded', function () {

  /* ── 1. GPS Detection ─────────────────────────────────── */
  var gpsBtn    = document.getElementById('gpsBtn');
  var latInput  = document.getElementById('lat');
  var lngInput  = document.getElementById('lng');
  var gpsStatus = document.getElementById('gpsStatus');

  if (gpsBtn) {
    gpsBtn.addEventListener('click', function () {
      if (!navigator.geolocation) {
        gpsStatus.style.color = '#e63946';
        gpsStatus.textContent = '❌ Geolocation not supported by your browser.';
        return;
      }
      gpsStatus.style.color = '#f4a261';
      gpsStatus.textContent = '📡 Detecting your location…';
      gpsBtn.disabled = true;

      navigator.geolocation.getCurrentPosition(
        function (pos) {
          latInput.value = pos.coords.latitude.toFixed(6);
          lngInput.value = pos.coords.longitude.toFixed(6);
          gpsStatus.style.color = '#2dc653';
          gpsStatus.textContent = '✅ Location detected: ' + latInput.value + ', ' + lngInput.value;
          gpsBtn.disabled = false;
        },
        function (err) {
          gpsStatus.style.color = '#e63946';
          gpsStatus.textContent = '❌ Could not detect: ' + err.message;
          gpsBtn.disabled = false;
        },
        { timeout: 10000, maximumAge: 60000 }
      );
    });
  }

  /* ── 2. Live Status Polling ───────────────────────────── */
  var trackers = document.querySelectorAll('.live-track');
  if (trackers.length > 0) {
    function pollStatus(el) {
      var rid = el.getAttribute('data-rid');
      fetch('/api/status/' + rid)
        .then(function (r) { return r.json(); })
        .then(function (data) {
          if (!data || data.error) return;
          var card  = el.closest('.req-card');
          var badge = card ? card.querySelector('.status-badge') : null;

          if (badge) {
            badge.className = 'status-badge badge-' + data.status;
            badge.textContent = data.status.toUpperCase();
          }
          if (card) {
            card.classList.remove('card-pending', 'card-active', 'card-resolved');
            card.classList.add('card-' + data.status);
          }
          if (data.status === 'active' && data.vol_name) {
            var existing = card ? card.querySelector('.vol-assigned') : null;
            if (!existing && card) {
              var vDiv = document.createElement('div');
              vDiv.className = 'vol-assigned';
              vDiv.innerHTML = '🤝 <strong>' + data.vol_name + '</strong>'
                + (data.vol_phone ? ' &nbsp;|&nbsp; 📞 ' + data.vol_phone : '');
              el.parentNode.insertBefore(vDiv, el);
            }
          }
          if (data.status === 'resolved') el.style.display = 'none';
        })
        .catch(function () {});
    }

    trackers.forEach(function (el) {
      pollStatus(el);
      setInterval(function () { pollStatus(el); }, 10000);
    });
  }

  /* ── 3. Auto-dismiss flash messages after 5s ──────────── */
  document.querySelectorAll('.flash').forEach(function (f) {
    setTimeout(function () {
      f.style.transition = 'opacity .5s';
      f.style.opacity = '0';
      setTimeout(function () { f.remove(); }, 500);
    }, 5000);
  });

  /* ── 4. Auto-refresh volunteer dashboard every 30s ─────── */
  if (document.querySelector('.vol-active-badge')) {
    setTimeout(function () { location.reload(); }, 30000);
  }

});
