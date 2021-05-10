
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
        }
    }
});


