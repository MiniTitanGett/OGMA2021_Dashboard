
function resizeContentWrapper() {
  try {
    heightTabs = document.getElementById("tab-menu-header").offsetHeight;
    heightMenu = document.getElementById("button-save-dashboard-wrapper").offsetHeight;
    heightTotal = document.getElementById("page-content").offsetHeight;
    document.getElementById("tab-content-wrapper").style.maxHeight = String(heightTotal - heightMenu - heightTabs) + 'px';
  }
  catch { /* Do Nothing */ }
}

window.onresize = resizeContentWrapper;

// Handles Resizing of ContentWrapper, uses x as a throw away output, takes x,y,z and throw away inputs to trigger when tabs are modified
window.dash_clientside = Object.assign({}, window.dash_clientside, {
    clientside: {
        resizeContentWrapper: function(x,y,z) {
            resizeContentWrapper();
            return x
        },
        graphLoadScreen0: function(trigger) {
            if (trigger == 'confirm-load'){
                var newDiv = document.createElement('div');
                newDiv.className = '_graph-data-loading';
                newDiv.id = 'graph-loading0';
                document.getElementById('{"index":0,"type":"tile-view-content"}').appendChild(newDiv);
            }
            return 0;
        },
        graphRemoveLoadScreen0: function(data, num_tiles) {
            try{
                document.getElementById('graph-loading0').remove();
            }catch{ /* Do Nothing */ }
            return 0;
        },
        graphLoadScreen1: function(n_click_view, view_content_className) {
            if (view_content_className != 'tile-nav tile-nav--view tile-nav--selected'){
                var newDiv = document.createElement('div');
                newDiv.className = '_graph-data-loading';
                newDiv.id = 'graph-loading1';
                document.getElementById('{"index":1,"type":"tile-view-content"}').appendChild(newDiv);
            }
            return 0;
        },
        graphRemoveLoadScreen1: function(data, num_tiles) {
            try{
                document.getElementById('graph-loading1').remove();
            }catch{ /* Do Nothing */ }
            return 0;
        },
        graphLoadScreen2: function(n_click_view, view_content_className) {
            if (view_content_className != 'tile-nav tile-nav--view tile-nav--selected'){
                var newDiv = document.createElement('div');
                newDiv.className = '_graph-data-loading';
                newDiv.id = 'graph-loading2';
                document.getElementById('{"index":2,"type":"tile-view-content"}').appendChild(newDiv);
            }
            return 0;
        },
        graphRemoveLoadScreen2: function(data, num_tiles) {
            try{
                document.getElementById('graph-loading2').remove();
            }catch{ /* Do Nothing */ }
            return 0;
        },
        graphLoadScreen3: function(n_click_view, view_content_className) {
            if (view_content_className != 'tile-nav tile-nav--view tile-nav--selected'){
                var newDiv = document.createElement('div');
                newDiv.className = '_graph-data-loading';
                newDiv.id = 'graph-loading3';
                document.getElementById('{"index":3,"type":"tile-view-content"}').appendChild(newDiv);
            }
            return 0;
        },
        graphRemoveLoadScreen3: function(data, num_tiles) {
            try{
                document.getElementById('graph-loading3').remove();
            }catch{ /* Do Nothing */ }
            return 0;
        }
    }
});


