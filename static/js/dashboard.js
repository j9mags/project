(function () {
  var VISIBLE_CLASS = 'is-showing-options',
      fab_btn = document.getElementById('fab_btn'),
      fab_ctn = document.getElementById('fab_ctn'),
      is_drawer_enabled = document.getElementById('is_drawer_enabled').value == "True",
      showOpts = function(e) {
        var processClick = function (evt) {
          if (e !== evt) {
            fab_ctn.classList.remove(VISIBLE_CLASS);
            fab_ctn.IS_SHOWING = false;
            document.removeEventListener('click', processClick);
          }
        };
        if (!fab_ctn.IS_SHOWING) {
          fab_ctn.IS_SHOWING = true;
          fab_ctn.classList.add(VISIBLE_CLASS);
          document.addEventListener('click', processClick);
        }
      };
  if(is_drawer_enabled){
      fab_btn.addEventListener('click', showOpts);
  }
}.call(this));