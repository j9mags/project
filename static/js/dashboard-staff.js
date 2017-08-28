(function () {
    var VISIBLE_CLASS = 'is-showing-dialog',
        DIALOG_ID_ST = 'dlg-add-students',
        addStudents_dlg = document.getElementById(DIALOG_ID_ST),
        addStudents_btn = document.getElementById('fab-add-students'),
        DIALOG_ID_CS = 'dlg-add-courses',
        addCourses_dlg = document.getElementById(DIALOG_ID_CS),
        addCourses_btn = document.getElementById('fab-add-courses'),
        DIALOG_ID_BLK = 'dlg-bulk-actions',
        blkActions_dlg = document.getElementById(DIALOG_ID_BLK),
        blkActions_btn = document.getElementById('bulk-form--btn'),
        showDlgSt = function(e) {
          var processClick = function (evt) {
            var target = evt.target.closest('#' + DIALOG_ID_ST);
            
            if ((e !== evt) && (target === null)) {
              addStudents_dlg.classList.remove(VISIBLE_CLASS);
              addStudents_dlg.IS_SHOWING = false;
              document.removeEventListener('click', processClick);
            }
          };
          if (!addStudents_dlg.IS_SHOWING) {
            addStudents_dlg.IS_SHOWING = true;
            addStudents_dlg.classList.add(VISIBLE_CLASS);
            document.addEventListener('click', processClick);
          }
        },
        showDlgCs = function(e) {
            var processClick = function (evt) {
              var target = evt.target.closest('#' + DIALOG_ID_CS);
              
              if ((e !== evt) && (target === null)) {
                addCourses_dlg.classList.remove(VISIBLE_CLASS);
                addCourses_dlg.IS_SHOWING = false;
                document.removeEventListener('click', processClick);
              }
            };
            if (!addCourses_dlg.IS_SHOWING) {
              addCourses_dlg.IS_SHOWING = true;
              addCourses_dlg.classList.add(VISIBLE_CLASS);
              document.addEventListener('click', processClick);
            }
        },
        showDlgBlk = function(e) {
            var processClick = function (evt) {
              var target = evt.target.closest('#' + DIALOG_ID_BLK);
              
              if ((e !== evt) && (target === null)) {
                blkActions_dlg.classList.remove(VISIBLE_CLASS);
                blkActions_dlg.IS_SHOWING = false;
                document.removeEventListener('click', processClick);
              }
            };
            if (!blkActions_dlg.IS_SHOWING) {
              blkActions_dlg.IS_SHOWING = true;
              blkActions_dlg.classList.add(VISIBLE_CLASS);
              document.addEventListener('click', processClick);
            }
        };
    addStudents_btn.addEventListener('click', showDlgSt);
    addCourses_btn.addEventListener('click', showDlgCs);
    blkActions_btn.addEventListener('click', showDlgBlk);

     function addOrUpdateUrlParam(name, value) {
      var href = window.location.href;
      var regex = new RegExp("[&\\?]" + name + "=");
      if(regex.test(href)) {
        regex = new RegExp("([&\\?])" + name + "=\\d+");
        window.location.href = href.replace(regex, "$1" + name + "=" + value);
      } else {
        if(href.indexOf("?") > -1)
          window.location.href = href + "&" + name + "=" + value;
        else
          window.location.href = href + "?" + name + "=" + value;
      }
    }

     function removeUrlParam(name) {
      var url = window.location.href;
      var urlparts= url.split('?');   
      if (urlparts.length>=2) {
          var prefix= encodeURIComponent(name)+'=';
          var pars= urlparts[1].split(/[&;]/g);

          for (var i= pars.length; i-- > 0;) {    
              if (pars[i].lastIndexOf(prefix, 0) !== -1) {  
                  pars.splice(i, 1);
              }
          }

          url = urlparts[0] + (pars.length > 0 ? '?' + pars.join('&') : "");
          window.location.href = url;
      } else {
          window.location.href = url;
      }
    }

    $('a.filter').click(function(ev){
      ev.preventDefault();
      var filter = $(this).data('filter');
      var value =  $(this).data('filter-value');
      addOrUpdateUrlParam(filter, value);
    });
    $('.chancen-filter a').click(function(ev){
      ev.preventDefault();
      var filter = $(this).data('filter');
      removeUrlParam(filter);
    });

    function init_bulk() {
      var boxes = $('tbody .mdl-data-table__select');

      $('table .mdl-data-table__select input').change(function(ev) {
        var selected = '';

        for (var i = 0, length = boxes.length; i < length; i++) {
          if (boxes[i].MaterialCheckbox.inputElement_.checked) {
            selected += $(boxes[i]).parents('tr').data('student') + ';';
          }
        }
        $('#selected_students').val(selected);
        if (selected.length > 0) 
          blkActions_btn.removeAttribute('disabled');
        else
          blkActions_btn.setAttribute('disabled', 'disabled');
      });
    }
    setTimeout(init_bulk, 500);
}.call(this));