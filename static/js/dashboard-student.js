(function () {
    var hash = window.location.hash || '#account';
    $(hash+'-tab').addClass('is-active');
    $(hash+'-panel').addClass('is-active');

    var VISIBLE_CLASS = 'is-showing-dialog',
        DIALOG_ID = 'dlg-revoke-mandate',
        dlg = document.getElementById(DIALOG_ID),
        btn = document.getElementById('btn-revoke-mandate'),
        showDlg = function(e) {
          e.preventDefault();
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
    $('a.filter').click(function(ev){
        ev.preventDefault();
        var filter = $(this).data('filter');
        var value =  $(this).data('filter-value');
        var hash =  $(this).attr('href');
        if (filter !== undefined)
            addOrUpdateUrlParam(filter, value, hash);
    });
    function addOrUpdateUrlParam(name, value, hash) {
        var href = window.location.href;
        var regex = new RegExp("[&\\?]" + name + "=");
        if(regex.test(href)) {
            regex = new RegExp("([&\\?])" + name + "=\\S+");
            window.location.href = href.replace(regex, "$1" + name + "=" + value + hash);
        } else {
            if(href.indexOf("?") > -1)
                window.location.href = href + "&" + name + "=" + value  + hash;
            else
                window.location.href = href + "?" + name + "=" + value + hash;
        }
    }
}.call(this));