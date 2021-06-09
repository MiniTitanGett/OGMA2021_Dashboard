
function resizeContentWrapper() {
  try {
    heightTabs = document.getElementById("tab-menu-header").offsetHeight;
    heightMenu = document.getElementById("button-save-dashboard-wrapper").offsetHeight;
    heightTotal = document.getElementById("page-content").offsetHeight;
    document.getElementById("tab-content-wrapper").style.maxHeight = String(heightTotal - heightMenu - heightTabs) + 'px';
  }
  catch {
    
  }
}

window.onresize = resizeContentWrapper;

// Handles Resizing of ContentWrapper, uses x as a throw away output, takes x,y,z and throw away inputs to trigger when tabs are modified
window.dash_clientside = Object.assign({}, window.dash_clientside, {
    clientside: {
        resizeContentWrapper: function(x,y,z) {
            resizeContentWrapper();
            return x
        },
        datasetLoadScreen: function(n_click_load, n_click_reset) {
            if (n_click_load != ',,,,' || n_click_reset != ',,,,'){
                var newDiv = document.createElement('div');
                newDiv.className = '_data-loading';
                newDiv.id = 'loading';
                document.body.appendChild(newDiv, document.getElementById('content'));
            }
            return 0;
        },
        datasetRemoveLoadScreen: function(data) {
            document.getElementById('loading').remove();
            return 0;
        },
        graphLoadScreen: function(n_click_view, view_content_className) {
            if (view_content_className != 'tile-nav tile-nav--view tile-nav--selected'){
                var newDiv = document.createElement('div');
                newDiv.className = '_data-loading';
                newDiv.id = 'graph-loading';
                document.getElementById('{"index":0,"type":"tile-view-content"}').appendChild(newDiv));
            }
            return 0;
        },
        graphRemoveLoadScreen: function(data) {
            document.getElementById('graph-loading').remove();
            return 0;
        }
    }
});


