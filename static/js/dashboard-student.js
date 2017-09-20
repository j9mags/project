(function () {
    var hash = window.location.hash || '#account';
    $(hash+'-tab').addClass('is-active');
    $(hash+'-panel').addClass('is-active');

    var VISIBLE_CLASS = 'is-showing-dialog',
        DIALOG_ID = 'dlg-revoke-mandate',
        dlg = document.getElementById(DIALOG_ID),
        btn = document.getElementById('btn-revoke-mandate'),
        showDlg = function(e) {
          var processClick = function (evt) {
            var target = evt.target.closest('#' + DIALOG_ID);
            
            if ((e !== evt) && (target === null)) {
              dlg.classList.remove(VISIBLE_CLASS);
              dlg.IS_SHOWING = false;
              document.removeEventListener('click', processClick);
            }
          };
          if (!dlg.IS_SHOWING) {
            dlg.IS_SHOWING = true;
            dlg.classList.add(VISIBLE_CLASS);
            document.addEventListener('click', processClick);
          }
        };
    window.showDlg = showDlg;
    if (btn !== null)
        btn.addEventListener('click', showDlg);
}.call(this));